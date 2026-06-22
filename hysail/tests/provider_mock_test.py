import json
import pickle

import pytest

from dapp.services.provider_mock.provider_mock import (
    ProviderMockConfig,
    ProviderMockServer,
)


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
