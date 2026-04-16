from hysail.utils.operators import xor_bytes
from hysail.encryption.block import Block
from hysail.logger.logger import execution_logger

import numpy as np
import random


class Decode:
    def __init__(self, servers, polynomials, local_blocks, local_mac):
        self._servers = servers
        self._polynomials = polynomials
        self._local_blocks = local_blocks
        self._local_mac = local_mac

    def decode(self):
        data = self._retrieve_blocks()
        result = b""
        for msg_i in sorted(data.keys()):
            result += data[msg_i].data
        return result

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
        num_blocks_to_retrieve = 0
        for block in self._local_blocks:
            for e in self._local_blocks[block]:
                max_index = max(e.indices)
                if max_index > num_blocks_to_retrieve:
                    num_blocks_to_retrieve = max_index
        return num_blocks_to_retrieve

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
