import os
import subprocess

from cleo.commands.command import Command as BaseCommand
from cleo.helpers import option
from cleo.io.io import IO
from cleo.io.outputs.output import Verbosity
from wgm.config import Config


class Command(BaseCommand):

    def configure(self) -> None:
        self._definition.add_option(
            option(
                'config-path',
                'c',
                description='Set path to wireguard config',
                default='/etc/wireguard',
                flag=False,
            )
        )
        self._definition.add_option(
            option(
                'wg-config-file',
                'w',
                description='Set config file to wireguard config',
                default=False,
                flag=False,
            )
        )
        super().configure()

    def execute(self, io: IO) -> int:
        self._io = io
        self.config = Config(
            config_path=os.path.abspath(self.option('config-path')),
            wg_config_file=self.option('wg-config-file'),
        )
        if self.config.wg_config_file is False:
            self.config.wg_config_file = os.path.join(
                self.config.config_path, 'wg0.conf')

        self.add_style('error', fg='red', options=['bold'])
        self.add_style('info', fg='blue')
        self.add_style('warn', fg='yellow')
        self.add_style('success', fg='green')

        try:
            status_code = super().execute(io)
        except InterruptedError as exception:
            self.line(exception.strerror or 'Unknown error', 'error')
            status_code = exception.errno or 1
        return 0 if status_code is None else status_code

    def shell(self, cmd):
        self.line(f'$: {cmd}', 'info', verbosity=Verbosity.VERBOSE)
        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, shell=True)
        try:
            stdout, stderr = process.communicate(timeout=10)
            if stdout:
                self.line(stdout, 'success', verbosity=Verbosity.VERBOSE)
            if stderr:
                self.line(stderr, 'error', verbosity=Verbosity.VERBOSE)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            self.line_error(f'Timeout expired for command: {cmd}')
            raise Exception('Timeout expired')
        if process.returncode != 0 and stderr:
            self.line_error(f'Error executing command: {cmd}')
            self.line_error(stderr)
            raise Exception(process.returncode)
        return stdout.strip()

    def read_file(self, filename):
        if not os.path.exists(filename):
            return False
        with open(filename, 'r') as f:
            content = f.read()
        if content.endswith('\n'):
            content = content[:-1]
        return content

    def read_config_file(self, filename):
        config = {}
        current_section = None
        with open(filename, 'r') as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if line.startswith('[') and line.endswith(']'):
                    current_section = line[1:-1]
                    if current_section not in config:
                        config[current_section] = {}
                    else:
                        if isinstance(config[current_section], list):
                            config[current_section].append({})
                        else:
                            config[current_section] = [
                                config[current_section], {}]
                elif current_section is None:
                    continue
                else:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    section = config[current_section]
                    if isinstance(section, list):
                        section = section[-1]
                    if key in section:
                        if isinstance(section[key], list):
                            section[key].append(value)
                        else:
                            section[key] = [section[key], value]
                    else:
                        section[key] = value
        return config

    def write_config_file(self, filename, config_dict):
        with open(filename, 'w') as file:
            for section, items in config_dict.items():
                if isinstance(items, dict):
                    items = [items]
                for item in items:
                    file.write(f'[{section}]\n')
                    for key, value in item.items():
                        if isinstance(value, list):
                            for v in value:
                                file.write(f'{key} = {v}\n')
                        else:
                            file.write(f'{key} = {value}\n')
                    file.write('\n')

    def read_config(self):
        # Check paths
        if not os.path.exists(self.config.config_path):
            raise InterruptedError(
                100, f'Path {self.config.config_path} not exists!')
        if not os.path.exists(self.config.wg_config_file):
            raise InterruptedError(
                101, f'Config file {self.config.wg_config_file} not exists!')

        # Read users
        clients_path = os.path.join(self.config.config_path, 'clients')
        if not os.path.exists(clients_path):
            os.mkdir(clients_path)
        self.config.users = {}
        for file in os.listdir(clients_path):
            absfile = os.path.join(clients_path, file)
            if not os.path.isdir(absfile):
                continue
            if any(file.startswith(x) for x in ['.', '_']):
                continue
            conf_file = os.path.join(clients_path, file, f'{file}.conf')
            if not os.path.exists(conf_file):
                continue
            config = self.read_config_file(conf_file)
            public_key = self.read_file(
                os.path.join(clients_path, file, 'public_key'))
            cdir = self.cdir_to_dict(config['Interface']['Address'])
            self.config.users[public_key] = {
                'id': cdir['ip'][3],
                'name': file,
                'cdir': cdir,
                'config': config,
            }

        # Read wg0
        self.config.wg = self.read_config_file(self.config.wg_config_file)
        if 'Peer' not in self.config.wg:
            self.config.wg['Peer'] = []
        if not isinstance(self.config.wg['Peer'], list):
            self.config.wg['Peer'] = [self.config.wg['Peer']]
        self.config.hostname = self.shell('hostname -f')
        self.config.endpoint = ':'.join([
            self.config.hostname,
            self.config.wg['Interface']['ListenPort']
        ])
        cdir = self.cdir_to_dict(self.config.wg['Interface']['Address'])
        self.config.server_id = cdir['ip'][3]
        self.config.cdir = cdir
        self.config.server_public_key = self.read_file(
            os.path.join(self.config.config_path, 'server_public_key')
        )
        if not self.config.server_public_key:
            raise InterruptedError(
                102,
                'Not server public key, check if file '
                f'{self.config.config_path}/server_public_key exists'
            )

    def cdir_to_dict(self, cdir_address: str) -> dict:
        parts = cdir_address.split('/')
        ip = [int(b) for b in parts[0].split('.')]
        mask = int(parts[1]) if len(parts) == 2 else 24
        return {
            'ip': ip,
            'mask': mask,
        }

    def dict_to_cdir(self, cdir_address: dict) -> str:
        ip = '.'.join([str(b) for b in cdir_address['ip']])
        return f'{ip}/{cdir_address["mask"]}'
