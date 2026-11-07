from clifire import application

from wgm import commands
from wgm.__version__ import __version__


def create_app():
    app = application.App(name='WireGuard Manager', version=__version__)
    app.add_commands(
        [
            commands.apply.ApplyCommand,
            commands.create.CreateCommand,
            commands.delete.DeleteCommand,
            commands.list.ListCommand,
            commands.show.ShowCommand,
        ]
    )
    return app


def main():
    create_app().fire()
