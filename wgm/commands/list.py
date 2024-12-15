from wgm.command import Command


class ListCommand(Command):
    name = 'list'
    description = 'List all users.'

    def handle(self):
        self.read_config()
        users = self.config.users
        if not users:
            self.line('Not users.', 'warn')
            return 0
        table = self.table()
        table.set_headers(['ID', 'Name', 'Private key', 'Address'])
        table.set_rows([
            [
                str(user['id']),
                user['name'],
                private_key,
                self.dict_to_cdir(user['cdir']),
            ] for private_key, user in users.items()
        ])
        table.render()
