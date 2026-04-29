import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import List

import numpy as np


@dataclass
class BlockMetadata:
    mac_value: np.ndarray
    block_index: int
    polynomial_index: int


@dataclass
class PacketMetadata:
    server: str  # storage_location
    packet_index: int
    degree: int
    indices: List[int]


@dataclass
class EncodingMetadata:
    polynomials: List[np.ndarray]
    blocks: List[BlockMetadata]
    packets: List[PacketMetadata]
    original_filename: str = ""
    original_file_hash: str = ""
    packet_root_hash: str = ""

    def add_packet(
        self, server: str, packet_index: int, degree: int, indices: List[int]
    ):
        self.packets.append(PacketMetadata(server, packet_index, degree, indices))

    def save(self, file_path: Path):
        with open(file_path, "wb") as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, file_path: Path) -> "EncodingMetadata":
        with open(file_path, "rb") as f:
            metadata = pickle.load(f)

        if not hasattr(metadata, "original_filename"):
            metadata.original_filename = ""
        if not hasattr(metadata, "original_file_hash"):
            metadata.original_file_hash = ""
        if not hasattr(metadata, "packet_root_hash"):
            metadata.packet_root_hash = ""

        return metadata
