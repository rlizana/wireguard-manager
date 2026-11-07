import base64
import hashlib
import shutil
from pathlib import Path

import pytest
from clifire import out

from wgm import runner
from wgm.main import create_app

SAMPLE = Path(__file__).parent / 'sample'


def key(seed):
    digest = hashlib.sha256(seed.encode()).digest()
    return base64.b64encode(digest).decode()


class FakeRunner:
    def __init__(self):
        self.calls = []
        self.count = 0
        self.show = ''

    def __call__(self, args, stdin=None, timeout=10, check=True):
        self.calls.append(args)
        if args[:2] == ['wg', 'genkey']:
            self.count += 1
            return runner.Result(code=0, stdout=key(f'key-{self.count}'))
        if args[:2] == ['wg', 'pubkey']:
            return runner.Result(code=0, stdout=key(f'pub-{stdin.strip()}'))
        if args[:2] == ['wg', 'show']:
            return runner.Result(code=0, stdout=self.show)
        if args[:2] == ['wg-quick', 'strip']:
            return runner.Result(
                code=0, stdout='[Interface]\nPrivateKey = private'
            )
        if args[:2] == ['hostname', '-f']:
            return runner.Result(code=0, stdout='vpn.example.com')
        return runner.Result(code=0, stdout='')


@pytest.fixture
def config_path(tmp_path):
    path = tmp_path / 'wireguard'
    shutil.copytree(SAMPLE, path)
    return path


@pytest.fixture
def fake_runner(monkeypatch):
    fake = FakeRunner()
    monkeypatch.setattr(runner, 'run', fake)
    return fake


@pytest.fixture
def app(fake_runner):
    out.setup(ansi=False)
    return create_app()
