from hysail.utils.operators import xor_bytes
from hysail.encryption.block import Block
from hysail.logger.logger import ExecutionLogger

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
        ExecutionLogger.info(self._local_blocks)
        num_blocks_to_retrieve = self._find_num_blocks_to_retrieve()

        blocks = self._local_blocks.copy()
        ExecutionLogger.info("LOCAL BLOCKS")
        for block in blocks:
            ExecutionLogger.info(f"[{block}]:")
            for e in blocks[block]:
                ExecutionLogger.info(f"  {e}")
            ExecutionLogger.info("*" * 10)
        ExecutionLogger.info("=" * 20)

        degree = 1
        ExecutionLogger.info(f"Num blocks to retrieve: {num_blocks_to_retrieve}")
        while len(retrieved_data.keys()) < num_blocks_to_retrieve:
            ExecutionLogger.info(f"Degree: {degree}, solved: {retrieved_data.keys()}")
            ExecutionLogger.info(retrieved_data)

            for index, block in enumerate(blocks.get(degree, [])):
                solvable_parts = int(
                    self._count_solvable_parts(block, set(retrieved_data.keys()))
                )
                ExecutionLogger.info(
                    f"Solvable parts for block {block}: {solvable_parts}"
                )
                if solvable_parts == 0:
                    blocks[degree].pop(index)
                else:
                    ExecutionLogger.info(block)
                    partial_block = self._solve_partial_block(block, retrieved_data)
                    partial_block.degree = solvable_parts
                    ExecutionLogger.info(f"Partial block data: {partial_block}")
                    if solvable_parts in blocks:
                        blocks[solvable_parts].append(partial_block)
                    else:
                        blocks[solvable_parts] = [partial_block]

                    if solvable_parts == 1:
                        retrieved_data[block.indices[0]] = partial_block
                    blocks[degree].pop(index)
                    ExecutionLogger.info("\n")
            degree += 1
            if degree > max(blocks.keys()):
                degree = 1
            ExecutionLogger.info("#" * 40)

        ExecutionLogger.info(retrieved_data)
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
        ExecutionLogger.info(f"block: {block}, retrieved_indices: {retrieved_indices}")
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
            ExecutionLogger.info("Validation failed for block index:", block.index)

        return comparison
