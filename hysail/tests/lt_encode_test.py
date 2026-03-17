from hysail.lt_code import LtCodeEncode

from unittest.mock import patch
import random
import pytest


def compute_num_blocks(data, block_size):
    pad = block_size - (len(data) % block_size)
    if pad == 0:
        pad = block_size
    return (len(data) + pad) // block_size


def test_when_encoding_then_correct_number_of_packets_generated():
    data = b"HelloWorld"

    enc = LtCodeEncode(data, block_size=2, num_packets=5)

    assert len(enc.packets) == 5


def test_when_encoding_then_degree_within_valid_range():
    data = b"HelloWorld"
    block_size = 2

    enc = LtCodeEncode(data, block_size, num_packets=10)
    num_blocks = compute_num_blocks(data, block_size)

    for pkt in enc.packets:
        assert 1 <= pkt.degree <= num_blocks


def test_when_encoding_then_indices_count_matches_degree():
    data = b"HelloWorld"

    enc = LtCodeEncode(data, 2, num_packets=10)

    for pkt in enc.packets:
        assert len(pkt.indices) == pkt.degree


def test_when_encoding_then_indices_are_within_valid_range():
    data = b"HelloWorld"
    block_size = 2

    enc = LtCodeEncode(data, block_size, num_packets=10)
    num_blocks = compute_num_blocks(data, block_size)

    for pkt in enc.packets:
        for idx in pkt.indices:
            assert 0 <= idx < num_blocks


def test_when_encoding_then_packet_data_is_bytes():
    data = b"HelloWorld"

    enc = LtCodeEncode(data, 2, num_packets=5)

    for pkt in enc.packets:
        assert isinstance(pkt.data, bytes)


def test_when_single_small_block_then_packet_reflects_padding():
    data = b"A"
    block_size = 10

    with (
        patch("random.randint", return_value=1),
        patch("random.sample", return_value=[0]),
    ):
        enc = LtCodeEncode(data, block_size, num_packets=1)
        pkt = enc.packets[0]

        expected = b"A" + bytes([9]) * 9

        assert pkt.degree == 1
        assert pkt.indices == [0]
        assert pkt.data == expected


def test_when_splitting_data_then_blocks_include_padding():
    data = b"ABCDEFGH"
    block_size = 2

    enc = LtCodeEncode(data, block_size, num_packets=1)

    blocks = enc._blocks

    assert blocks[:-1] == [b"AB", b"CD", b"EF", b"GH"]
    assert blocks[-1] == b"\x02\x02"


def test_when_xoring_blocks_then_packet_matches_manual_xor():
    data = b"\x01\x02\x03\x04"
    block_size = 1

    enc = LtCodeEncode(data, block_size, num_packets=1)
    pkt = enc.packets[0]

    blocks = enc._blocks

    result = blocks[pkt.indices[0]]
    for i in pkt.indices[1:]:
        result = bytes(x ^ y for x, y in zip(result, blocks[i]))

    assert pkt.data == result


def test_when_seeding_rng_then_encoding_is_deterministic():
    data = b"HelloWorld"

    random.seed(42)
    enc1 = LtCodeEncode(data, 2, num_packets=5)

    random.seed(42)
    enc2 = LtCodeEncode(data, 2, num_packets=5)

    for p1, p2 in zip(enc1.packets, enc2.packets):
        assert p1.degree == p2.degree
        assert p1.indices == p2.indices
        assert p1.data == p2.data


def test_when_data_empty_then_encoding_raises_value_error():
    with pytest.raises(ValueError):
        LtCodeEncode(b"", block_size=2, num_packets=1)


def test_when_invalid_num_packets_then_raises():
    with pytest.raises(ValueError):
        LtCodeEncode(b"Hello", block_size=2, num_packets=0)


def test_when_mocking_random_then_indices_order_is_respected():
    data = b"ABCDEFGH"
    block_size = 2

    with (
        patch("random.randint", return_value=3),
        patch("random.sample", return_value=[2, 0, 1]),
    ):
        enc = LtCodeEncode(data, block_size, num_packets=1)
        pkt = enc.packets[0]

        assert pkt.degree == 3
        assert pkt.indices == [2, 0, 1]


def test_when_indices_order_forced_then_packet_respects_that_order():
    data = b"ABCDEFGH"
    block_size = 2

    with (
        patch("random.randint", return_value=3),
        patch("random.sample", return_value=[2, 0, 1]),
    ):
        enc = LtCodeEncode(data, block_size, num_packets=1)
        pkt = enc.packets[0]

        blocks = enc._blocks

        expected = blocks[2]
        expected = bytes(x ^ y for x, y in zip(expected, blocks[0]))
        expected = bytes(x ^ y for x, y in zip(expected, blocks[1]))

        assert pkt.data == expected
