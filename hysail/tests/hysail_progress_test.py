from hysail.hysail_decode import HysailDecode
from hysail.logger.progress import advance_progress, create_progress_task
from hysail.tests.dummy import DummyDecode, DummyProgress


def test_when_progress_is_missing_then_create_progress_task_returns_none():
    assert create_progress_task(None, "Decoding file", total=3) is None


def test_when_progress_or_task_id_is_missing_then_advance_progress_does_nothing():
    captured = {"advances": 0}
    DummyProgress.captured = captured

    advance_progress(None, "task-id")
    advance_progress(DummyProgress(), None)

    assert captured["advances"] == 0


def test_when_progress_and_total_are_provided_then_create_progress_task_returns_id():
    captured = {}
    DummyProgress.captured = captured

    task_id = create_progress_task(DummyProgress(), "Decoding file", total=3)

    assert task_id == "task-id"
    assert captured["description"] == "Decoding file"
    assert captured["total"] == 3


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
