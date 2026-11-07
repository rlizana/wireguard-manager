from clifire import command, out

from wgm.commands.base import WgmCommand


class DeleteCommand(WgmCommand):
    _name = 'delete'
    _help = 'Delete a WireGuard user.'

    name = command.Field(pos=0, help='The user name')
    apply = command.Field(
        default=False,
        help='Apply changes to the running interface',
    )

    def fire(self):
        server = self.server()
        server.delete_user(self.name)
        out.success(f'User "{self.name}" deleted.')
        if self.apply:
            server.apply()
        return 0
