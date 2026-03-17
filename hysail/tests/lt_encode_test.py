from hysail.lt_code import LtCodeEncode

from unittest.mock import patch
import random
import pytest


def compute_k_with_padding(data, block_size):
    padding = block_size - (len(data) % block_size)
    if padding == 0:
        padding = block_size
    padded_len = len(data) + padding
    return padded_len // block_size


def compute_num_blocks(data, block_size):
    pad = block_size - (len(data) % block_size)
    if pad == 0:
        pad = block_size
    return (len(data) + pad) // block_size


def test_when_encoding_then_degree_within_valid_range():
    data = b"HelloWorld"
    block_size = 2

    enc = LtCodeEncode(data, block_size)
    pkt = enc.packet
    num_blocks = compute_num_blocks(data, block_size)

    assert 1 <= pkt.degree <= num_blocks


def test_when_encoding_then_indices_count_matches_degree():
    data = b"HelloWorld"
    pkt = LtCodeEncode(data, 2).packet

    assert len(pkt.indices) == pkt.degree


def test_when_encoding_then_indices_are_within_valid_range():
    data = b"HelloWorld"
    block_size = 2

    enc = LtCodeEncode(data, block_size)
    pkt = enc.packet

    num_blocks = compute_num_blocks(data, block_size)
    for idx in pkt.indices:
        assert 0 <= idx < num_blocks


def test_when_encoding_then_packet_is_bytes():
    data = b"HelloWorld"

    pkt = LtCodeEncode(data, 2).packet
    assert isinstance(pkt.data, bytes)


def test_when_single_small_block_then_packet_reflects_padding():
    data = b"A"
    block_size = 10

    with (
        patch("random.randint", return_value=1),
        patch("random.sample", return_value=[0]),
    ):
        pkt = LtCodeEncode(data, block_size).packet

        expected = b"A" + bytes([9]) * 9

        assert pkt.degree == 1
        assert pkt.indices == [0]
        assert pkt.data == expected


def test_when_splitting_data_then_blocks_include_padding():
    data = b"ABCDEFGH"
    block_size = 2

    enc = LtCodeEncode(data, block_size)
    blocks = enc._split_blocks(enc._data, block_size)

    assert blocks[:-1] == [b"AB", b"CD", b"EF", b"GH"]
    assert blocks[-1] == b"\x02\x02"


def test_when_xoring_blocks_then_packet_matches_manual_xor():
    data = b"\x01\x02\x03\x04"
    block_size = 1

    enc = LtCodeEncode(data, block_size)
    pkt = enc.packet

    blocks = enc._blocks
    result = blocks[pkt.indices[0]]

    for i in pkt.indices[1:]:
        result = bytes(x ^ y for x, y in zip(result, blocks[i]))

    assert pkt.data == result


def test_when_seeding_rng_then_encoding_is_deterministic():
    data = b"HelloWorld"

    random.seed(42)
    pkt1 = LtCodeEncode(data, 2).packet

    random.seed(42)
    pkt2 = LtCodeEncode(data, 2).packet

    assert pkt1.degree == pkt2.degree
    assert pkt1.indices == pkt2.indices
    assert pkt1.data == pkt2.data


def test_when_data_empty_then_encoding_raises_value_error():
    with pytest.raises(ValueError):
        LtCodeEncode(b"", block_size=2)


def test_when_mocking_random_then_indices_order_is_respected():
    data = b"ABCDEFGH"
    block_size = 2

    with (
        patch("random.randint", return_value=3),
        patch("random.sample", return_value=[2, 0, 1]),
    ):
        pkt = LtCodeEncode(data, block_size).packet

        assert pkt.degree == 3
        assert pkt.indices == [2, 0, 1]


def test_when_indices_order_forced_then_packet_respects_that_order():
    data = b"ABCDEFGH"
    block_size = 2

    with (
        patch("random.randint", return_value=3),
        patch("random.sample", return_value=[2, 0, 1]),
    ):
        enc = LtCodeEncode(data, block_size)
        pkt = enc.packet

        blocks = enc._blocks

        expected = blocks[2]
        expected = bytes(x ^ y for x, y in zip(expected, blocks[0]))
        expected = bytes(x ^ y for x, y in zip(expected, blocks[1]))

        assert pkt.data == expected
