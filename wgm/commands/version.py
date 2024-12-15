from wgm import __version__
from wgm.command import Command


class VersionCommand(Command):
    name = 'version'
    description = 'Show version.'
    check_config = False

    def handle(self):
        self.line(f'Version {__version__}', 'info')
