import pytest

from hysail.lt_code import LtCodeEncode, LtCodeDecode, LtPacket


def generate_packets(data, block_size, num_packets=30):
    enc = LtCodeEncode(data, block_size, num_packets=num_packets)
    return enc.packets, enc.num_blocks


def test_when_enough_packets_then_full_decode_succeeds():
    data = b"ABCDEFGH"
    block_size = 2

    packets, num_blocks = generate_packets(data, block_size, num_packets=50)
    dec = LtCodeDecode(packets, num_blocks)

    assert dec.is_decoded
    assert dec.data == data


def test_when_too_few_packets_then_decode_fails():
    data = b"ABCDEFGH"
    block_size = 2

    packets, num_blocks = generate_packets(data, block_size, num_packets=2)
    dec = LtCodeDecode(packets, num_blocks)

    assert not dec.is_decoded
    with pytest.raises(ValueError):
        _ = dec.data


def test_when_decoded_then_blocks_match_expected():
    data = b"ABCDEFGH"
    block_size = 2

    packets, num_blocks = generate_packets(data, block_size, num_packets=50)
    dec = LtCodeDecode(packets, num_blocks)
    assert len(dec.blocks) == num_blocks

    if dec.is_decoded:
        for b in dec.blocks:
            assert isinstance(b, bytes)


def test_when_known_block_present_then_reduce_packet_simplifies():
    dec = LtCodeDecode([], num_blocks=2)
    dec._blocks[0] = b"A"

    pkt = (
        type(dec._packets).__args__[0]
        if hasattr(type(dec._packets), "__args__")
        else None
    )

    # reuse encoder to get a valid LtPacket
    enc = LtCodeEncode(b"AB", block_size=1, num_packets=1)
    pkt = enc.packets[0].copy()

    pkt.indices = [0, 1]
    pkt.degree = 2
    pkt.data = bytes([ord("A") ^ ord("B")])

    dec._reduce_packet(pkt)

    assert pkt.degree == 1
    assert pkt.indices == [1]
    assert pkt.data == b"B"


def test_when_degree_one_packet_then_try_resolve_stores_block():
    dec = LtCodeDecode([], num_blocks=2)

    enc = LtCodeEncode(b"A", block_size=1, num_packets=1)
    pkt = enc.packets[0].copy()

    pkt.indices = [0]
    pkt.degree = 1
    pkt.data = b"Z"

    resolved = dec._try_resolve(pkt)

    assert resolved
    assert dec.blocks[0] == b"Z"


def test_when_padding_present_then_data_is_stripped_correctly():
    data = b"ABC"
    block_size = 2

    packets, num_blocks = generate_packets(data, block_size, num_packets=50)

    dec = LtCodeDecode(packets, num_blocks)

    assert dec.is_decoded
    assert dec.data == data


def test_when_no_padding_removal_then_raw_data_contains_padding():
    data = b"ABC"
    block_size = 2

    packets, num_blocks = generate_packets(data, block_size, num_packets=50)

    dec = LtCodeDecode(packets, num_blocks, remove_padding=False)

    assert dec.is_decoded

    raw = b"".join(dec.blocks)

    assert raw.startswith(data)
    assert len(raw) > len(data)


def test_when_no_packets_then_decode_not_complete():
    dec = LtCodeDecode([], num_blocks=3)
    assert not dec.is_decoded

    with pytest.raises(ValueError):
        _ = dec.data


def test_when_duplicate_packets_then_decoder_still_works():
    data = b"ABCDEFGH"
    block_size = 2

    packets, num_blocks = generate_packets(data, block_size, num_packets=10)
    packets = packets + packets

    dec = LtCodeDecode(packets, num_blocks)

    assert dec.is_decoded
    assert dec.data == data
