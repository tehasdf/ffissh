import os
import socket
import select

from ._libssh2 import lib, ffi
from . import constants, exceptions, utils


def _read_output(chan, conn):
    buf = ffi.new('char[1024]')
    while True:
        rc = lib.libssh2_channel_read(chan, buf, 1024)
        if rc > 0:
            out = ffi.buffer(buf, rc)
            yield str(out)
        elif rc == constants.LIBSSH2_ERROR_EAGAIN:
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
        lib.libssh2_session_set_blocking(self._session, False)
        if verify_fingerprint:
            raise NotImplementedError()
        utils._run_until_done(lib.libssh2_userauth_publickey_fromfile,
                              self._session, self.username, self.pubkey,
                              self.privkey, self.passphrase)

    def open_channel(self):
        while True:
            chan = lib.libssh2_channel_open_session(self._session)
            if not chan:
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
        listener = lib.libssh2_channel_forward_listen(self._session, port)
        chan = lib.libssh2_channel_forward_accept(listener)
        if not chan:
            raise exceptions.SSHError('Could not accept forward')
        return Channel(chan, self)

    def waitsocket(self):
        dirs = lib.libssh2_session_block_directions(self._session)
        readfd, writefd = [], []
        if dirs & constants.LIBSSH2_SESSION_BLOCK_INBOUND:
            readfd.append(self._sock)
        if dirs & constants.LIBSSH2_SESSION_BLOCK_OUTBOUND:
            writefd.append(self._sock)
        return select.select(readfd, writefd, [], 10)
