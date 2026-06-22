from pathlib import Path

from hysail.utils.padding import add_padding, remove_padding


def test_when_padding_short_payload_then_add_padding_fills_remaining_block_space():
    assert add_padding(b"A", 4) == b"A\x03\x03\x03"


def test_when_payload_matches_block_size_then_add_padding_adds_full_block():
    assert add_padding(b"DATA", 4) == b"DATA\x04\x04\x04\x04"


def test_when_padding_is_valid_then_remove_padding_returns_original_payload():
    assert remove_padding(b"DATA\x04\x04\x04\x04") == b"DATA"


def test_when_padding_is_invalid_then_remove_padding_keeps_data_unchanged():
    assert remove_padding(b"AB") == b"AB"
    assert remove_padding(b"DATA\x04\x04\x04\x03") == b"DATA\x04\x04\x04\x03"


def test_bad_apple_padding_round_trip_returns_original_bytes():
    root = Path(__file__).resolve().parents[3]
    bad_apple_path = root / "examples" / "bad_apple.mp4"
    original = bad_apple_path.read_bytes()

    block_size = 1024
    padded = add_padding(original, block_size)

    assert len(padded) % block_size == 0
    assert remove_padding(padded) == original


def test_when_block_size_is_greater_than_255_then_add_and_remove_padding_work():
    payload = b"hy" * 257
    block_size = 512

    padded = add_padding(payload, block_size)

    assert len(padded) % block_size == 0
    assert remove_padding(padded) == payload
