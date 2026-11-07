import io
from pathlib import Path

from clifire import command, out

from wgm.commands.base import WgmCommand
from wgm.errors import WgmError


class ShowCommand(WgmCommand):
    _name = 'show'
    _help = 'Show the config file of a WireGuard user.'

    name = command.Field(pos=0, help='The user name')
    qr = command.Field(default=False, help='Show the config as a QR code')
    output = command.Field(
        default='',
        alias=['o'],
        help='Write the config to the given file',
    )

    def fire(self):
        server = self.server()
        user = server.find(self.name)
        if not user:
            raise WgmError(f'User "{self.name}" not exists.')
        text = user.conf.render()
        if self.output:
            server.write(Path(self.output), text, mode=0o600)
            out.success(f'Config file "{self.output}" created.')
        elif self.qr:
            print(self._qr(text))
        else:
            print(text, end='')
        return 0

    @staticmethod
    def _qr(text):
        import qrcode

        code = qrcode.QRCode(border=1)
        code.add_data(text)
        code.make()
        buffer = io.StringIO()
        code.print_ascii(out=buffer, invert=True)
        return buffer.getvalue()
