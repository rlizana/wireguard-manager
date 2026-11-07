from clifire import command, out

from wgm.commands.base import WgmCommand


class ListCommand(WgmCommand):
    _name = 'list'
    _help = 'List all users.'

    status = command.Field(
        default=False,
        help='Show the last handshake of every user',
    )

    def fire(self):
        server = self.server()
        if not server.users:
            out.warn('Not users.')
            return 0
        handshakes = server.handshakes() if self.status else None
        users = sorted(server.users.values(), key=lambda user: user.name)
        data = []
        for user in users:
            row = {
                'ID': str(server.user_id(user.address)),
                'Name': user.name,
                'Public key': user.public_key,
                'Address': str(user.address),
            }
            if self.status:
                row['Status'] = server.status(user.public_key, handshakes)
            data.append(row)
        out.table(data)
        return 0
