from hysail.utils.operators import xor_bytes

import numpy as np
import random


class Decode:
    def __init__(self, servers, polynomials, local_blocks, local_mac):
        self._servers = servers
        self._polynomials = polynomials
        self._local_blocks = local_blocks
        self._local_mac = local_mac

    def decode(self):
        if not self._validate_blocks():
            raise ValueError("Validation failed")

        self._retrieve_blocks()
        return True

    def _retrieve_blocks(self):
        retrieved_indices = set()
        retrieved_data = []
        num_blocks_to_retrieve = len(self._local_blocks.values())

        # blocks = self._local_blocks.copy()
        # while len(retrieved_indices) < num_blocks_to_retrieve:
        for degree in sorted(self._local_blocks.keys()):
            if len(retrieved_indices) >= num_blocks_to_retrieve:
                break

            blocks = self._local_blocks[degree]
            for block in blocks:
                block_is_retrievable = self._challenge_server(block.server, block)
                indices = set(block.indices)
                if degree == 1 and not indices.issubset(retrieved_indices):
                    if block_is_retrievable:
                        retrieved_data.append(block.server.download_block(block.index))
                        retrieved_indices.update(indices)
                    continue
            print("----")

        print(retrieved_indices)
        print(retrieved_data)
        return retrieved_indices

    def _validate_blocks(self):
        degrees = sorted(self._local_blocks.keys())
        is_valid = True

        for degree in degrees:
            blocks = self._local_blocks[degree]
            for block in blocks:
                comparison = self._challenge_server(block.server, block)
                is_valid = is_valid and comparison

        return is_valid

    def _challenge_server(self, server, block):
        random_polynomial_index = random.randint(0, len(self._polynomials) - 1)
        polynomial = self._polynomials[random_polynomial_index]

        answer = server.receive_challenge(polynomial, block.index)
        macs = [
            self._local_mac[i][random_polynomial_index] for i in block.indices
        ]
        result = macs[0].mac
        for mac in macs[1:]:
            result = xor_bytes(result, mac.mac)

        if isinstance(result, bytes):
            result = np.frombuffer(result, dtype=np.uint8)

        packed_result = np.packbits(result)[0]
        packed_answer = np.packbits(answer)[0]
        comparison = bool(packed_result == packed_answer)
        if not comparison:
            print("Validation failed for block index:", block.index)

        return comparison

    # def __init__(self, packets, num_blocks, remove_padding=True):
    #     if num_blocks <= 0:
    #         raise ValueError("num_blocks must be > 0")

    #     self._blocks = [None] * num_blocks
    #     self._decoded = False
    #     self._remove_padding = remove_padding

    #     self._num_blocks = num_blocks
    #     self._packets = [p.copy() for p in packets]

    #     self._validate_packets()
    #     self._decode()

    # @property
    # def blocks(self):
    #     return self._blocks

    # @property
    # def data(self):
    #     if not self._decoded:
    #         raise ValueError("Decoding not complete")

    #     data = b"".join(self._blocks)

    #     if self._remove_padding:
    #         data = self._strip_padding(data)

    #     return data

    # @property
    # def is_decoded(self):
    #     return self._decoded

    # def _validate_packets(self):
    #     """
    #     Ensure all packet indices are within valid range.
    #     Prevents IndexError during decoding.
    #     """
    #     for pkt in self._packets:
    #         for idx in pkt.indices:
    #             if idx < 0 or idx >= self._num_blocks:
    #                 raise ValueError(f"Packet index out of range: {idx}")

    # def _decode(self):
    #     progress = True

    #     while progress:
    #         progress = False

    #         for pkt in self._packets:
    #             if pkt.degree == 0:
    #                 continue

    #             self._reduce_packet(pkt)

    #             if self._try_resolve(pkt):
    #                 progress = True

    #     self._decoded = all(block is not None for block in self._blocks)

    # def _reduce_packet(self, pkt):
    #     new_indices = []
    #     data = pkt.data

    #     for idx in pkt.indices:
    #         block = self._blocks[idx]

    #         if block is not None:
    #             data = self._xor_bytes(data, block)
    #         else:
    #             new_indices.append(idx)

    #     pkt.indices = new_indices
    #     pkt.degree = len(new_indices)
    #     pkt.data = data

    # def _try_resolve(self, pkt):
    #     if pkt.degree != 1:
    #         return False

    #     idx = pkt.indices[0]

    #     if self._blocks[idx] is None:
    #         self._blocks[idx] = pkt.data
    #         return True

    #     return False

    # def _strip_padding(self, data):
    #     if not data:
    #         return data

    #     pad = data[-1]

    #     if pad == 0 or pad > len(data):
    #         return data

    #     if data[-pad:] != bytes([pad]) * pad:
    #         return data

    #     return data[:-pad]

    # @staticmethod
    # def _xor_bytes(a, b):
    #     return bytes(x ^ y for x, y in zip(a, b))
