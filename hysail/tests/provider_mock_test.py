import json
import pickle
from contextlib import contextmanager
from pathlib import Path
from threading import Thread
from urllib.request import Request, urlopen

from http.server import ThreadingHTTPServer

import pytest

from dapp.services.provider_mock.provider_mock import (
    ProviderMockConfig,
    ProviderMockServer,
)
from hysail.encryption.encode import Encode


@contextmanager
def running_provider_servers(provider_server: ProviderMockServer):
    servers = [
        ThreadingHTTPServer(
            (state.host, state.port),
            provider_server._create_handler(state),
        )
        for state in provider_server.providers
    ]
    threads = [Thread(target=server.serve_forever, daemon=True) for server in servers]

    try:
        for thread in threads:
            thread.start()
        yield provider_server.providers
    finally:
        for server in servers:
            server.shutdown()
            server.server_close()


def upload_block(endpoint: str, block_id: str, payload: bytes):
    request = Request(
        f"{endpoint}/blocks/{block_id}",
        data=payload,
        method="POST",
    )
    with urlopen(request) as response:
        return response.status


def download_block(endpoint: str, block_id: str) -> bytes:
    with urlopen(f"{endpoint}/blocks/{block_id}") as response:
        return response.read()


def test_when_server_count_is_zero_then_provider_mock_raises_value_error(tmp_path):
    manifest_path = tmp_path / "manifest.json"
    block_path = tmp_path / "block.bin"
    manifest_path.write_text(
        json.dumps({"blockId": "block-a", "packets": []}),
        encoding="utf-8",
    )
    block_path.write_bytes(b"block-data")

    with pytest.raises(ValueError, match="server_count must be at least 1"):
        ProviderMockServer(
            config=ProviderMockConfig(
                manifest_path=manifest_path,
                block_path=block_path,
                server_count=0,
            )
        )


def test_when_server_count_is_set_then_provider_mock_generates_n_servers(tmp_path):
    manifest_path = tmp_path / "manifest.json"
    block_path = tmp_path / "block.bin"
    manifest_path.write_text(
        json.dumps(
            {
                "blockId": "block-a",
                "providerEndpoint": "http://127.0.0.1:9100",
                "packets": [],
            }
        ),
        encoding="utf-8",
    )
    block_path.write_bytes(b"block-data")

    server = ProviderMockServer(
        config=ProviderMockConfig(
            manifest_path=manifest_path,
            block_path=block_path,
            server_count=3,
        )
    )

    assert len(server.providers) == 3
    assert [state.endpoint for state in server.providers] == [
        "http://127.0.0.1:9100",
        "http://127.0.0.1:9101",
        "http://127.0.0.1:9102",
    ]
    assert all(
        state.block_bytes == {"block-a": b"block-data"} for state in server.providers
    )


def test_when_server_count_is_set_with_packets_then_each_server_has_all_blocks(
    tmp_path,
):
    packet_0 = tmp_path / "packet_0.pkl"
    packet_1 = tmp_path / "packet_1.pkl"
    block_path = tmp_path / "unused_block.bin"
    manifest_path = tmp_path / "manifest.json"

    with open(packet_0, "wb") as file:
        pickle.dump(b"block-0", file)
    with open(packet_1, "wb") as file:
        pickle.dump(b"block-1", file)

    manifest_path.write_text(
        json.dumps(
            {
                "providerEndpoint": "http://127.0.0.1:9200",
                "packets": [
                    {
                        "packetIndex": 0,
                        "blockId": "block-0",
                        "providerEndpoint": "http://127.0.0.1:8000",
                        "blockPath": str(packet_0),
                    },
                    {
                        "packetIndex": 1,
                        "blockId": "block-1",
                        "providerEndpoint": "http://127.0.0.1:8001",
                        "blockPath": str(packet_1),
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    block_path.write_bytes(b"unused")

    server = ProviderMockServer(
        config=ProviderMockConfig(
            manifest_path=manifest_path,
            block_path=block_path,
            server_count=2,
        )
    )

    assert len(server.providers) == 2
    assert [state.endpoint for state in server.providers] == [
        "http://127.0.0.1:9200",
        "http://127.0.0.1:9201",
    ]
    assert all(
        state.block_bytes == {"block-0": b"block-0", "block-1": b"block-1"}
        for state in server.providers
    )


def test_when_uploading_encoded_bad_apple_packets_then_three_provider_mock_servers_store_them(
    tmp_path,
):
    repo_root = Path(__file__).resolve().parents[2]
    sample_file = repo_root / "examples" / "bad_apple.mp4"
    manifest_path = tmp_path / "manifest.json"
    block_path = tmp_path / "fallback.bin"

    with open(sample_file, "rb") as file:
        data = file.read(20 * 1024)

    encoded = Encode(data, 4096)
    packets = encoded.packets[:3]

    manifest_path.write_text(
        json.dumps(
            {
                "blockId": "fallback-block",
                "providerEndpoint": "http://127.0.0.1:9300",
                "packets": [],
            }
        ),
        encoding="utf-8",
    )
    block_path.write_bytes(b"fallback")

    provider_server = ProviderMockServer(
        config=ProviderMockConfig(
            manifest_path=manifest_path,
            block_path=block_path,
            server_count=3,
        )
    )

    with running_provider_servers(provider_server) as providers:
        for packet, provider in zip(packets, providers):
            block_id = f"packet-{packet.index}"
            status = upload_block(provider.endpoint, block_id, packet.data)

            assert status == 201
            assert download_block(provider.endpoint, block_id) == packet.data

    assert [state.endpoint for state in provider_server.providers] == [
        "http://127.0.0.1:9300",
        "http://127.0.0.1:9301",
        "http://127.0.0.1:9302",
    ]
    assert [
        provider_server.providers[index].block_bytes[f"packet-{packet.index}"]
        for index, packet in enumerate(packets)
    ] == [packet.data for packet in packets]
