import json
from types import SimpleNamespace

from click.testing import CliRunner

from hysail.hysail import main
from hysail.tests.dummy import (
    DummyHysailChainPublisher,
    DummyHysailDecode,
    DummyHysailEncode,
)


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


def test_when_cli_publish_runs_then_manifest_is_sent_to_chain(tmp_path, monkeypatch):
    metadata_file = tmp_path / "payload_metadata.pkl"
    deployment_file = tmp_path / "deployments.json"
    metadata_file.write_bytes(b"unused")
    deployment_file.write_text(
        json.dumps({"fileRegistry": "0x1234567890123456789012345678901234567890"})
    )

    captured = {}
    DummyHysailChainPublisher.captured = captured
    DummyHysailChainPublisher.return_value = {
        "fileId": "payload.txt-deadbeefcafe",
        "contractAddress": "0x1234567890123456789012345678901234567890",
        "transactionHash": "0xabc",
    }

    monkeypatch.setattr("hysail.hysail.HysailChainPublisher", DummyHysailChainPublisher)
    monkeypatch.setattr(
        "hysail.hysail.EncodingMetadata.load",
        lambda _: SimpleNamespace(
            original_filename="payload.txt",
            original_file_hash="a" * 64,
            packet_root_hash="b" * 64,
            packets=[SimpleNamespace(server="server-1")],
        ),
    )

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "publish",
            str(metadata_file),
            "--metadata-uri",
            "http://127.0.0.1:8000/manifest",
            "--deployment-file",
            str(deployment_file),
            "--private-key",
            "0xfeed",
        ],
    )

    assert result.exit_code == 0
    assert captured["rpc_url"] == "http://127.0.0.1:8545"
    assert captured["contract_address"] == "0x1234567890123456789012345678901234567890"
    assert captured["private_key"] == "0xfeed"
    assert captured["manifest"]["metadataUri"] == "http://127.0.0.1:8000/manifest"
    assert captured["manifest"]["originalFilename"] == "payload.txt"
    assert (tmp_path / "payload_metadata_chain_manifest.json").exists()
    assert "Published file" in result.output
