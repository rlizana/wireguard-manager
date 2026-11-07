from clifire import command

from wgm.server import Server


class WgmCommand(command.Command):
    config_path = command.Field(
        default='/etc/wireguard',
        alias=['c'],
        help='Set path to wireguard config',
    )
    wg_config_file = command.Field(
        default='',
        alias=['w'],
        help='Set config file to wireguard config',
    )

    def server(self):
        return Server.load(self.config_path, self.wg_config_file)
