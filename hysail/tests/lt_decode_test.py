import pytest
import random

from hysail.lt_code import LtCodeEncode, LtCodeDecode, LtPacket


def generate_packets(data, block_size, n_packets=30):
    return [LtCodeEncode(data, block_size).packet for _ in range(n_packets)]


def compute_num_blocks(data, block_size):
    pad = block_size - (len(data) % block_size)
    if pad == 0:
        pad = block_size
    return (len(data) + pad) // block_size


def test_when_enough_packets_then_full_decode_succeeds():
    random.seed(42)

    data = b"ABCDEFGH"
    block_size = 2

    packets = generate_packets(data, block_size, 40)
    num_blocks = compute_num_blocks(data, block_size)

    dec = LtCodeDecode(packets, num_blocks)

    assert dec.is_decoded
    assert dec.data == data


def test_when_too_few_packets_then_decode_fails():
    random.seed(42)

    data = b"ABCDEFGH"
    block_size = 2

    packets = generate_packets(data, block_size, 2)
    num_blocks = compute_num_blocks(data, block_size)

    dec = LtCodeDecode(packets, num_blocks)

    assert not dec.is_decoded

    with pytest.raises(ValueError):
        _ = dec.data


def test_when_decoded_then_blocks_match_num_blocks():
    random.seed(42)

    data = b"ABCDEFGH"
    block_size = 2

    packets = generate_packets(data, block_size, 40)
    num_blocks = compute_num_blocks(data, block_size)

    dec = LtCodeDecode(packets, num_blocks)

    assert len(dec.blocks) == num_blocks

    if dec.is_decoded:
        for b in dec.blocks:
            assert isinstance(b, bytes)


def test_when_degree_one_packet_then_try_resolve_stores_block():
    dec = LtCodeDecode([], num_blocks=2)
    pkt = LtPacket(1, [0], b"Z")

    resolved = dec._try_resolve(pkt)

    assert resolved
    assert dec.blocks[0] == b"Z"
