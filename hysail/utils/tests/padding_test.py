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
