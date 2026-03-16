import pytest

from hysail.lt_code import LtCodeEncode, LtCodeDecode


def generate_packets(data, block_size, n_packets=20):
    packets = []
    for _ in range(n_packets):
        enc = LtCodeEncode(data, block_size)
        packets.append(
            {
                "degree": enc.degree,
                "indices": enc.indices,
                "data": enc.packet,
            }
        )
    return packets


def test_full_decode_success():
    data = b"ABCDEFGH"
    block_size = 2

    packets = generate_packets(data, block_size, n_packets=30)

    k = len(data) // block_size
    dec = LtCodeDecode(packets, k)

    assert dec.is_decoded
    assert dec.data == data


def test_decode_incomplete():
    data = b"ABCDEFGH"
    block_size = 2

    # too few packets → likely failure
    packets = generate_packets(data, block_size, n_packets=2)

    k = len(data) // block_size
    dec = LtCodeDecode(packets, k)

    assert not dec.is_decoded

    with pytest.raises(ValueError):
        _ = dec.data


def test_blocks_structure():
    data = b"ABCDEFGH"
    block_size = 2

    packets = generate_packets(data, block_size, n_packets=30)

    k = len(data) // block_size
    dec = LtCodeDecode(packets, k)

    assert len(dec.blocks) == k

    if dec.is_decoded:
        for b in dec.blocks:
            assert isinstance(b, bytes)


def test_reduce_packet_behavior():
    dec = LtCodeDecode([], k=2)

    # manually set one known block
    dec._blocks[0] = b"A"

    pkt = {
        "degree": 2,
        "indices": [0, 1],
        "data": bytes([ord("A") ^ ord("B")]),
    }

    dec._reduce_packet(pkt)

    assert pkt["degree"] == 1
    assert pkt["indices"] == [1]
    assert pkt["data"] == b"B"


def test_try_resolve():
    dec = LtCodeDecode([], k=2)

    pkt = {
        "degree": 1,
        "indices": [0],
        "data": b"Z",
    }

    resolved = dec._try_resolve(pkt)

    assert resolved
    assert dec.blocks[0] == b"Z"


def test_normalize_packets_copy():
    packets = [{"degree": 1, "indices": [0], "data": b"A"}]

    dec = LtCodeDecode([], k=1)
    normalized = dec._normalize_packets(packets)

    # ensure deep-ish copy of indices
    assert normalized[0]["indices"] == packets[0]["indices"]
    assert normalized[0]["indices"] is not packets[0]["indices"]
