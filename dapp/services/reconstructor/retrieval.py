from __future__ import annotations

import copy
import hashlib
import json
from urllib.request import Request, urlopen

import numpy as np

from errors import ValidationError
from models import RetrievedPacket
from hysail.utils.operators import xor_bytes


class PacketRetrievalService:
    def load_manifest(self, manifest_path) -> dict:
        return json.loads(manifest_path.read_text())

    def build_payload(self, retrieved_data: dict[int, RetrievedPacket]) -> bytes:
        return b"".join(
            retrieved_data[index].data for index in sorted(retrieved_data.keys())
        )

    def sha256_hex(self, payload: bytes) -> str:
        return hashlib.sha256(payload).hexdigest()

    def validate_payload_hash(self, manifest: dict, payload_hash: str) -> None:
        if payload_hash == manifest["originalFileHash"]:
            return

        raise ValidationError(
            "Reconstructed payload hash mismatch: "
            f"expected {manifest['originalFileHash']}, got {payload_hash}"
        )

    def retrieve_blocks(
        self,
        manifest: dict,
    ) -> tuple[dict[int, RetrievedPacket], list[RetrievedPacket]]:
        packets_by_degree: dict[int, list[dict]] = {}
        for packet in manifest["packets"]:
            packets_by_degree.setdefault(packet["degree"], []).append(
                copy.deepcopy(packet)
            )

        num_blocks_to_retrieve = (
            max(max(packet["indices"]) for packet in manifest["packets"]) + 1
        )
        retrieved_data: dict[int, RetrievedPacket] = {}
        accepted_packets: dict[str, RetrievedPacket] = {}
        degree = 1
        stalled_cycles = 0
        max_degree = max(packets_by_degree.keys())

        while len(retrieved_data) < num_blocks_to_retrieve:
            progress_made = False
            for packet in list(packets_by_degree.get(degree, [])):
                solvable_parts = self._count_solvable_parts(
                    packet, set(retrieved_data.keys())
                )
                if solvable_parts == 0:
                    continue

                partial_packet = self._solve_partial_packet(
                    packet, manifest, retrieved_data
                )
                partial_packet.degree = solvable_parts
                self._append_partial_packet(packets_by_degree, partial_packet)
                self._store_accepted_packet(accepted_packets, packet, partial_packet)

                if solvable_parts == 1:
                    retrieved_data[partial_packet.indices[0]] = partial_packet
                    progress_made = True

            degree, stalled_cycles = self._next_degree(
                degree,
                packets_by_degree,
                progress_made,
                stalled_cycles,
            )

            if stalled_cycles > max_degree:
                raise ValidationError(
                    "Unable to solve packets into a consistent reconstruction set"
                )

        return retrieved_data, list(accepted_packets.values())

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

    def _challenge_packet(self, manifest: dict, packet: dict) -> None:
        challenge_url = f"{manifest['providerEndpoint']}/challenge"
        block_macs = {
            entry["blockIndex"]: entry["macs"] for entry in manifest["blockMacs"]
        }

        for polynomial_index, polynomial in enumerate(manifest["challengePolynomials"]):
            expected = self._xor_mac_values(
                [block_macs[index][polynomial_index] for index in packet["indices"]]
            )
            response = self._post_json(
                challenge_url,
                {"blockId": packet["blockId"], "polynomial": polynomial},
            )["response"]
            if response != expected:
                raise ValidationError(
                    "Block consistency check failed before download: "
                    f"packet {packet['packetIndex']} polynomial {polynomial_index}"
                )

    def _count_solvable_parts(self, packet: dict, retrieved_indices: set[int]) -> int:
        return len(packet["indices"]) - len(set(packet["indices"]) & retrieved_indices)

    def _build_packet_record(
        self,
        packet: dict,
        data: bytes,
        indices: list[int] | None = None,
        degree: int | None = None,
    ) -> RetrievedPacket:
        return RetrievedPacket(
            packet_index=packet["packetIndex"],
            degree=packet["degree"] if degree is None else degree,
            indices=list(packet["indices"]) if indices is None else indices,
            block_id=packet["blockId"],
            price_wei=int(packet["priceWei"]),
            data=data,
        )

    def _serialize_packet(self, packet: RetrievedPacket) -> dict:
        return {
            "packetIndex": packet.packet_index,
            "degree": packet.degree,
            "indices": list(packet.indices),
            "blockId": packet.block_id,
            "priceWei": str(packet.price_wei),
            "data": packet.data,
        }

    def _fetch_packet_data(self, manifest: dict, packet: dict) -> bytes:
        if "data" in packet:
            return packet["data"]

        self._challenge_packet(manifest, packet)
        return self._fetch_bytes(
            f"{manifest['providerEndpoint']}/blocks/{packet['blockId']}"
        )

    def _reduce_packet_with_known_blocks(
        self,
        packet_data: bytes,
        remaining_indices: list[int],
        retrieved_data: dict[int, RetrievedPacket],
    ) -> tuple[bytes, list[int]]:
        reduced_data = packet_data
        unresolved_indices = list(remaining_indices)
        for index in list(unresolved_indices):
            if index in retrieved_data:
                reduced_data = xor_bytes(reduced_data, retrieved_data[index].data)
                unresolved_indices.remove(index)
        return reduced_data, unresolved_indices

    def _store_accepted_packet(
        self,
        accepted_packets: dict[str, RetrievedPacket],
        packet: dict,
        partial_packet: RetrievedPacket,
    ) -> None:
        if packet["blockId"] in accepted_packets or "data" in packet:
            return

        accepted_packets[packet["blockId"]] = self._build_packet_record(
            packet,
            data=partial_packet.data,
        )

    def _append_partial_packet(
        self,
        packets_by_degree: dict[int, list[dict]],
        partial_packet: RetrievedPacket,
    ) -> None:
        packets_by_degree.setdefault(partial_packet.degree, []).append(
            self._serialize_packet(partial_packet)
        )

    def _next_degree(
        self,
        degree: int,
        packets_by_degree: dict[int, list[dict]],
        progress_made: bool,
        stalled_cycles: int,
    ) -> tuple[int, int]:
        next_degree = degree + 1
        if next_degree <= max(packets_by_degree.keys()):
            return next_degree, stalled_cycles

        return 1, 0 if progress_made else stalled_cycles + 1

    def _solve_partial_packet(
        self,
        packet: dict,
        manifest: dict,
        retrieved_data: dict[int, RetrievedPacket],
    ) -> RetrievedPacket:
        data = self._fetch_packet_data(manifest, packet)

        remaining_indices = list(packet["indices"])
        unique_indices = set(remaining_indices)
        if len(unique_indices) == 1 and not unique_indices.issubset(retrieved_data):
            return self._build_packet_record(
                packet, data=data, indices=remaining_indices
            )

        reduced_data, unresolved_indices = self._reduce_packet_with_known_blocks(
            data,
            remaining_indices,
            retrieved_data,
        )

        return self._build_packet_record(
            packet,
            data=reduced_data,
            indices=unresolved_indices,
        )
