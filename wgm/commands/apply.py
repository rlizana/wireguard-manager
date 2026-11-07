from clifire import out

from wgm.commands.base import WgmCommand


class ApplyCommand(WgmCommand):
    _name = 'apply'
    _help = 'Apply the config file to the running interface.'

    def fire(self):
        server = self.server()
        server.apply()
        out.success(f'Interface "{server.interface_name}" updated.')
        return 0
