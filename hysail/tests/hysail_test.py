import math
from pathlib import Path

from hysail.constant import DEFAULT_BLOCK_SIZE_PERCENTAGE
from hysail.hysail_decode import HysailDecode
from hysail.hysail_encode import HysailEncode
from hysail.tests.dummy import (
    DummyDecode,
    DummyEncode,
    DummySaver,
)


def test_when_block_size_is_missing_then_encode_uses_percentage_fallback(
    tmp_path, monkeypatch
):
    file_path = tmp_path / "payload.txt"
    data = b"a" * 100
    file_path.write_bytes(data)

    captured = {}

    DummyEncode.captured = captured
    DummySaver.captured = captured

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


def test_when_decoding_without_output_override_then_decoded_file_is_written(
    tmp_path, monkeypatch
):
    metadata_file = tmp_path / "payload_metadata.pkl"
    server_file = tmp_path / "servers.json"
    metadata_file.write_bytes(b"metadata")
    server_file.write_text('{"servers": []}')

    DummyDecode.expected_metadata_file = str(metadata_file)
    DummyDecode.expected_server_file = str(server_file)
    DummyDecode.decoded_data = b"decoded-content"

    monkeypatch.setattr("hysail.hysail_decode.Decode", DummyDecode)

    hysail_decode = HysailDecode(str(metadata_file), str(server_file))
    output_path = hysail_decode.decode()

    assert output_path == tmp_path / "payload_decoded.bin"
    assert output_path.read_bytes() == b"decoded-content"


def test_when_output_file_is_provided_then_decode_writes_to_explicit_path(
    tmp_path, monkeypatch
):
    metadata_file = tmp_path / "payload_metadata.pkl"
    server_file = tmp_path / "servers.json"
    output_file = tmp_path / "custom" / "result.bin"
    metadata_file.write_bytes(b"metadata")
    server_file.write_text('{"servers": []}')

    DummyDecode.expected_metadata_file = str(metadata_file)
    DummyDecode.expected_server_file = str(server_file)
    DummyDecode.decoded_data = b"custom-output"

    monkeypatch.setattr("hysail.hysail_decode.Decode", DummyDecode)

    hysail_decode = HysailDecode(str(metadata_file), str(server_file), str(output_file))
    output_path = hysail_decode.decode()

    assert output_path == output_file
    assert output_path.read_bytes() == b"custom-output"


def test_when_output_file_is_dot_slash_then_decode_writes_to_current_directory(
    tmp_path, monkeypatch
):
    metadata_file = tmp_path / "payload_metadata.pkl"
    server_file = tmp_path / "servers.json"
    metadata_file.write_bytes(b"metadata")
    server_file.write_text('{"servers": []}')

    DummyDecode.expected_metadata_file = str(metadata_file)
    DummyDecode.expected_server_file = str(server_file)
    DummyDecode.decoded_data = b"decoded-content"

    monkeypatch.setattr("hysail.hysail_decode.Decode", DummyDecode)
    monkeypatch.chdir(tmp_path)

    hysail_decode = HysailDecode(str(metadata_file), str(server_file), "./")
    output_path = hysail_decode.decode()

    assert output_path == Path("payload_decoded.bin")
    assert output_path.read_bytes() == b"decoded-content"
