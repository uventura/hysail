from hysail.hysail_decode import HysailDecode
from hysail.tests.dummy import DummyDecode, DummyProgress


def test_when_decoding_runs_then_progress_bar_advances_for_each_step(
    tmp_path, monkeypatch
):
    metadata_file = tmp_path / "payload_metadata.pkl"
    server_file = tmp_path / "servers.json"
    metadata_file.write_bytes(b"metadata")
    server_file.write_text('{"servers": []}')

    captured = {"advances": 0}

    DummyProgress.captured = captured
    DummyDecode.expected_metadata_file = str(metadata_file)
    DummyDecode.expected_server_file = str(server_file)
    DummyDecode.decoded_data = b"progress-output"

    monkeypatch.setattr("hysail.hysail_decode.Decode", DummyDecode)
    monkeypatch.setattr("hysail.hysail_decode.get_progress", lambda: DummyProgress())

    hysail_decode = HysailDecode(str(metadata_file), str(server_file))
    output_path = hysail_decode.decode()

    assert output_path.read_bytes() == b"progress-output"
    assert captured["description"] == "Decoding file"
    assert captured["total"] == 3
    assert captured["advances"] == 3
