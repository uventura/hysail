from click.testing import CliRunner

from hysail.hysail import main
from hysail.tests.dummy import DummyHysailDecode, DummyHysailEncode


def test_when_cli_decode_runs_then_hysail_decode_is_invoked(tmp_path, monkeypatch):
    metadata_file = tmp_path / "payload_metadata.pkl"
    server_file = tmp_path / "servers.json"
    metadata_file.write_bytes(b"metadata")
    server_file.write_text('{"servers": []}')

    captured = {}

    DummyHysailDecode.captured = captured
    DummyHysailDecode.return_path = tmp_path / "payload_decoded.bin"

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


def test_when_cli_decode_receives_output_file_then_it_passes_the_path(
    tmp_path, monkeypatch
):
    metadata_file = tmp_path / "payload_metadata.pkl"
    server_file = tmp_path / "servers.json"
    output_file = tmp_path / "custom" / "result.bin"
    metadata_file.write_bytes(b"metadata")
    server_file.write_text('{"servers": []}')

    captured = {}

    DummyHysailDecode.captured = captured
    DummyHysailDecode.return_path = output_file

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


def test_when_cli_encode_runs_then_hysail_encode_is_invoked(tmp_path, monkeypatch):
    input_file = tmp_path / "payload.txt"
    server_list_file = tmp_path / "servers.json"
    input_file.write_bytes(b"payload")
    server_list_file.write_text(
        '{"servers": [{"id": 1, "storage_location": "server-1"}]}'
    )

    captured = {}

    DummyHysailEncode.captured = captured
    DummyHysailEncode.return_value = 7

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
    assert captured["metadata_output"] == "./"
    assert "Encoded 7 packets distributed to 1 servers" in result.output
