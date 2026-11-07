# WireGuard Manager (wgm)

WireGuard Manager (wgm) is a command-line tool designed to simplify the
management of WireGuard VPN users. It allows you to create, list, show and
delete WireGuard users with a few simple commands.

## Requirements

- Python 3.12 or higher
- [wireguard-tools](https://www.wireguard.com/install/) (`wg`, `wg-quick`)
- Root privileges to read and write the WireGuard config directory
  (`/etc/wireguard` by default)

## Installation

### From PyPI

```bash
pip install wgm
```

### As a tool with uv

```bash
uv tool install wgm
```

### From source

```bash
git clone https://github.com/rlizana/wgm.git
cd wgm
uv tool install .
```

If you install the tool as root, the executable lands in `/root/.local/bin`;
add it to your `PATH` or install it for your user instead.

## Usage

```bash
wgm help
wgm help create
```

| Command  | Description                                              |
| -------- | -------------------------------------------------------- |
| `create` | Create a new user and its config file                    |
| `list`   | List all users (`--status` shows the last handshake)     |
| `show`   | Show the config of a user (`--qr` for mobile, `-o` file) |
| `delete` | Delete a user and its peer from the server config        |
| `apply`  | Apply the server config to the running interface         |
| `version` | Show the version                                        |

All the commands accept `--config-path` (`-c`) to point to another WireGuard
directory and `--wg-config-file` (`-w`) to use another server config file.

### Examples

```bash
sudo wgm create user-1
sudo wgm create user-2 --allowed-cdirs 10.0.0.0/24,192.168.1.0/24
sudo wgm create user-3 --endpoint vpn.example.com:51820 --apply
sudo wgm list --status
sudo wgm show user-1
sudo wgm show user-1 --qr
sudo wgm show user-1 -o /tmp/user-1.conf
sudo wgm delete user-1 --apply
```

The expected layout of the config directory is:

```
/etc/wireguard
├── wg0.conf
├── server_public_key
└── clients
    └── user-1
        ├── private_key
        ├── public_key
        └── user-1.conf
```

Every write to `wg0.conf` keeps a `wg0.conf.bak` copy and is atomic, so a
failure never leaves a truncated server config. Comments and `PostUp`/`PostDown`
lines are preserved.

`create` and `delete` only edit the config file; use `--apply` (or `wgm apply`)
to reload the running interface with `wg syncconf`, which does not drop the
existing connections.

## Development

```bash
uv sync --all-extras
uv run pre-commit install
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

The tests do not need `wireguard-tools`: `wg` is replaced by a fake runner, and
the config fixtures live in `tests/sample`.

## Building the package

```bash
uv build
```

## Publishing

```bash
UV_PUBLISH_TOKEN=... uv publish
```

The `Publish` workflow does the same from a `v*` tag or manually from the
GitHub UI.
