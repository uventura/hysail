import math

from hysail.constant import DEFAULT_BLOCK_SIZE_PERCENTAGE
from hysail.hysail_encode import HysailEncode


def test_encode_uses_block_size_percentage_for_fallback(tmp_path, monkeypatch):
    file_path = tmp_path / "payload.txt"
    data = b"a" * 100
    file_path.write_bytes(data)

    captured = {}

    class DummyEncode:
        def __init__(self, data_arg, block_size_arg):
            captured["data"] = data_arg
            captured["block_size"] = block_size_arg
            self.packets = []
            self.mac_blocks = {}
            self.polynomials = []

    class DummySaver:
        def __init__(self, packets, input_path, server_list, metadata=None):
            captured["packets"] = packets
            captured["input_path"] = input_path
            captured["server_list"] = server_list
            captured["metadata"] = metadata

        def save(self):
            pass

    monkeypatch.setattr("hysail.hysail_encode.Encode", DummyEncode)
    monkeypatch.setattr("hysail.hysail_encode.PacketSaver", DummySaver)

    server_list = [{"id": 1, "storage_location": str(tmp_path / "server1")}]
    hysail_encode = HysailEncode(str(file_path), None, server_list)
    packet_count = hysail_encode.encode()

    expected_block_size = max(1, math.ceil(len(data) * DEFAULT_BLOCK_SIZE_PERCENTAGE))
    assert captured["block_size"] == expected_block_size
    assert captured["data"] == data
    assert packet_count == 0
    assert captured["server_list"] == server_list
