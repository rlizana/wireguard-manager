import os
import shutil

from wgm.command import Command
from cleo.helpers import argument


class DeleteCommand(Command):
    name = 'delete'
    description = 'Delete a WireGuard user.'
    arguments = [
        argument(
            name='name',
            description='The user name',
        ),
    ]

    def handle(self):
        self.read_config()
        name = self.argument('name')
        public_key = None
        for key, user in self.config.users.items():
            if user['name'] == name:
                public_key = key
                break
        if not public_key:
            self.line(f'User "{name}" not exists.', 'error')
            return 1
        for peer in self.config.wg['Peer']:
            if peer['PublicKey'] == public_key:
                self.config.wg['Peer'].remove(peer)
                break
        self.write_config_file(self.config.wg_config_file, self.config.wg)
        clients_path = os.path.join(self.config.config_path, 'clients')
        shutil.rmtree(os.path.join(clients_path, name))
        self.line(f'User "{name}" deleted.', 'success')
