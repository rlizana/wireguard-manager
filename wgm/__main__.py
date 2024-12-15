from cleo.application import Application
from cleo.commands.list_command import ListCommand as HelpListCommand
from wgm import __version__
from wgm.commands.create import CreateCommand
from wgm.commands.delete import DeleteCommand
from wgm.commands.list import ListCommand
from wgm.commands.version import VersionCommand


def create_app():
    app = Application('WireGuard Manager', __version__)

    # Reconfigure default command list to help-list
    help_list_command = HelpListCommand()
    help_list_command.name = 'help-list'
    app._default_command = help_list_command.name
    app.add(help_list_command)

    app.add(CreateCommand())
    app.add(DeleteCommand())
    app.add(ListCommand())
    app.add(VersionCommand())

    return app


def main():
    app = create_app()
    app.run()


if __name__ == '__main__':
    main()
