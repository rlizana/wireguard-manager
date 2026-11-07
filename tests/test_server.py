import ipaddress
import time

import pytest

from wgm.errors import WgmError
from wgm.server import Server


def test_load_not_exists(tmp_path):
    with pytest.raises(WgmError) as error:
        Server.load(tmp_path / 'nope')
    assert error.value.code == 100


def test_load_without_public_key(config_path, fake_runner):
    (config_path / 'server_public_key').unlink()
    with pytest.raises(WgmError) as error:
        Server.load(config_path)
    assert error.value.code == 102


def test_load(config_path, fake_runner):
    server = Server.load(config_path)
    assert server.interface_name == 'wg0'
    assert server.listen_port == '51820'
    assert server.server_id == 1
    assert server.network == ipaddress.ip_network('1.2.3.0/24')
    assert server.endpoint() == 'vpn.example.com:51820'
    assert server.users == {}


def test_next_id(config_path, fake_runner):
    server = Server.load(config_path)
    assert server.next_id() == 2
    user = server.create_user('user-1')
    assert server.next_id() == 3
    assert str(user.address) == '1.2.3.2/32'


def test_create_delete_user(config_path, fake_runner):
    server = Server.load(config_path)
    user = server.create_user('user-1', ['10.0.0.0/24'])
    interface = user.conf.section('Interface')
    peer = user.conf.section('Peer')
    assert interface.get('Address') == '1.2.3.2/32'
    assert peer.get('AllowedIPs') == '1.2.3.0/24, 10.0.0.0/24'
    assert peer.get('Endpoint') == 'vpn.example.com:51820'
    assert len(server.peers) == 1
    assert (config_path / 'wg0.conf.bak').is_file()
    assert server.find('user-1').public_key == user.public_key
    server.delete_user('user-1')
    assert server.find('user-1') is None
    assert Server.load(config_path).peers == []
    assert not user.path.exists()


def test_create_existing_user(config_path, fake_runner):
    server = Server.load(config_path)
    server.create_user('user-1')
    with pytest.raises(WgmError):
        server.create_user('user-1')


def test_delete_missing_user(config_path, fake_runner):
    server = Server.load(config_path)
    with pytest.raises(WgmError):
        server.delete_user('user-1')


def test_create_user_rollback(config_path, fake_runner, monkeypatch):
    server = Server.load(config_path)

    def fail():
        raise RuntimeError('boom')

    monkeypatch.setattr(server, 'save', fail)
    with pytest.raises(RuntimeError):
        server.create_user('user-1')
    assert not (config_path / 'clients' / 'user-1').exists()


def test_permissions(config_path, fake_runner):
    server = Server.load(config_path)
    user = server.create_user('user-1')
    assert (config_path / 'clients').stat().st_mode & 0o777 == 0o700
    assert user.path.stat().st_mode & 0o777 == 0o700
    assert (user.path / 'private_key').stat().st_mode & 0o777 == 0o600
    assert (user.path / 'public_key').stat().st_mode & 0o777 == 0o644
    assert (user.path / 'user-1.conf').stat().st_mode & 0o777 == 0o600
    assert (config_path / 'wg0.conf').stat().st_mode & 0o777 == 0o600


def test_wg0_keeps_postup(config_path, fake_runner):
    Server.load(config_path).create_user('user-1')
    wg0 = (config_path / 'wg0.conf').read_text()
    assert 'PostUp = iptables -A FORWARD -i wg0 -j ACCEPT' in wg0
    assert 'PostDown = iptables -t nat -D PREROUTING -i eth0 -j ACCEPT' in wg0
    assert 'ListenPort = 51820' in wg0


def test_apply(config_path, fake_runner):
    server = Server.load(config_path)
    server.apply()
    assert ['wg-quick', 'strip', str(config_path / 'wg0.conf')] in (
        fake_runner.calls
    )
    assert ['wg', 'syncconf', 'wg0', str(config_path / '.wg0.conf')] in (
        fake_runner.calls
    )
    assert not (config_path / '.wg0.conf').exists()


def test_handshakes(config_path, fake_runner):
    server = Server.load(config_path)
    assert server.handshakes() == {}
    assert server.status('abc') == '-'
    fake_runner.show = 'abc 0\n'
    assert server.status('abc') == 'never'
    stamp = int(time.time()) - 1800
    fake_runner.show = f'abc {stamp}\n'
    assert server.status('abc') == '30m'
