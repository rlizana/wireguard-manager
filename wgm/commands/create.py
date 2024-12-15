import os

from wgm.command import Command
from cleo.helpers import argument, option


class CreateCommand(Command):
    name = 'create'
    description = 'Create a new WireGuard user.'
    arguments = [
        argument(
            name='name',
            description='The user name',
        ),
    ]
    options = [
        option(
            'private-cdir',
            description=('Force private network to set user address'),
            default=False,
            flag=False,
        ),
        option(
            'allowed-cdirs',
            description=(
                'Set cdirs to be allowed to connect seprarated by comma, by '
                'default is 0.0.0.0/24'),
            default='0.0.0.0/24',
            flag=False,
        )
    ]

    def handle(self):
        self.read_config()
        name = self.argument('name')
        if name in self.config.users.keys():
            self.line(f'User "{name}" already exists.', 'error')
            return 1
        clients_path = os.path.join(self.config.config_path, 'clients')
        if not os.path.exists(clients_path):
            os.mkdir(clients_path)
        user_path = os.path.join(clients_path, name)
        if os.path.exists(user_path):
            self.line(f'User "{name}" already exists.', 'error')
            return 1
        os.mkdir(user_path)

        # Generate private key
        self.shell(
            f'wg genkey | tee {user_path}/private_key '
            f'| wg pubkey > {user_path}/public_key')
        user_private_key = self.read_file(f'{user_path}/private_key')
        user_public_key = self.read_file(f'{user_path}/private_key')

        # Prepare data
        user_ids = [int(u['id']) for u in self.config.users]
        user_ids += [self.config.server_id]
        user_id = 1
        while user_id in user_ids:
            user_id += 1
        allowed_cdirs = (
            self.option('allowed-cdirs').split(',')
            if self.option('allowed-cdirs') else []
        )
        cdir = self.config.cdir.copy()
        cdir['ip'][3] = 0
        allowed_cdirs.insert(0, self.dict_to_cdir(cdir))
        user_address = self.config.cdir
        user_address['ip'][3] = user_id
        user_address['mask'] = 32

        # Create config user
        self.write_config_file(f'{user_path}/{name}.conf', {
            'Interface': [{
                'PrivateKey': user_private_key,
                'Address': self.dict_to_cdir(user_address),
            }],
            'Peer': [{
                'PublicKey': self.config.server_public_key,
                'AllowedIPs': ', '.join(allowed_cdirs),
                'Endpoint': self.config.endpoint,
                'PersistentKeepalive': 25,
            }]
        })
        self.line(f'Config file "{user_path}/{name}.conf" created.', 'info')

        # Update server config
        if 'Peer' not in self.config.wg:
            self.config.wg['Peer'] = []
        if not isinstance(self.config.wg['Peer'], list):
            self.config.wg['Peer'] = [self.config.wg['Peer']]
        self.config.wg['Peer'].append({
            'PublicKey': user_public_key,
            'AllowedIPs': self.dict_to_cdir(user_address),
        })
        self.write_config_file(self.config.wg_config_file, self.config.wg)
        self.line(f'User "{name}" created.', 'success')
