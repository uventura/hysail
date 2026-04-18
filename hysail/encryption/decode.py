import json
import random
from pathlib import Path

import numpy as np

from hysail.encryption.block import Block, LocalBlock
from hysail.encryption.encoding_metadata import EncodingMetadata
from hysail.encryption.local_mac import LocalMac
from hysail.logger.logger import execution_logger
from hysail.server.server import Server
from hysail.utils.operators import xor_bytes
from hysail.utils.padding import remove_padding


class Decode:
    def __init__(self, metadata_file, server_file):
        self._servers = self._load_servers(server_file)
        self._polynomials = []
        self._local_blocks = {}
        self._local_mac = []

        self._load_from_metadata(metadata_file)

    def decode(self):
        data = self._retrieve_blocks()
        result = b""
        for msg_i in sorted(data.keys()):
            result += data[msg_i].data
        return remove_padding(result)

    def _retrieve_blocks(self):
        retrieved_data = {}
        num_blocks_to_retrieve = self._find_num_blocks_to_retrieve()

        blocks = self._local_blocks.copy()
        self._log_all_local_blocks(blocks)

        degree = 1
        execution_logger.debug(
            f"Number of blocks to retrieve: {num_blocks_to_retrieve}"
        )
        while len(retrieved_data.keys()) < num_blocks_to_retrieve:
            execution_logger.debug(
                f"Degree: {degree}, solved: {retrieved_data.keys()}\n"
            )

            for _, block in enumerate(blocks.get(degree, [])):
                solvable_parts = int(
                    self._count_solvable_parts(block, set(retrieved_data.keys()))
                )
                execution_logger.debug(f"Solvable parts: {solvable_parts}")
                execution_logger.debug(f"Block: {block}")
                if solvable_parts == 0:
                    execution_logger.debug("Block is already solved, skipping.\n")
                    continue

                partial_block = self._solve_partial_block(block, retrieved_data)
                partial_block.degree = solvable_parts
                execution_logger.debug(f"Partial block data: {partial_block}\n")

                if solvable_parts in blocks:
                    blocks[solvable_parts].append(partial_block)
                else:
                    blocks[solvable_parts] = [partial_block]

                if solvable_parts == 1:
                    retrieved_data[block.indices[0]] = partial_block
                    execution_logger.info(f"Retrieved block index: {block.indices[0]}")
            degree += 1
            if degree > max(blocks.keys()):
                degree = 1
            execution_logger.debug("-" * 40)

        execution_logger.debug(retrieved_data)
        return retrieved_data

    def _find_num_blocks_to_retrieve(self):
        max_index = -1
        for blocks in self._local_blocks.values():
            for block in blocks:
                if block.indices:
                    max_index = max(max_index, max(block.indices))
        return max_index + 1

    def _count_solvable_parts(self, block, retrieved_indices):
        return len(block.indices) - len(set(block.indices) & retrieved_indices)

    def _solve_partial_block(self, block, retrieved_data):
        if not isinstance(block, Block):
            self._challenge_server(block.server, block)
            data = block.server.download_block(block.index)
        else:
            data = block.data

        indices = set(block.indices)
        if len(indices) == 1 and not indices.issubset(retrieved_data):
            return Block(block.index, block.degree, block.indices, data)

        for index in block.indices:
            if index in retrieved_data:
                data = xor_bytes(data, retrieved_data[index].data)
                block.indices.remove(index)
        return Block(block.index, block.degree, block.indices, data)

    def _challenge_server(self, server, block):
        random_polynomial_index = random.randint(0, len(self._polynomials) - 1)
        polynomial = self._polynomials[random_polynomial_index]

        answer = server.receive_challenge(polynomial, block.index)
        macs = [self._local_mac[i][random_polynomial_index] for i in block.indices]
        result = macs[0].mac
        for mac in macs[1:]:
            result = xor_bytes(result, mac.mac)

        if isinstance(result, bytes):
            result = np.frombuffer(result, dtype=np.uint8)

        packed_result = np.packbits(result)[0]
        packed_answer = np.packbits(answer)[0]
        comparison = bool(packed_result == packed_answer)
        if not comparison:
            execution_logger.error(f"Validation failed for block index: {block.index}")

        return comparison

    def _log_all_local_blocks(self, blocks):
        execution_logger.debug("-" * 20)
        execution_logger.debug(" " * 4 + "LOCAL BLOCKS")
        execution_logger.debug("-" * 20)

        for block in blocks:
            execution_logger.debug(f"[{block}]:")
            for e in blocks[block]:
                execution_logger.debug(f"  {e}")
            execution_logger.debug("-" * 10)
        execution_logger.debug("_" * 20)

    def _load_from_metadata(self, metadata_file):
        metadata = EncodingMetadata.load(Path(metadata_file))
        server_cache = {server._storage_location: server for server in self._servers}
        execution_logger.debug(
            f"Loaded metadata from {metadata_file}: "
            f"{len(metadata.polynomials)} polynomials, "
            f"{len(metadata.blocks)} block MACs, "
            f"{len(metadata.packets)} packets"
        )
        self._polynomials = metadata.polynomials
        self._local_blocks = self._build_local_blocks(metadata, server_cache)
        self._local_mac = self._build_local_mac(metadata)

    def _build_local_blocks(self, metadata, server_cache):
        local_blocks = {}
        execution_logger.debug("Building local blocks from metadata")
        for packet in metadata.packets:
            server = server_cache.get(packet.server)
            if server is None:
                raise ValueError(
                    f"Server not found for storage location: {packet.server}"
                )

            local_block = LocalBlock(
                index=packet.packet_index,
                degree=packet.degree,
                indices=list(packet.indices),
                server=server,
            )
            local_blocks.setdefault(packet.degree, []).append(local_block)
            execution_logger.debug(
                "Generated local block: "
                f"index={local_block.index}, "
                f"degree={local_block.degree}, "
                f"indices={local_block.indices}, "
                f"server={local_block.server._storage_location}"
            )

        execution_logger.debug(
            f"Built local blocks grouped by degree: "
            f"{ {degree: len(blocks) for degree, blocks in local_blocks.items()} }"
        )
        return local_blocks

    def _build_local_mac(self, metadata):
        if not metadata.blocks:
            execution_logger.debug("No local MAC entries found in metadata")
            return []

        num_blocks = max(block.block_index for block in metadata.blocks) + 1
        local_mac = [
            [None for _ in range(len(metadata.polynomials))] for _ in range(num_blocks)
        ]

        execution_logger.debug(
            f"Building local MAC matrix with {num_blocks} blocks and "
            f"{len(metadata.polynomials)} polynomials"
        )

        for block_metadata in metadata.blocks:
            local_mac[block_metadata.block_index][block_metadata.polynomial_index] = (
                LocalMac(
                    mac=block_metadata.mac_value,
                    polynomial_index=block_metadata.polynomial_index,
                    block_index=block_metadata.block_index,
                )
            )
            execution_logger.debug(
                "Generated local MAC: "
                f"block_index={block_metadata.block_index}, "
                f"polynomial_index={block_metadata.polynomial_index}, "
                f"mac_value={block_metadata.mac_value}"
            )

        execution_logger.debug(
            "Built local MAC matrix occupancy: "
            f"{[sum(mac is not None for mac in row) for row in local_mac]}"
        )

        return local_mac

    def _load_servers(self, server_file):
        with open(server_file, "r") as file:
            data = json.load(file)

        servers = [
            Server(server_dict["storage_location"])
            for server_dict in data.get("servers", [])
        ]

        execution_logger.debug(f"Loaded {len(servers)} servers from {server_file}")
        for server in servers:
            execution_logger.debug(
                f"Generated server: storage_location={server._storage_location}"
            )

        return servers
