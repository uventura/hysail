from __future__ import annotations

import copy
import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import numpy as np
from web3 import Web3

from hysail.utils.operators import xor_bytes

BASE_DIR = Path(__file__).resolve().parents[2]
SHARED_EXAMPLE_DIR = BASE_DIR / "packages" / "shared" / "example"
DEPLOYMENTS_PATH = BASE_DIR / "packages" / "shared" / "deployments" / "local.json"
OUTPUT_DIR = Path(__file__).resolve().parents[3] / "output"
MANIFEST_PATH = SHARED_EXAMPLE_DIR / "sample_manifest.json"
DEV_PRIVATE_KEY = os.environ.get(
    "Hysail_PRIVATE_KEY",
    "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80",
)
RPC_URL = os.environ.get("Hysail_RPC_URL", "http://127.0.0.1:8545")
DOWNLOAD_MANAGER_ABI = [
    {
        "inputs": [{"internalType": "bytes32", "name": "fileId", "type": "bytes32"}],
        "name": "requestDownload",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "uint256", "name": "jobId", "type": "uint256"}],
        "name": "jobs",
        "outputs": [
            {"internalType": "bytes32", "name": "fileId", "type": "bytes32"},
            {"internalType": "address", "name": "requester", "type": "address"},
            {"internalType": "uint256", "name": "budget", "type": "uint256"},
            {"internalType": "uint256", "name": "spent", "type": "uint256"},
            {"internalType": "bytes32", "name": "resultHash", "type": "bytes32"},
            {"internalType": "bool", "name": "finalized", "type": "bool"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "jobCount",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "jobId", "type": "uint256"},
            {"internalType": "bytes32", "name": "blockId", "type": "bytes32"},
            {"internalType": "address", "name": "provider", "type": "address"},
            {"internalType": "uint256", "name": "priceWei", "type": "uint256"},
        ],
        "name": "acceptBlock",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "jobId", "type": "uint256"},
            {"internalType": "bytes32", "name": "resultHash", "type": "bytes32"},
        ],
        "name": "finalizeJob",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "uint256", "name": "jobId", "type": "uint256"}],
        "name": "rejectJob",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
]


class ValidationError(RuntimeError):
    pass


@dataclass
class RetrievedPacket:
    packet_index: int
    degree: int
    indices: list[int]
    block_id: str
    price_wei: int
    data: bytes


def sha256_hex(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def fetch_bytes(url: str) -> bytes:
    with urlopen(url) as response:
        return response.read()


def post_json(url: str, payload: dict) -> dict:
    request = Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request) as response:
        return json.loads(response.read().decode())


def xor_mac_values(mac_values: list[list[int]]) -> list[int]:
    result = np.array(mac_values[0], dtype=np.uint8)
    for mac in mac_values[1:]:
        result = np.bitwise_xor(result, np.array(mac, dtype=np.uint8))
    return result.tolist()


def challenge_packet(manifest: dict, packet: dict) -> None:
    challenge_url = f"{manifest['providerEndpoint']}/challenge"
    block_macs = {entry["blockIndex"]: entry["macs"] for entry in manifest["blockMacs"]}

    for polynomial_index, polynomial in enumerate(manifest["challengePolynomials"]):
        expected = xor_mac_values(
            [block_macs[index][polynomial_index] for index in packet["indices"]]
        )
        response = post_json(
            challenge_url,
            {"blockId": packet["blockId"], "polynomial": polynomial},
        )["response"]
        if response != expected:
            raise ValidationError(
                "Block consistency check failed before download: "
                f"packet {packet['packetIndex']} polynomial {polynomial_index}"
            )


def count_solvable_parts(packet: dict, retrieved_indices: set[int]) -> int:
    return len(packet["indices"]) - len(set(packet["indices"]) & retrieved_indices)


def solve_partial_packet(
    packet: dict, manifest: dict, retrieved_data: dict[int, RetrievedPacket]
) -> RetrievedPacket:
    if "data" not in packet:
        challenge_packet(manifest, packet)
        data = fetch_bytes(f"{manifest['providerEndpoint']}/blocks/{packet['blockId']}")
    else:
        data = packet["data"]

    remaining_indices = list(packet["indices"])
    unique_indices = set(remaining_indices)
    if len(unique_indices) == 1 and not unique_indices.issubset(retrieved_data):
        return RetrievedPacket(
            packet_index=packet["packetIndex"],
            degree=packet["degree"],
            indices=remaining_indices,
            block_id=packet["blockId"],
            price_wei=int(packet["priceWei"]),
            data=data,
        )

    for index in list(remaining_indices):
        if index in retrieved_data:
            data = xor_bytes(data, retrieved_data[index].data)
            remaining_indices.remove(index)

    return RetrievedPacket(
        packet_index=packet["packetIndex"],
        degree=packet["degree"],
        indices=remaining_indices,
        block_id=packet["blockId"],
        price_wei=int(packet["priceWei"]),
        data=data,
    )


