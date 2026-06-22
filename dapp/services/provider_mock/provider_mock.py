from __future__ import annotations

import json
import pickle
import copy
from dataclasses import dataclass
from threading import Event, Thread
from urllib.parse import urlparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import numpy as np

from hysail.logger.logger import execution_logger
from hysail.utils.galois import bytes_to_poly_coeffs, gf2_poly_mod

BASE_DIR = Path(__file__).resolve().parents[2]
SHARED_EXAMPLE_DIR = BASE_DIR / "packages" / "shared" / "example"
MANIFEST_PATH = SHARED_EXAMPLE_DIR / "sample_manifest.json"
BLOCK_PATH = SHARED_EXAMPLE_DIR / "sample_block.txt"


@dataclass
class ProviderMockConfig:
    manifest_path: Path = MANIFEST_PATH
    block_path: Path = BLOCK_PATH
    server_count: int | None = None


@dataclass
class ProviderState:
    endpoint: str
    host: str
    port: int
    block_bytes: dict[str, bytes]


class ProviderMockServer:
    def __init__(self, config: ProviderMockConfig | None = None):
        self.config = config or ProviderMockConfig()
        if self.config.server_count is not None and self.config.server_count < 1:
            raise ValueError("server_count must be at least 1")
        self.manifest = json.loads(
            self.config.manifest_path.read_text(encoding="utf-8")
        )
        self.providers = self._build_provider_states()

    def serve_forever(self) -> None:
        servers = []
        for state in self.providers:
            server = ThreadingHTTPServer(
                (state.host, state.port), self._create_handler(state)
            )
            servers.append(server)

        for state in self.providers:
            execution_logger.info(f"Provider mock listening on {state.endpoint}")

        stop_event = Event()
        threads = [
            Thread(target=server.serve_forever, daemon=True) for server in servers
        ]

        try:
            for thread in threads:
                thread.start()
            stop_event.wait()
        except KeyboardInterrupt:
            execution_logger.info("Stopping provider mock servers")
        finally:
            for server in servers:
                server.shutdown()
                server.server_close()

    def _build_provider_states(self) -> list[ProviderState]:
        packets = self.manifest.get("packets", [])
        fallback_endpoint = self._fallback_endpoint()

        if not packets:
            default_states = [self._build_single_fallback_state(fallback_endpoint)]
            return self._apply_server_count(default_states, fallback_endpoint)

        packet_blocks = self._load_packet_blocks(packets)
        states_by_endpoint: dict[str, ProviderState] = {}
        for packet in packets:
            endpoint = packet.get("providerEndpoint") or fallback_endpoint
            parsed = urlparse(endpoint)
            host = parsed.hostname or "127.0.0.1"
            port = parsed.port or 8000

            if endpoint not in states_by_endpoint:
                states_by_endpoint[endpoint] = ProviderState(
                    endpoint=endpoint,
                    host=host,
                    port=port,
                    block_bytes={},
                )

            block_id = packet["blockId"]
            if block_id in packet_blocks:
                states_by_endpoint[endpoint].block_bytes[block_id] = packet_blocks[
                    block_id
                ]

        return self._apply_server_count(
            list(states_by_endpoint.values()),
            fallback_endpoint,
        )

    def _build_single_fallback_state(self, endpoint: str) -> ProviderState:
        parsed = urlparse(endpoint)
        block_id = self.manifest.get("blockId", "block_0")
        return ProviderState(
            endpoint=endpoint,
            host=parsed.hostname or "127.0.0.1",
            port=parsed.port or 8000,
            block_bytes={
                block_id: self.config.block_path.read_bytes(),
            },
        )

    def _apply_server_count(
        self,
        states: list[ProviderState],
        fallback_endpoint: str,
    ) -> list[ProviderState]:
        if self.config.server_count is None:
            return states

        if not states:
            states = [self._build_single_fallback_state(fallback_endpoint)]

        base_endpoint = (
            self.manifest.get("providerEndpoint")
            or states[0].endpoint
            or fallback_endpoint
        )
        parsed = urlparse(base_endpoint)
        host = parsed.hostname or states[0].host
        start_port = parsed.port or states[0].port

        all_blocks: dict[str, bytes] = {}
        for state in states:
            all_blocks.update(state.block_bytes)

        generated_states: list[ProviderState] = []
        for offset in range(self.config.server_count):
            port = start_port + offset
            endpoint = f"http://{host}:{port}"
            generated_states.append(
                ProviderState(
                    endpoint=endpoint,
                    host=host,
                    port=port,
                    block_bytes=copy.deepcopy(all_blocks),
                )
            )

        return generated_states

    def _fallback_endpoint(self) -> str:
        endpoint = self.manifest.get("providerEndpoint")
        if endpoint:
            return endpoint
        return "http://127.0.0.1:8000"

    def _load_packet_blocks(self, packets: list[dict]) -> dict[str, bytes]:
        blocks: dict[str, bytes] = {}
        for packet in packets:
            packet_index = packet["packetIndex"]
            block_path = self._resolve_packet_path(packet, packet_index)
            if block_path is None:
                continue

            with open(block_path, "rb") as file:
                payload = pickle.load(file)

            block_data = payload.data if hasattr(payload, "data") else payload
            blocks[packet["blockId"]] = block_data

        return blocks

    def _resolve_packet_path(self, packet: dict, packet_index: int) -> Path | None:
        storage_location = packet.get("server")
        original_name = self.manifest.get("originalFilename")
        if storage_location and original_name:
            stem = Path(original_name).stem
            packet_path = Path(storage_location) / f"{stem}_packet_{packet_index}.pkl"
            if packet_path.exists():
                return packet_path

        custom_block_path = packet.get("blockPath")
        if custom_block_path:
            packet_path = Path(custom_block_path)
            if packet_path.exists():
                return packet_path

        return None

    def _create_handler(self, state: ProviderState):
        manifest = self.manifest
        block_bytes = state.block_bytes

        class ProviderHandler(BaseHTTPRequestHandler):
            def _read_json(self) -> dict:
                length = int(self.headers.get("Content-Length", "0"))
                raw_body = self.rfile.read(length) if length else b"{}"
                return json.loads(raw_body.decode() or "{}")

            def _send_json(self, payload: dict, status: int = 200) -> None:
                body = json.dumps(payload, indent=2).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def _send_bytes(
                self,
                payload: bytes,
                content_type: str = "application/octet-stream",
            ) -> None:
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def _send_no_content(self, status: int = 204) -> None:
                self.send_response(status)
                self.send_header("Content-Length", "0")
                self.end_headers()

            def _extract_block_id(self) -> str | None:
                if not self.path.startswith("/blocks/"):
                    return None
                return self.path.rsplit("/", 1)[-1]

            def do_GET(self) -> None:
                if self.path == "/manifest":
                    self._send_json(manifest)
                    return

                block_id = self._extract_block_id()
                if block_id is not None and block_id in block_bytes:
                    self._send_bytes(
                        block_bytes[block_id],
                        content_type="application/octet-stream",
                    )
                    return

                if self.path == "/health":
                    self._send_json({"status": "ok", "endpoint": state.endpoint})
                    return

                self._send_json({"error": "not found"}, status=404)

            def do_POST(self) -> None:
                block_id = self._extract_block_id()
                if block_id is not None:
                    length = int(self.headers.get("Content-Length", "0"))
                    payload = self.rfile.read(length) if length else b""
                    block_bytes[block_id] = payload
                    self._send_no_content(status=201)
                    return

                if self.path != "/challenge":
                    self._send_json({"error": "not found"}, status=404)
                    return

                payload = self._read_json()
                polynomial = payload.get("polynomial")
                block_id = payload.get("blockId")

                if block_id not in block_bytes:
                    self._send_json({"error": "unknown block"}, status=404)
                    return

                if not isinstance(polynomial, list) or not polynomial:
                    self._send_json({"error": "invalid polynomial"}, status=400)
                    return

                response = gf2_poly_mod(
                    bytes_to_poly_coeffs(block_bytes[block_id]),
                    np.array(polynomial, dtype=np.uint8),
                )
                self._send_json({"response": response.tolist()})

        return ProviderHandler
