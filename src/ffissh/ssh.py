import os
import socket

from ._libssh2 import lib, ffi
from . import exceptions, utils


def _read_output(chan):
    buf = ffi.new('char[1024]')
    while True:
        rc = lib.libssh2_channel_read(chan, buf, 1024)
        if rc > 0:
            out = ffi.buffer(buf, rc)
            yield str(out)
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
    def __init__(self, chan):
        self._chan = chan

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.close()

    def close(self):
        pass

    def execute(self, command):
        utils._run_until_done(lib.libssh2_channel_exec, self._chan, command)
        stdout = ''.join(_read_output(self._chan))
        return Result(0, stdout, '')


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

    def open_channel(self):
        chan = lib.libssh2_channel_open_session(self._session)
        if not chan:
            raise exceptions.SSHError('Could not open channel')
        return Channel(chan)
