import shutil

import pytest
from clifire import out

from wgm import __version__


def output(capsys):
    return out.ansi_clean(capsys.readouterr().out)


def test_path_not_exists(app, config_path):
    (config_path / 'server_public_key').unlink()
    with pytest.raises(SystemExit) as error:
        app.fire(f'create username --config-path {config_path}')
    assert error.value.code == 102
    shutil.rmtree(config_path)
    with pytest.raises(SystemExit) as error:
        app.fire(f'list --config-path {config_path}')
    assert error.value.code == 100


def test_list(app, config_path, capsys):
    app.fire(f'list --config-path {config_path}')
    assert 'Not users.' in output(capsys)


def test_create(app, config_path, capsys):
    app.fire(f'create username --config-path {config_path}')
    assert 'User "username" created.' in output(capsys)
    assert (config_path / 'clients' / 'username').is_dir()
    with pytest.raises(SystemExit) as error:
        app.fire(f'create username --config-path {config_path}')
    assert error.value.code == 1
    assert 'User "username" already exists.' in output(capsys)


def test_delete(app, config_path, capsys):
    with pytest.raises(SystemExit) as error:
        app.fire(f'delete username --config-path {config_path}')
    assert error.value.code == 1
    assert 'User "username" not exists.' in output(capsys)
    app.fire(f'create username --config-path {config_path}')
    output(capsys)
    app.fire(f'delete username --config-path {config_path}')
    assert 'User "username" deleted.' in output(capsys)


def test_create_list_delete(app, config_path, capsys):
    app.fire(f'create username --config-path {config_path}')
    app.fire(f'list --config-path {config_path}')
    assert 'username' in output(capsys)
    app.fire(f'delete username --config-path {config_path}')
    app.fire(f'list --config-path {config_path}')
    assert 'Not users.' in output(capsys)


def test_create_user_wg0(app, config_path):
    app.fire(f'create user-1 --config-path {config_path}')
    user_path = config_path / 'clients' / 'user-1'
    user_conf = (user_path / 'user-1.conf').read_text()
    wg0 = (config_path / 'wg0.conf').read_text()
    server_key = (config_path / 'server_public_key').read_text().strip()
    public_key = (user_path / 'public_key').read_text().strip()
    private_key = (user_path / 'private_key').read_text().strip()
    assert 'Address = 1.2.3.2/32' in user_conf
    assert 'AllowedIPs = 1.2.3.0/24, 0.0.0.0/24' in user_conf
    assert f'PrivateKey = {private_key}' in user_conf
    assert f'PublicKey = {server_key}' in user_conf
    assert f'PublicKey = {public_key}' in wg0


def test_create_allowed_cdirs(app, config_path):
    app.fire(
        f'create user-1 --allowed-cdirs 10.0.0.0/24,10.1.0.0/24 '
        f'--config-path {config_path}'
    )
    user_conf = (config_path / 'clients' / 'user-1' / 'user-1.conf').read_text()
    assert 'AllowedIPs = 1.2.3.0/24, 10.0.0.0/24, 10.1.0.0/24' in user_conf


def test_show(app, config_path, capsys):
    app.fire(f'create username --config-path {config_path}')
    output(capsys)
    app.fire(f'show username --config-path {config_path}')
    printed = output(capsys)
    assert '[Interface]' in printed
    assert 'PrivateKey' in printed
    with pytest.raises(SystemExit) as error:
        app.fire(f'show other --config-path {config_path}')
    assert error.value.code == 1


def test_show_output(app, config_path, tmp_path):
    app.fire(f'create username --config-path {config_path}')
    target = tmp_path / 'exported.conf'
    app.fire(f'show username -o {target} --config-path {config_path}')
    source = config_path / 'clients' / 'username' / 'username.conf'
    assert target.read_text() == source.read_text()
    assert target.stat().st_mode & 0o777 == 0o600


def test_show_qr(app, config_path, capsys):
    app.fire(f'create username --config-path {config_path}')
    output(capsys)
    app.fire(f'show username --qr --config-path {config_path}')
    printed = output(capsys)
    assert '[Interface]' not in printed
    assert len(printed.strip().splitlines()) > 2


def test_list_status(app, config_path, fake_runner, capsys):
    app.fire(f'create user-1 --config-path {config_path}')
    key_path = config_path / 'clients' / 'user-1' / 'public_key'
    fake_runner.show = f'{key_path.read_text().strip()} 0'
    output(capsys)
    app.fire(f'list --status --config-path {config_path}')
    printed = output(capsys)
    assert 'never' in printed
    assert 'user-1' in printed
    assert 'Public key' in printed


def test_version(app, capsys):
    app.fire('version')
    assert __version__ in output(capsys)
