# WireGuard Manager (wgm)

WireGuard Manager (wgm) is a command-line tool designed to simplify the management of WireGuard VPN users. It allows you to easily create, list, and delete WireGuard users with a few simple commands.

## Installation

### From Source

To install WireGuard Manager (wgm) from source, follow these steps:

1. Clone the repository:
    ```bash
    git clone https://github.com/rlizana/wgm.git
    cd wgm
    ```

2. Install the dependencies using Poetry:
    ```bash
    poetry install
    ```

3. Install the package globally:
    ```bash
    poetry build
    pip install dist/*.whl
    ```

This will allow you to call [wgm](http://_vscodecontentref_/0) from anywhere in the console.

### As a Package

To install WireGuard Manager (wgm) as a package, you can use pip:

```bash
pip install wgm
```

## Usage

To use the WireGuard Manager, follow these steps:

1. Activate the virtual environment:
    ```bash
    poetry shell
    ```

2. Run the application:
    ```bash
    python main.py
    ```

## Building the package

To build the package, follow these steps:
```bash
poetry build
```

## Launch unit tests

To install the necessary dependencies for running unit tests with `unittest`, follow these steps:

Install the development dependencies:
    ```bash
    poetry install --with dev
    poetry run pre-commit install
    ```

Run the unit tests:
    ```bash
    python -m unittest discover tests
    ```

Or you can run the command
```bash
poetry run python -m wgm
```
