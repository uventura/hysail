from hysail.lt_code import LtCodeEncode

from unittest.mock import patch
import random
import pytest


def test_degree_range():
    data = b"HelloWorld"
    enc = LtCodeEncode(data, block_size=2)

    k = len(data) // 2 + (1 if len(data) % 2 else 0)
    assert 1 <= enc.degree <= k


def test_indices_match_degree():
    data = b"HelloWorld"
    enc = LtCodeEncode(data, block_size=2)

    assert len(enc.indices) == enc.degree


def test_indices_are_valid():
    data = b"HelloWorld"
    block_size = 2
    enc = LtCodeEncode(data, block_size)

    k = len(data) // block_size + (1 if len(data) % block_size else 0)

    for idx in enc.indices:
        assert 0 <= idx < k


def test_packet_is_bytes():
    data = b"HelloWorld"
    enc = LtCodeEncode(data, block_size=2)

    assert isinstance(enc.packet, bytes)


def test_single_block():
    data = b"A"
    enc = LtCodeEncode(data, block_size=10)

    assert enc.degree == 1
    assert enc.indices == [0]
    assert enc.packet == b"A"


def test_split_blocks():
    data = b"ABCDEFGH"
    enc = LtCodeEncode(data, block_size=2)

    blocks = enc._split_blocks(data, 2)
    assert blocks == [b"AB", b"CD", b"EF", b"GH"]


def test_xor_correctness():
    data = b"\x01\x02\x03\x04"
    block_size = 1

    enc = LtCodeEncode(data, block_size)

    blocks = enc._split_blocks(data, block_size)

    # recompute manually
    result = blocks[enc.indices[0]]
    for i in enc.indices[1:]:
        result = bytes(x ^ y for x, y in zip(result, blocks[i]))

    assert enc.packet == result


def test_deterministic_behavior():
    data = b"HelloWorld"

    random.seed(42)
    enc1 = LtCodeEncode(data, 2)

    random.seed(42)
    enc2 = LtCodeEncode(data, 2)

    assert enc1.degree == enc2.degree
    assert enc1.indices == enc2.indices
    assert enc1.packet == enc2.packet


def test_empty_data():
    data = b""

    with pytest.raises(ValueError):
        LtCodeEncode(data, block_size=2)


def test_indices_order_with_mock():
    data = b"ABCDEFGH"  # blocks: [AB, CD, EF, GH]
    block_size = 2

    # Force:
    # degree = 3
    # indices = [2, 0, 1] (specific order we want to test)
    with (
        patch("random.randint", return_value=3),
        patch("random.sample", return_value=[2, 0, 1]),
    ):
        enc = LtCodeEncode(data, block_size)

        assert enc.degree == 3
        assert enc.indices == [2, 0, 1]


def test_packet_respects_indices_order():
    data = b"ABCDEFGH"  # [AB, CD, EF, GH]
    block_size = 2

    with (
        patch("random.randint", return_value=3),
        patch("random.sample", return_value=[2, 0, 1]),
    ):
        enc = LtCodeEncode(data, block_size)

        blocks = [b"AB", b"CD", b"EF", b"GH"]

        expected = blocks[2]
        expected = bytes(x ^ y for x, y in zip(expected, blocks[0]))
        expected = bytes(x ^ y for x, y in zip(expected, blocks[1]))

        assert enc.packet == expected
