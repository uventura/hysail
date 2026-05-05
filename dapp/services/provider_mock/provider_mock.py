from __future__ import annotations

import json
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import numpy as np

from hysail.utils.galois import bytes_to_poly_coeffs, gf2_poly_mod

BASE_DIR = Path(__file__).resolve().parents[2]
SHARED_EXAMPLE_DIR = BASE_DIR / "packages" / "shared" / "example"
MANIFEST_PATH = SHARED_EXAMPLE_DIR / "sample_manifest.json"
BLOCK_PATH = SHARED_EXAMPLE_DIR / "sample_block.txt"


@dataclass
class ProviderMockConfig:
    host: str = "127.0.0.1"
    port: int = 8000
    manifest_path: Path = MANIFEST_PATH
    block_path: Path = BLOCK_PATH


class ProviderMockServer:
    def __init__(self, config: ProviderMockConfig | None = None):
        self.config = config or ProviderMockConfig()
        self.manifest = json.loads(self.config.manifest_path.read_text())
        self.block_bytes = self.config.block_path.read_bytes()

    def serve_forever(self) -> None:
        server = ThreadingHTTPServer(
            (self.config.host, self.config.port), self._create_handler()
        )
        print(
            f"Provider mock listening on http://{self.config.host}:{self.config.port}"
        )
        server.serve_forever()

    def _create_handler(self):
        manifest = self.manifest
        block_bytes = self.block_bytes

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

            def do_GET(self) -> None:
                if self.path == "/manifest":
                    self._send_json(manifest)
                    return

                if self.path == f"/blocks/{manifest['blockId']}":
                    self._send_bytes(
                        block_bytes,
                        content_type="text/plain; charset=utf-8",
                    )
                    return

                if self.path == "/health":
                    self._send_json({"status": "ok"})
                    return

                self._send_json({"error": "not found"}, status=404)

            def do_POST(self) -> None:
                if self.path != "/challenge":
                    self._send_json({"error": "not found"}, status=404)
                    return

                payload = self._read_json()
                polynomial = payload.get("polynomial")
                block_id = payload.get("blockId")

                if block_id != manifest["blockId"]:
                    self._send_json({"error": "unknown block"}, status=404)
                    return

                if not isinstance(polynomial, list) or not polynomial:
                    self._send_json({"error": "invalid polynomial"}, status=400)
                    return

                response = gf2_poly_mod(
                    bytes_to_poly_coeffs(block_bytes),
                    np.array(polynomial, dtype=np.uint8),
                )
                self._send_json({"response": response.tolist()})

        return ProviderHandler
