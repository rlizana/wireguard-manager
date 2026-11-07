import ipaddress
import os
import shutil
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

from wgm import keys, runner
from wgm.conf import Conf
from wgm.errors import WgmError


@dataclass
class User:
    name: str
    public_key: str
    address: ipaddress.IPv4Interface
    path: Path
    conf: Conf


@dataclass
class Server:
    path: Path
    wg_file: Path
    wg: Conf
    public_key: str
    users: dict = field(default_factory=dict)

    @classmethod
    def load(cls, config_path, wg_config_file=''):
        path = Path(config_path).expanduser().absolute()
        if not path.is_dir():
            raise WgmError(f'Path {path} not exists!', code=100)
        wg_file = (
            Path(wg_config_file).expanduser()
            if wg_config_file
            else path / 'wg0.conf'
        )
        if not wg_file.is_file():
            raise WgmError(f'Config file {wg_file} not exists!', code=101)
        public_key = cls._read(path / 'server_public_key')
        if not public_key:
            raise WgmError(
                'Not server public key, check if file '
                f'{path}/server_public_key exists',
                code=102,
            )
        server = cls(
            path=path,
            wg_file=wg_file,
            wg=Conf.load(wg_file),
            public_key=public_key,
        )
        server._load_users()
        return server

    @property
    def interface(self):
        return self.wg.section('Interface')

    @property
    def interface_name(self):
        return self.wg_file.stem

    @property
    def listen_port(self):
        return self.interface.get('ListenPort', '51820')

    @property
    def address(self):
        value = self.interface.get('Address')
        if '/' not in value:
            value = f'{value}/24'
        return ipaddress.ip_interface(value)

    @property
    def server_id(self):
        return self.user_id(self.address)

    @property
    def network(self):
        return self.address.network

    @property
    def peers(self):
        return self.wg.sections('Peer')

    def find(self, name):
        for user in self.users.values():
            if user.name == name:
                return user
        return None

    def endpoint(self, override=''):
        if override:
            return override
        hostname = runner.run(['hostname', '-f']).stdout
        return f'{hostname}:{self.listen_port}'

    def next_id(self):
        used = {self.server_id}
        used.update(self.user_id(user.address) for user in self.users.values())
        user_id = 1
        while user_id in used:
            user_id += 1
        return user_id

    def create_user(self, name, allowed_ips=None, endpoint=''):
        allowed_ips = list(allowed_ips or ['0.0.0.0/24'])
        if self.find(name) or (self.path / 'clients' / name).exists():
            raise WgmError(f'User "{name}" already exists.')
        clients = self.path / 'clients'
        clients.mkdir(mode=0o700, parents=True, exist_ok=True)
        user_path = clients / name
        user_path.mkdir(mode=0o700)
        try:
            return self._create_user(name, user_path, allowed_ips, endpoint)
        except Exception:
            shutil.rmtree(user_path, ignore_errors=True)
            raise

    def delete_user(self, name):
        user = self.find(name)
        if not user:
            raise WgmError(f'User "{name}" not exists.')
        for peer in self.peers:
            if peer.get('PublicKey') == user.public_key:
                self.wg.remove(peer)
                break
        self.save()
        shutil.rmtree(user.path)
        del self.users[user.public_key]
        return user

    def save(self):
        if self.wg_file.exists():
            backup = self.wg_file.with_suffix(f'{self.wg_file.suffix}.bak')
            shutil.copy2(self.wg_file, backup)
        self.write(self.wg_file, self.wg.render(), mode=0o600)

    def apply(self):
        stripped = runner.run(['wg-quick', 'strip', str(self.wg_file)]).stdout
        path = self.write(
            self.path / f'.{self.interface_name}.conf',
            stripped + '\n',
            mode=0o600,
        )
        try:
            runner.run(['wg', 'syncconf', self.interface_name, str(path)])
        finally:
            os.remove(path)

    def handshakes(self):
        result = runner.run(
            ['wg', 'show', self.interface_name, 'latest-handshakes'],
            check=False,
        )
        if not result.ok:
            return {}
        stamps = {}
        for line in result.stdout.splitlines():
            parts = line.split()
            if len(parts) == 2:
                stamps[parts[0]] = int(parts[1])
        return stamps

    def status(self, public_key, handshakes=None):
        if handshakes is None:
            handshakes = self.handshakes()
        if not handshakes:
            return '-'
        stamp = handshakes.get(public_key, 0)
        if not stamp:
            return 'never'
        minutes = int((time.time() - stamp) / 60)
        if minutes < 1:
            return 'now'
        if minutes < 60:
            return f'{minutes}m'
        return f'{minutes // 60}h'

    @staticmethod
    def user_id(address):
        return int(str(address.ip).split('.')[3])

    def _create_user(self, name, user_path, allowed_ips, endpoint):
        private_key, public_key = keys.generate()
        self.write(user_path / 'private_key', private_key + '\n', mode=0o600)
        self.write(user_path / 'public_key', public_key + '\n', mode=0o644)
        octets = str(self.address.ip).split('.')
        octets[3] = str(self.next_id())
        user_address = ipaddress.ip_interface('{}/32'.format('.'.join(octets)))
        allowed = [str(self.network), *allowed_ips]
        user_conf = Conf()
        user_interface = user_conf.add_section('Interface')
        user_interface.set('PrivateKey', private_key)
        user_interface.set('Address', str(user_address))
        user_peer = user_conf.add_section('Peer')
        user_peer.set('PublicKey', self.public_key)
        user_peer.set('AllowedIPs', ', '.join(allowed))
        user_peer.set('Endpoint', self.endpoint(endpoint))
        user_peer.set('PersistentKeepalive', '25')
        self.write(user_path / f'{name}.conf', user_conf.render(), mode=0o600)
        peer = self.wg.add_section('Peer')
        peer.set('PublicKey', public_key)
        peer.set('AllowedIPs', str(user_address))
        self.save()
        user = User(
            name=name,
            public_key=public_key,
            address=user_address,
            path=user_path,
            conf=user_conf,
        )
        self.users[public_key] = user
        return user

    def _load_users(self):
        clients = self.path / 'clients'
        if not clients.is_dir():
            clients.mkdir(mode=0o700, parents=True)
            return
        for path in sorted(clients.iterdir()):
            if not path.is_dir() or path.name.startswith(('.', '_')):
                continue
            conf_file = path / f'{path.name}.conf'
            if not conf_file.is_file():
                continue
            conf = Conf.load(conf_file)
            section = conf.section('Interface')
            if not section:
                raise WgmError(f'Invalid config file {conf_file}')
            public_key = self._read(path / 'public_key')
            self.users[public_key] = User(
                name=path.name,
                public_key=public_key,
                address=ipaddress.ip_interface(section.get('Address')),
                path=path,
                conf=conf,
            )

    @staticmethod
    def _read(path):
        if not path.is_file():
            return ''
        return path.read_text().strip()

    @staticmethod
    def write(path, text, mode=0o600):
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        handle, tmp = tempfile.mkstemp(dir=path.parent, prefix=f'.{path.name}')
        try:
            with os.fdopen(handle, 'w') as file:
                file.write(text)
            os.chmod(tmp, mode)
            os.replace(tmp, path)
        except Exception:
            if os.path.exists(tmp):
                os.remove(tmp)
            raise
        return path
