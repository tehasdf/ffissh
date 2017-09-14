
import os
import argparse

from ffissh.ssh import Connection, Sftp


def _ssh(args):
    conn = Connection(host=args.host, port=args.port, username=args.username)
    conn.privkey = args.privkey
    conn.pubkey = args.pubkey
    conn.passphrase = args.passphrase
    with conn:
        sftp = Sftp(conn)
        with sftp.open('f.json') as f:
            print(f.read())


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
