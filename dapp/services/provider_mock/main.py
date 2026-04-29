from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
SHARED_EXAMPLE_DIR = BASE_DIR / "packages" / "shared" / "example"
MANIFEST = json.loads((SHARED_EXAMPLE_DIR / "sample_manifest.json").read_text())
BLOCK_BYTES = (SHARED_EXAMPLE_DIR / "sample_block.txt").read_bytes()


class ProviderHandler(BaseHTTPRequestHandler):
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


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 8000), ProviderHandler)
    print("Provider mock listening on http://127.0.0.1:8000")
    server.serve_forever()


if __name__ == "__main__":
    main()
