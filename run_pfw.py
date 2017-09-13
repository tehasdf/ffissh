# usage is similar to run.py, but pass a port, eg.
# $ python run_pfw.py --host host.com --username root 15126
# and then on the server do `$ curl localhost:15126`, and you should see the
# request printed in this program


import os
import argparse

from ffissh.ssh import Connection


def _ssh(args):
    conn = Connection(host=args.host, port=args.port, username=args.username)
    conn.privkey = args.privkey
    conn.pubkey = args.pubkey
    conn.passphrase = args.passphrase
    buf = ''
    with conn:
        chan = conn.request_portforward(args.forwardport)
        while True:
            conn.waitsocket()
            buf += chan.read_nonblocking()
            if buf.endswith('\r\n\r\n'):
                print buf
                break


parser = argparse.ArgumentParser()
parser.add_argument('forwardport', type=int)
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
