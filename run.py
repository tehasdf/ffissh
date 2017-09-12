"""Example usage of the libssh2 python wrapper

This is based on libssh2's ssh2_exec.c example.
"""

import os
import socket
import argparse
from contextlib import closing

from _libssh2_py import lib, ffi


# constants copied from libssh2.h
LIBSSH2_ERROR_EAGAIN = -37
LIBSSH2_KNOWNHOST_TYPE_PLAIN = 1
LIBSSH2_KNOWNHOST_FILE_OPENSSH = 1
LIBSSH2_KNOWNHOST_KEYENC_RAW = 1 << 16


def _run_until_done(func, *args, **kwargs):
    """Keep retrying func(*args, **kwargs) if it returns EAGAIN.

    Raise a RuntimeError if it returns nonzero.
    This is a common idiom in the library. However, it is mostly useful with
    nonblocking sessions which we don't actually use here, so perhaps
    the EAGAIN checking isn't required after all.
    """
    while True:
        rc = func(*args, **kwargs)
        if rc != LIBSSH2_ERROR_EAGAIN:
            break
    if rc:
        raise RuntimeError('Error {0} calling {1}(*{2}, **{3})'
                           .format(rc, func, args, kwargs))


def _check_fingerprint(args, session):
    nh = lib.libssh2_knownhost_init(session)
    if not nh:
        raise RuntimeError('No known hosts')
    lib.libssh2_knownhost_readfile(
        nh, args.known_hosts,
        LIBSSH2_KNOWNHOST_FILE_OPENSSH)

    # just dumps the loaded known_hosts into "dumpfile"
    # lib.libssh2_knownhost_writefile(
    #   nh, "dumpfile", LIBSSH2_KNOWNHOST_FILE_OPENSSH)

    fp_len, fp_type = ffi.new('size_t*'), ffi.new('int*')
    fp_cdata = lib.libssh2_session_hostkey(session, fp_len, fp_type)
    if not fp_cdata:
        raise RuntimeError('No fingerprint')
    knownhost = ffi.new('struct libssh2_knownhost **')
    check = lib.libssh2_knownhost_checkp(  # NOQA  # unused 'check'
        nh, args.host, args.port, fp_cdata, fp_len[0],
        LIBSSH2_KNOWNHOST_TYPE_PLAIN | LIBSSH2_KNOWNHOST_KEYENC_RAW,
        knownhost)
    # i have been unable to get the check to work, it seems i don't read
    # the fingerprint correctly
    lib.libssh2_knownhost_free(nh)


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


def _ssh(args):
    """Run a command over ssh.

    1. Handshake
    2. Check fingerprint
    3. Auth via pubkey
    4. Open a SSH channel
    5. Exec a command
    6. Read the output
    7. TODO cleanup
    """
    command = ' '.join(args.command)
    session = lib.libssh2_session_init()
    with closing(socket.create_connection((args.host, args.port))) as sock:
        _run_until_done(lib.libssh2_session_handshake, session, sock.fileno())

        _check_fingerprint(args, session)
        _run_until_done(lib.libssh2_userauth_publickey_fromfile,
                        session, args.username,
                        args.pubkey,
                        args.privkey,
                        args.passphrase)

        chan = lib.libssh2_channel_open_session(session)
        if not chan:
            raise RuntimeError('Could not open channel')

        _run_until_done(lib.libssh2_channel_exec, chan, command)
        for part in _read_output(chan):
            lines = part.split('\n')
            for line in lines:
                print '[{0}] {1}'.format(args.host, line)


parser = argparse.ArgumentParser()
parser.add_argument('command', nargs=argparse.REMAINDER)
parser.add_argument('--host', required=True)
parser.add_argument('--port', type=int, default=22)
parser.add_argument('--pubkey',
                    default=os.path.expanduser('~/.ssh/id_rsa.pub'))
parser.add_argument('--privkey', default=os.path.expanduser('~/.ssh/id_rsa'))
parser.add_argument('--username', required=True)
parser.add_argument('--known-hosts',
                    default=os.path.expanduser('~/.ssh/known_hosts'))
parser.add_argument('--passphrase', default='')

if __name__ == '__main__':
    args = parser.parse_args()
    _ssh(args)
