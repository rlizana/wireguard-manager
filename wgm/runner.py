import subprocess
from dataclasses import dataclass

from wgm.errors import WgmError


@dataclass
class Result:
    code: int = 0
    stdout: str = ''
    stderr: str = ''

    @property
    def ok(self):
        return self.code == 0


def run(args, stdin=None, timeout=10, check=True):
    try:
        process = subprocess.run(
            args,
            input=stdin,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exception:
        raise WgmError(f'Command not found: {args[0]}') from exception
    except subprocess.TimeoutExpired as exception:
        raise WgmError(f'Timeout expired: {" ".join(args)}') from exception
    result = Result(
        code=process.returncode,
        stdout=process.stdout.strip(),
        stderr=process.stderr.strip(),
    )
    if check and not result.ok:
        detail = result.stderr or result.stdout
        raise WgmError(
            f'Command failed ({result.code}): {" ".join(args)}: {detail}'
        )
    return result