def retrieve_blocks(
    manifest: dict,
) -> tuple[dict[int, RetrievedPacket], list[RetrievedPacket]]:
    packets_by_degree: dict[int, list[dict]] = {}
    for packet in manifest["packets"]:
        packets_by_degree.setdefault(packet["degree"], []).append(copy.deepcopy(packet))

    num_blocks_to_retrieve = (
        max(max(packet["indices"]) for packet in manifest["packets"]) + 1
    )
    retrieved_data: dict[int, RetrievedPacket] = {}
    accepted_packets: dict[str, RetrievedPacket] = {}
    degree = 1
    stalled_cycles = 0

    while len(retrieved_data) < num_blocks_to_retrieve:
        progress_made = False
        for packet in list(packets_by_degree.get(degree, [])):
            solvable_parts = count_solvable_parts(packet, set(retrieved_data.keys()))
            if solvable_parts == 0:
                continue

            partial_packet = solve_partial_packet(packet, manifest, retrieved_data)
            partial_packet.degree = solvable_parts
            packets_by_degree.setdefault(solvable_parts, []).append(
                {
                    "packetIndex": partial_packet.packet_index,
                    "degree": partial_packet.degree,
                    "indices": list(partial_packet.indices),
                    "blockId": partial_packet.block_id,
                    "priceWei": str(partial_packet.price_wei),
                    "data": partial_packet.data,
                }
            )

            if packet["blockId"] not in accepted_packets and "data" not in packet:
                accepted_packets[packet["blockId"]] = RetrievedPacket(
                    packet_index=packet["packetIndex"],
                    degree=packet["degree"],
                    indices=list(packet["indices"]),
                    block_id=packet["blockId"],
                    price_wei=int(packet["priceWei"]),
                    data=partial_packet.data,
                )

            if solvable_parts == 1:
                retrieved_data[partial_packet.indices[0]] = partial_packet
                progress_made = True

        degree += 1
        if degree > max(packets_by_degree.keys()):
            degree = 1
            stalled_cycles = 0 if progress_made else stalled_cycles + 1

        if stalled_cycles > max(packets_by_degree.keys()):
            raise ValidationError(
                "Unable to solve packets into a consistent reconstruction set"
            )

    return retrieved_data, list(accepted_packets.values())


def get_download_manager(web3: Web3):
    deployments = json.loads(DEPLOYMENTS_PATH.read_text())
    return web3.eth.contract(
        address=Web3.to_checksum_address(deployments["downloadManager"]),
        abi=DOWNLOAD_MANAGER_ABI,
    )


def get_job_id(download_manager) -> int:
    explicit_job_id = os.environ.get("Hysail_JOB_ID")
    if explicit_job_id is not None:
        return int(explicit_job_id)

    job_id = download_manager.functions.jobCount().call()
    if job_id == 0:
        raise RuntimeError("No download job available")
    return int(job_id)


def send_transaction(web3: Web3, account, function_call) -> str:
    transaction = function_call.build_transaction(
        {
            "from": account.address,
            "nonce": web3.eth.get_transaction_count(account.address),
            "chainId": web3.eth.chain_id,
            "gas": 300000,
            "gasPrice": web3.eth.gas_price,
        }
    )
    signed = account.sign_transaction(transaction)
    tx_hash = web3.eth.send_raw_transaction(signed.raw_transaction)
    web3.eth.wait_for_transaction_receipt(tx_hash)
    return tx_hash.hex()


def reject_job(download_manager, web3: Web3, account, job_id: int) -> None:
    job = download_manager.functions.jobs(job_id).call()
    if job[-1]:
        return
    send_transaction(web3, account, download_manager.functions.rejectJob(job_id))


def settle_job(
    manifest: dict, accepted_packets: list[RetrievedPacket], result_hash: str
) -> tuple[int, list[str]]:
    web3 = Web3(Web3.HTTPProvider(RPC_URL))
    account = web3.eth.account.from_key(DEV_PRIVATE_KEY)
    download_manager = get_download_manager(web3)
    job_id = get_job_id(download_manager)
    job = download_manager.functions.jobs(job_id).call()

    if Web3.to_checksum_address(job[1]) != Web3.to_checksum_address(account.address):
        raise RuntimeError(
            "Latest download job does not belong to the configured requester"
        )
    if job[-1]:
        raise RuntimeError(f"Download job {job_id} is already finalized")

    tx_hashes = []
    for packet in accepted_packets:
        tx_hashes.append(
            send_transaction(
                web3,
                account,
                download_manager.functions.acceptBlock(
                    job_id,
                    Web3.keccak(text=packet.block_id),
                    Web3.to_checksum_address(manifest["providerAddress"]),
                    packet.price_wei,
                ),
            )
        )

    tx_hashes.append(
        send_transaction(
            web3,
            account,
            download_manager.functions.finalizeJob(job_id, bytes.fromhex(result_hash)),
        )
    )
    return job_id, tx_hashes


def reject_latest_job() -> int | None:
    try:
        web3 = Web3(Web3.HTTPProvider(RPC_URL))
        account = web3.eth.account.from_key(DEV_PRIVATE_KEY)
        download_manager = get_download_manager(web3)
        job_id = get_job_id(download_manager)
        reject_job(download_manager, web3, account, job_id)
        return job_id
    except (RuntimeError, HTTPError, URLError, ValueError):
        return None


def main() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text())
    try:
        retrieved_data, accepted_packets = retrieve_blocks(manifest)
        payload = b"".join(
            retrieved_data[index].data for index in sorted(retrieved_data.keys())
        )
        payload_hash = sha256_hex(payload)

        if payload_hash != manifest["originalFileHash"]:
            raise ValidationError(
                "Reconstructed payload hash mismatch: "
                f"expected {manifest['originalFileHash']}, got {payload_hash}"
            )

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output_path = OUTPUT_DIR / manifest["outputFileName"]
        output_path.write_bytes(payload)

        job_id, tx_hashes = settle_job(manifest, accepted_packets, payload_hash)

        print("Reconstruction complete")
        print(f"Output: {output_path}")
        print(f"Result hash: {payload_hash}")
        print(f"Job finalized: {job_id}")
        for tx_hash in tx_hashes:
            print(f"Transaction: {tx_hash}")
    except ValidationError as error:
        job_id = reject_latest_job()
        if job_id is not None:
            raise SystemExit(f"{error}. Download job {job_id} rejected with refund.")
        raise SystemExit(str(error))


if __name__ == "__main__":
    main()
