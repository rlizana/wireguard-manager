from wgm import runner


def generate():
    private_key = runner.run(['wg', 'genkey']).stdout
    public_key = runner.run(['wg', 'pubkey'], stdin=private_key + '\n').stdout
    return private_key, public_key
