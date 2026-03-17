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


def test_when_encoding_then_degree_within_valid_range():
    data = b"HelloWorld"
    block_size = 2
    enc = LtCodeEncode(data, block_size)

    k = compute_k_with_padding(data, block_size)
    assert 1 <= enc.degree <= k


def test_when_encoding_then_indices_count_matches_degree():
    data = b"HelloWorld"
    enc = LtCodeEncode(data, block_size=2)

    assert len(enc.indices) == enc.degree


def test_when_encoding_then_indices_are_within_valid_range():
    data = b"HelloWorld"
    block_size = 2
    enc = LtCodeEncode(data, block_size)

    k = compute_k_with_padding(data, block_size)

    for idx in enc.indices:
        assert 0 <= idx < k


def test_when_encoding_then_packet_is_bytes():
    data = b"HelloWorld"
    enc = LtCodeEncode(data, block_size=2)

    assert isinstance(enc.packet, bytes)


def test_when_single_small_block_then_degree_and_packet_reflect_it():
    data = b"A"
    block_size = 10

    with (
        patch("random.randint", return_value=1),
        patch("random.sample", return_value=[0]),
    ):
        enc = LtCodeEncode(data, block_size)

        expected = b"A" + bytes([9]) * 9  # PKCS padding

        assert enc.degree == 1
        assert enc.indices == [0]
        assert enc.packet == expected


def test_when_splitting_data_then_blocks_are_sized_correctly():
    data = b"ABCDEFGH"
    block_size = 2

    enc = LtCodeEncode(data, block_size)
    blocks = enc._split_blocks(data, block_size)

    assert blocks[:-1] == [b"AB", b"CD", b"EF", b"GH"]
    assert blocks[-1] == b"\x02\x02"


def test_when_xoring_blocks_then_packet_matches_manual_xor():
    data = b"\x01\x02\x03\x04"
    block_size = 1

    enc = LtCodeEncode(data, block_size)

    blocks = enc._split_blocks(data, block_size)

    # recompute manually
    result = blocks[enc.indices[0]]
    for i in enc.indices[1:]:
        result = bytes(x ^ y for x, y in zip(result, blocks[i]))

    assert enc.packet == result


def test_when_seeding_rng_then_encoding_is_deterministic():
    data = b"HelloWorld"

    random.seed(42)
    enc1 = LtCodeEncode(data, 2)

    random.seed(42)
    enc2 = LtCodeEncode(data, 2)

    assert enc1.degree == enc2.degree
    assert enc1.indices == enc2.indices
    assert enc1.packet == enc2.packet


def test_when_data_empty_then_encoding_raises_value_error():
    data = b""

    with pytest.raises(ValueError):
        LtCodeEncode(data, block_size=2)


def test_when_mocking_random_then_indices_order_is_respected():
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


def test_when_indices_order_forced_then_packet_respects_that_order():
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
