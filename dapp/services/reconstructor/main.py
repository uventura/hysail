from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.request import urlopen

BASE_DIR = Path(__file__).resolve().parents[2]
SHARED_EXAMPLE_DIR = BASE_DIR / "packages" / "shared" / "example"
OUTPUT_DIR = Path(__file__).resolve().parents[3] / "output"
MANIFEST_PATH = SHARED_EXAMPLE_DIR / "sample_manifest.json"


def sha256_hex(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def fetch_bytes(url: str) -> bytes:
    with urlopen(url) as response:
        return response.read()


def main() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text())
    block_url = f"{manifest['providerEndpoint']}/blocks/{manifest['blockId']}"
    payload = fetch_bytes(block_url)
    payload_hash = sha256_hex(payload)

    if payload_hash != manifest["blockHash"]:
        raise SystemExit(
            "Block validation failed: "
            f"expected {manifest['blockHash']}, got {payload_hash}"
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / manifest["outputFileName"]
    output_path.write_bytes(payload)

    print("Reconstruction complete")
    print(f"Output: {output_path}")
    print(f"Result hash: {payload_hash}")


if __name__ == "__main__":
    main()
