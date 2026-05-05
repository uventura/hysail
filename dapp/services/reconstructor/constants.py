import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
SHARED_EXAMPLE_DIR = BASE_DIR / "packages" / "shared" / "example"
DEPLOYMENTS_PATH = BASE_DIR / "packages" / "shared" / "deployments" / "local.json"
OUTPUT_DIR = Path(__file__).resolve().parents[3] / "output"
MANIFEST_PATH = SHARED_EXAMPLE_DIR / "sample_manifest.json"
DEFAULT_PRIVATE_KEY = os.environ.get(
    "Hysail_PRIVATE_KEY",
    "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80",
)
DEFAULT_RPC_URL = os.environ.get("Hysail_RPC_URL", "http://127.0.0.1:8545")
JOB_ID_ENV_VAR = "Hysail_JOB_ID"
