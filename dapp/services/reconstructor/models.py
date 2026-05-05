from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from constants import (
    DEFAULT_PRIVATE_KEY,
    DEFAULT_RPC_URL,
    DEPLOYMENTS_PATH,
    MANIFEST_PATH,
    OUTPUT_DIR,
)


@dataclass
class ReconstructorConfig:
    manifest_path: Path = MANIFEST_PATH
    deployments_path: Path = DEPLOYMENTS_PATH
    output_dir: Path = OUTPUT_DIR
    rpc_url: str = DEFAULT_RPC_URL
    private_key: str = DEFAULT_PRIVATE_KEY


@dataclass
class RetrievedPacket:
    packet_index: int
    degree: int
    indices: list[int]
    block_id: str
    price_wei: int
    data: bytes


@dataclass
class ReconstructionResult:
    output_path: Path
    payload_hash: str
    job_id: int
    tx_hashes: list[str]


@dataclass
class ChainContext:
    web3: object
    account: object
    download_manager: object


@dataclass
class JobContext:
    chain_context: ChainContext
    job_id: int
    job: object
