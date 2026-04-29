from types import SimpleNamespace

from hysail.chain.manifest import build_file_manifest


def test_build_file_manifest_generates_expected_fields():
    metadata = SimpleNamespace(
        original_filename="hello.txt",
        original_file_hash="a" * 64,
        packet_root_hash="b" * 64,
        packets=[
            SimpleNamespace(server="server-a"),
            SimpleNamespace(server="server-b"),
            SimpleNamespace(server="server-a"),
        ],
    )

    manifest = build_file_manifest(metadata, "http://127.0.0.1:8000/manifest")

    assert manifest["metadataUri"] == "http://127.0.0.1:8000/manifest"
    assert manifest["originalFilename"] == "hello.txt"
    assert manifest["originalFileHash"] == "a" * 64
    assert manifest["blockRoot"] == "b" * 64
    assert manifest["packetCount"] == 3
    assert manifest["servers"] == ["server-a", "server-b"]
    assert manifest["fileId"].startswith("hello.txt-")
