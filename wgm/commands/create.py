from clifire import command, out

from wgm.commands.base import WgmCommand


class CreateCommand(WgmCommand):
    _name = 'create'
    _help = 'Create a new WireGuard user.'

    name = command.Field(pos=0, help='The user name')
    allowed_cdirs = command.Field(
        default=['0.0.0.0/24'],
        alias=['a'],
        help=(
            'Set cdirs to be allowed to connect separated by comma, by '
            'default is 0.0.0.0/24'
        ),
    )
    endpoint = command.Field(
        default='',
        help='Set the endpoint of the server, by default hostname -f',
    )
    apply = command.Field(
        default=False,
        help='Apply changes to the running interface',
    )

    def fire(self):
        server = self.server()
        user = server.create_user(self.name, self.allowed_cdirs, self.endpoint)
        out.info(f'Config file "{user.path}/{user.name}.conf" created.')
        out.success(f'User "{user.name}" created.')
        if self.apply:
            server.apply()
        return 0
