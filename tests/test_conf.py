from wgm.conf import Conf


def test_round_trip():
    text = (
        '# global comment\n'
        '\n'
        '[Interface]\n'
        '# inner comment\n'
        'PrivateKey = abc\n'
        'Address = 1.2.3.1/24\n'
        'PostUp = iptables -A FORWARD\n'
        '\n'
        '[Peer]\n'
        'PublicKey = xyz\n'
        'AllowedIPs = 1.2.3.2/32\n'
    )
    assert Conf.parse(text).render() == text


def test_repeated_keys():
    text = '[Interface]\nPostUp = a\nPostUp = b\n'
    conf = Conf.parse(text)
    assert conf.section('Interface').values('PostUp') == ['a', 'b']
    assert conf.render() == text


def test_set_updates_existing():
    conf = Conf.parse('[Interface]\nAddress = 1.2.3.1\n')
    conf.section('Interface').set('Address', '1.2.3.9')
    assert conf.render() == '[Interface]\nAddress = 1.2.3.9\n'


def test_add_and_remove_peer():
    text = (
        '[Interface]\n'
        'Address = 1.2.3.1\n'
        '\n'
        '[Peer]\n'
        'PublicKey = abc\n'
        '\n'
        '[Peer]\n'
        'PublicKey = def\n'
    )
    conf = Conf.parse(text)
    peers = conf.sections('Peer')
    assert [peer.get('PublicKey') for peer in peers] == ['abc', 'def']
    conf.remove(peers[0])
    assert [peer.get('PublicKey') for peer in conf.sections('Peer')] == ['def']
    assert 'abc' not in conf.render()
    assert 'PostUp' not in conf.render()
    conf.add_section('Peer').set('PublicKey', 'ghi')
    assert conf.sections('Peer')[-1].get('PublicKey') == 'ghi'


def test_missing_section():
    conf = Conf.parse('[Interface]\nAddress = 1.2.3.1\n')
    assert conf.section('Peer') is None
    assert conf.section('Interface').get('ListenPort', '51820') == '51820'
