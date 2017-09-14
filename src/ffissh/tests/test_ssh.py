
from pytest import raises

from ffissh import ssh
from ffissh.exceptions import SSHError


def test_a_thing():
    with raises(SSHError) as e:
        connection = ssh.Connection('127.0.0.1', username='nobody')
        with connection:
            pass
    assert e.value[1] == -18
