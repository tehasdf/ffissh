import os
import socket
import select

from ._libssh2 import lib, ffi
from . import constants, exceptions, utils


def _read_output(
        chan, conn,
        blocking=True,
        read_func=lib.libssh2_channel_read):
    bufsize = 1024
    buf = ffi.new('char[{}]'.format(bufsize))
    while True:
        rc = read_func(chan, buf, bufsize)
        if rc > 0:
            out = ffi.buffer(buf, rc)
            yield str(out)
        elif rc == constants.LIBSSH2_ERROR_EAGAIN:
            if not blocking:
                break
            conn.waitsocket()
        elif rc == 0:
            break
        else:
            raise RuntimeError('Read error')


class Result(object):
    def __init__(self, rc, stdout, stderr):
        self.rc = rc
        self.stdout = stdout
        self.stderr = stderr


class Channel(object):
    def __init__(self, chan, connection):
        self._chan = chan
        self._conn = connection

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.close()

    def close(self):
        pass

    def execute(self, command):
        while True:
            rc = lib.libssh2_channel_exec(self._chan, command)
            if rc == constants.LIBSSH2_ERROR_EAGAIN:
                self._conn.waitsocket()
            else:
                break
        stdout = self.read()
        return Result(0, stdout, '')

    def read(self):
        return ''.join(_read_output(self._chan, self._conn))

    def read_nonblocking(self):
        return ''.join(_read_output(self._chan, self._conn, blocking=False))


class SftpFile(object):
    def __init__(self, sftp, path, mode='r'):
        self._sftp = sftp
        self._mode = mode
        flags = {
            'r': constants.LIBSSH2_FXF_READ,
            'w': constants.LIBSSH2_FXF_WRITE & constants.LIBSSH2_FXF_TRUNC,
            'a': constants.LIBSSH2_FXF_APPEND,
            'r+': (constants.LIBSSH2_FXF_READ
                   & constants.LIBSSH2_FXF_WRITE
                   & constants.LIBSSH2_FXF_TRUNC),
            }[mode]

        self._handle = lib.libssh2_sftp_open(
            sftp._session,
            path,
            flags,
            0,  # file permissions
            )

    def read(self):
        return ''.join(_read_output(
            self._handle,
            self._sftp.connection,
            read_func=lib.libssh2_sftp_read,
            blocking=False))

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        lib.libssh2_sftp_close_handle(self._handle)


class Sftp(object):
    def __init__(self, connection):
        self.connection = connection
        while True:
            self._session = lib.libssh2_sftp_init(connection._session)
            if not self._session:
                # TODO: make threadsafe
                errno = lib.libssh2_session_last_errno(
                        self.connection._session)
                if errno == constants.LIBSSH2_ERROR_EAGAIN:
                    self.connection.waitsocket()
                else:
                    raise RuntimeError('failed to initialize SFTP session')
            else:
                break

        ffi.gc(self._session, lib.libssh2_sftp_shutdown)

    def open(self, *args, **kwargs):
        return SftpFile(self, *args, **kwargs)


class Connection(object):
    def __init__(self, host=None, port=22, username=None):
        self.host = host
        self.port = port
        self.username = username
        self.privkey = os.path.expanduser('~/.ssh/id_rsa')
        self.pubkey = os.path.expanduser('~/.ssh/id_rsa.pub')
        self._session = None
        self._sock = None
        self.passphrase = ''

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *exc_info):
        if self._sock:
            self._sock.close()

    def connect(self, verify_fingerprint=False):
        self._session = lib.libssh2_session_init()
        self._sock = socket.create_connection((self.host, self.port))
        utils._run_until_done(lib.libssh2_session_handshake,
                              self._session, self._sock.fileno())
        if verify_fingerprint:
            raise NotImplementedError()
        utils._run_until_done(lib.libssh2_userauth_publickey_fromfile,
                              self._session, self.username, self.pubkey,
                              self.privkey, self.passphrase)
        lib.libssh2_session_set_blocking(self._session, False)

    def open_channel(self):
        while True:
            chan = lib.libssh2_channel_open_session(self._session)
            if not chan:
                # TODO: make threadsafe
                errno = lib.libssh2_session_last_error(self._session,
                                                       ffi.NULL, ffi.NULL, 0)
                if errno == constants.LIBSSH2_ERROR_EAGAIN:
                    self.waitsocket()
            else:
                break
        if not chan:
            raise exceptions.SSHError('Could not open channel')
        return Channel(chan, self)

    def request_portforward(self, port):
        boundport = ffi.new('int*')
        lib.libssh2_session_set_blocking(self._session, True)
        listener = lib.libssh2_channel_forward_listen_ex(
            self._session, self.host, port, boundport, 16)
        if not listener:
            raise exceptions.SSHError('Could not start listener')
        chan = lib.libssh2_channel_forward_accept(listener)
        if not chan:
            raise exceptions.SSHError('Could not accept forward')
        lib.libssh2_session_set_blocking(self._session, False)
        return Channel(chan, self)

    def waitsocket(self):
        dirs = lib.libssh2_session_block_directions(self._session)
        readfd, writefd = [], []
        if dirs & constants.LIBSSH2_SESSION_BLOCK_INBOUND:
            readfd.append(self._sock)
        if dirs & constants.LIBSSH2_SESSION_BLOCK_OUTBOUND:
            writefd.append(self._sock)
        return select.select(readfd, writefd, [], 10)
