from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import numpy as np

from hysail.utils.galois import bytes_to_poly_coeffs, gf2_poly_mod

BASE_DIR = Path(__file__).resolve().parents[2]
SHARED_EXAMPLE_DIR = BASE_DIR / "packages" / "shared" / "example"
MANIFEST = json.loads((SHARED_EXAMPLE_DIR / "sample_manifest.json").read_text())
BLOCK_BYTES = (SHARED_EXAMPLE_DIR / "sample_block.txt").read_bytes()


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
        self, payload: bytes, content_type: str = "application/octet-stream"
    ) -> None:
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:
        if self.path == "/manifest":
            self._send_json(MANIFEST)
            return

        if self.path == f"/blocks/{MANIFEST['blockId']}":
            self._send_bytes(BLOCK_BYTES, content_type="text/plain; charset=utf-8")
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

        if block_id != MANIFEST["blockId"]:
            self._send_json({"error": "unknown block"}, status=404)
            return

        if not isinstance(polynomial, list) or not polynomial:
            self._send_json({"error": "invalid polynomial"}, status=400)
            return

        response = gf2_poly_mod(
            bytes_to_poly_coeffs(BLOCK_BYTES),
            np.array(polynomial, dtype=np.uint8),
        )
        self._send_json({"response": response.tolist()})


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 8000), ProviderHandler)
    print("Provider mock listening on http://127.0.0.1:8000")
    server.serve_forever()


if __name__ == "__main__":
    main()
