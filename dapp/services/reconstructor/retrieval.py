from __future__ import annotations

import hashlib
import json
from urllib.request import Request, urlopen

import numpy as np

from errors import ValidationError
from hysail.encryption.block import LocalBlock
from hysail.encryption.decode import Decode
from hysail.encryption.local_mac import LocalMac
from models import RetrievedBlock


class ManifestBlockServer:
    def __init__(
        self, retrieval_service: "BlockRetrievalService", manifest: dict, block: dict
    ):
        self._retrieval_service = retrieval_service
        self._manifest = manifest
        self._block = block
        self._storage_location = manifest["providerEndpoint"]

    def download_block(self, block_index):
        if block_index != self._block["packetIndex"]:
            raise ValueError(f"Unexpected block index: {block_index}")

        return self._retrieval_service.fetch_block_data(self._manifest, self._block)

    def receive_challenge(self, polynomial, check_block_index):
        if check_block_index != self._block["packetIndex"]:
            raise ValueError(f"Unexpected block index: {check_block_index}")

        return self._retrieval_service.challenge_block(
            self._manifest,
            self._block,
            polynomial,
        )


class BlockRetrievalService:
    def load_manifest(self, manifest_path) -> dict:
        return json.loads(manifest_path.read_text())

    def build_decoder(self, manifest: dict) -> Decode:
        return Decode(
            polynomials=self._build_polynomials(manifest),
            local_blocks=self._build_local_blocks(manifest),
            local_mac=self._build_local_mac(manifest),
        )

    def build_accepted_blocks(self, decoder: Decode) -> list[RetrievedBlock]:
        return [
            RetrievedBlock(
                block_index=block.index,
                degree=block.degree,
                indices=list(block.indices),
                block_id=block.block_id,
                price_wei=int(block.price_wei),
                data=b"",
            )
            for block in decoder.get_accepted_blocks()
        ]

    def sha256_hex(self, payload: bytes) -> str:
        return hashlib.sha256(payload).hexdigest()

    def validate_payload_hash(self, manifest: dict, payload_hash: str) -> None:
        if payload_hash == manifest["originalFileHash"]:
            return

        raise ValidationError(
            "Reconstructed payload hash mismatch: "
            f"expected {manifest['originalFileHash']}, got {payload_hash}"
        )

    def _fetch_bytes(self, url: str) -> bytes:
        with urlopen(url) as response:
            return response.read()

    def _post_json(self, url: str, payload: dict) -> dict:
        request = Request(
            url,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request) as response:
            return json.loads(response.read().decode())

    def _xor_mac_values(self, mac_values: list[list[int]]) -> list[int]:
        result = np.array(mac_values[0], dtype=np.uint8)
        for mac in mac_values[1:]:
            result = np.bitwise_xor(result, np.array(mac, dtype=np.uint8))
        return result.tolist()

    def challenge_block(
        self,
        manifest: dict,
        block: dict,
        polynomial: np.ndarray,
    ) -> np.ndarray:
        challenge_url = f"{manifest['providerEndpoint']}/challenge"
        block_macs = {
            entry["blockIndex"]: entry["macs"] for entry in manifest["blockMacs"]
        }

        response = self._post_json(
            challenge_url,
            {
                "blockId": block["blockId"],
                "polynomial": polynomial.tolist(),
            },
        )["response"]

        polynomial_index = self._find_polynomial_index(manifest, polynomial)
        expected = self._xor_mac_values(
            [block_macs[index][polynomial_index] for index in block["indices"]]
        )
        if response != expected:
            raise ValidationError(
                "Block consistency check failed before download: "
                f"block {block['packetIndex']} polynomial {polynomial_index}"
            )

        return np.array(response, dtype=np.uint8)

    def fetch_block_data(self, manifest: dict, block: dict) -> bytes:
        return self._fetch_bytes(
            f"{manifest['providerEndpoint']}/blocks/{block['blockId']}"
        )

    def _build_polynomials(self, manifest: dict) -> list[np.ndarray]:
        return [
            np.array(polynomial, dtype=np.uint8)
            for polynomial in manifest["challengePolynomials"]
        ]

    def _build_local_blocks(self, manifest: dict) -> dict[int, list[LocalBlock]]:
        local_blocks: dict[int, list[LocalBlock]] = {}
        for block in manifest["packets"]:
            local_blocks.setdefault(block["degree"], []).append(
                LocalBlock(
                    index=block["packetIndex"],
                    degree=block["degree"],
                    indices=list(block["indices"]),
                    server=ManifestBlockServer(self, manifest, block),
                    block_id=block["blockId"],
                    price_wei=int(block["priceWei"]),
                )
            )
        return local_blocks

    def _build_local_mac(self, manifest: dict) -> dict[int, dict[int, LocalMac]]:
        local_mac: dict[int, dict[int, LocalMac]] = {}
        for block in manifest["blockMacs"]:
            local_mac[block["blockIndex"]] = {
                polynomial_index: LocalMac(
                    mac=np.array(mac_value, dtype=np.uint8),
                    polynomial_index=polynomial_index,
                    block_index=block["blockIndex"],
                )
                for polynomial_index, mac_value in enumerate(block["macs"])
            }
        return local_mac

    def _find_polynomial_index(self, manifest: dict, polynomial: np.ndarray) -> int:
        polynomial_values = polynomial.tolist()
        for index, candidate in enumerate(manifest["challengePolynomials"]):
            if candidate == polynomial_values:
                return index

        raise ValidationError("Challenge polynomial not present in manifest")
