import math
from pathlib import Path

from click.testing import CliRunner

from hysail.constant import DEFAULT_BLOCK_SIZE_PERCENTAGE
from hysail.hysail import main
from hysail.hysail_decode import HysailDecode
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
        def __init__(self, packets, input_path, server_list):
            captured["packets"] = packets
            captured["input_path"] = input_path
            captured["server_list"] = server_list

        def save(self):
            pass

        @property
        def packet_metadata(self):
            return []

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


def test_decode_writes_decoded_output_file(tmp_path, monkeypatch):
    metadata_file = tmp_path / "payload_metadata.pkl"
    server_file = tmp_path / "servers.json"
    metadata_file.write_bytes(b"metadata")
    server_file.write_text('{"servers": []}')

    class DummyDecode:
        def __init__(self, metadata_file_arg, server_file_arg):
            assert metadata_file_arg == str(metadata_file)
            assert server_file_arg == str(server_file)

        def decode(self):
            return b"decoded-content"

    monkeypatch.setattr("hysail.hysail_decode.Decode", DummyDecode)

    hysail_decode = HysailDecode(str(metadata_file), str(server_file))
    output_path = hysail_decode.decode()

    assert output_path == tmp_path / "payload_decoded.bin"
    assert output_path.read_bytes() == b"decoded-content"


def test_decode_uses_explicit_output_file_when_provided(tmp_path, monkeypatch):
    metadata_file = tmp_path / "payload_metadata.pkl"
    server_file = tmp_path / "servers.json"
    output_file = tmp_path / "custom" / "result.bin"
    metadata_file.write_bytes(b"metadata")
    server_file.write_text('{"servers": []}')

    class DummyDecode:
        def __init__(self, metadata_file_arg, server_file_arg):
            assert metadata_file_arg == str(metadata_file)
            assert server_file_arg == str(server_file)

        def decode(self):
            return b"custom-output"

    monkeypatch.setattr("hysail.hysail_decode.Decode", DummyDecode)

    hysail_decode = HysailDecode(str(metadata_file), str(server_file), str(output_file))
    output_path = hysail_decode.decode()

    assert output_path == output_file
    assert output_path.read_bytes() == b"custom-output"


def test_decode_uses_current_directory_when_output_file_is_dot_slash(
    tmp_path, monkeypatch
):
    metadata_file = tmp_path / "payload_metadata.pkl"
    server_file = tmp_path / "servers.json"
    metadata_file.write_bytes(b"metadata")
    server_file.write_text('{"servers": []}')

    class DummyDecode:
        def __init__(self, metadata_file_arg, server_file_arg):
            assert metadata_file_arg == str(metadata_file)
            assert server_file_arg == str(server_file)

        def decode(self):
            return b"decoded-content"

    monkeypatch.setattr("hysail.hysail_decode.Decode", DummyDecode)
    monkeypatch.chdir(tmp_path)

    hysail_decode = HysailDecode(str(metadata_file), str(server_file), "./")
    output_path = hysail_decode.decode()

    assert output_path == Path("payload_decoded.bin")
    assert output_path.read_bytes() == b"decoded-content"


def test_decode_advances_progress_bar_for_each_step(tmp_path, monkeypatch):
    metadata_file = tmp_path / "payload_metadata.pkl"
    server_file = tmp_path / "servers.json"
    metadata_file.write_bytes(b"metadata")
    server_file.write_text('{"servers": []}')

    captured = {"advances": 0}

    class DummyProgress:
        def add_task(self, description, total):
            captured["description"] = description
            captured["total"] = total
            return "task-id"

        def advance(self, task_id):
            assert task_id == "task-id"
            captured["advances"] += 1

    class DummyDecode:
        def __init__(self, metadata_file_arg, server_file_arg):
            assert metadata_file_arg == str(metadata_file)
            assert server_file_arg == str(server_file)

        def decode(self):
            return b"progress-output"

    monkeypatch.setattr("hysail.hysail_decode.Decode", DummyDecode)
    monkeypatch.setattr("hysail.hysail_decode.get_progress", lambda: DummyProgress())

    hysail_decode = HysailDecode(str(metadata_file), str(server_file))
    output_path = hysail_decode.decode()

    assert output_path.read_bytes() == b"progress-output"
    assert captured["description"] == "Decoding file"
    assert captured["total"] == 3
    assert captured["advances"] == 3


def test_cli_decode_invokes_hysail_decode(tmp_path, monkeypatch):
    metadata_file = tmp_path / "payload_metadata.pkl"
    server_file = tmp_path / "servers.json"
    metadata_file.write_bytes(b"metadata")
    server_file.write_text('{"servers": []}')

    captured = {}

    class DummyHysailDecode:
        def __init__(self, metadata_file_arg, server_file_arg, output_file_arg=None):
            captured["metadata_file"] = metadata_file_arg
            captured["server_file"] = server_file_arg
            captured["output_file"] = output_file_arg

        def decode(self):
            return tmp_path / "payload_decoded.bin"

    monkeypatch.setattr("hysail.hysail.HysailDecode", DummyHysailDecode)

    runner = CliRunner()
    result = runner.invoke(
        main,
        ["decode", str(metadata_file), "--server-file", str(server_file)],
    )

    assert result.exit_code == 0
    assert captured["metadata_file"] == str(metadata_file)
    assert captured["server_file"] == str(server_file)
    assert captured["output_file"] == "./"
    assert "Decoded file written to" in result.output


def test_cli_decode_passes_output_file_when_provided(tmp_path, monkeypatch):
    metadata_file = tmp_path / "payload_metadata.pkl"
    server_file = tmp_path / "servers.json"
    output_file = tmp_path / "custom" / "result.bin"
    metadata_file.write_bytes(b"metadata")
    server_file.write_text('{"servers": []}')

    captured = {}

    class DummyHysailDecode:
        def __init__(self, metadata_file_arg, server_file_arg, output_file_arg=None):
            captured["metadata_file"] = metadata_file_arg
            captured["server_file"] = server_file_arg
            captured["output_file"] = output_file_arg

        def decode(self):
            return output_file

    monkeypatch.setattr("hysail.hysail.HysailDecode", DummyHysailDecode)

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "decode",
            str(metadata_file),
            "--server-file",
            str(server_file),
            "--output-file",
            str(output_file),
        ],
    )

    assert result.exit_code == 0
    assert captured["metadata_file"] == str(metadata_file)
    assert captured["server_file"] == str(server_file)
    assert captured["output_file"] == str(output_file)
    assert "Decoded file written to" in result.output


def test_cli_encode_invokes_hysail_encode(tmp_path, monkeypatch):
    input_file = tmp_path / "payload.txt"
    server_list_file = tmp_path / "servers.json"
    input_file.write_bytes(b"payload")
    server_list_file.write_text(
        '{"servers": [{"id": 1, "storage_location": "server-1"}]}'
    )

    captured = {}

    class DummyHysailEncode:
        def __init__(self, input_file_arg, block_size_arg, server_list_arg):
            captured["input_file"] = input_file_arg
            captured["block_size"] = block_size_arg
            captured["server_list"] = server_list_arg

        def encode(self):
            return 7

    monkeypatch.setattr("hysail.hysail.HysailEncode", DummyHysailEncode)

    runner = CliRunner()
    result = runner.invoke(
        main,
        ["encode", str(input_file), "--server-list", str(server_list_file)],
    )

    assert result.exit_code == 0
    assert captured["input_file"] == str(input_file)
    assert captured["block_size"] is None
    assert captured["server_list"] == [{"id": 1, "storage_location": "server-1"}]
    assert "Encoded 7 packets distributed to 1 servers" in result.output
