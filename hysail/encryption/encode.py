import random
from functools import reduce

from hysail.encryption.block import Block
from hysail.encryption.local_mac import LocalMac
import hysail.utils.galois as ga


# It uses LtCode
class Encode:
    def __init__(self, data, block_size, num_packets=1):
        if not data:
            raise ValueError("Data cannot be empty")

        if num_packets <= 0:
            raise ValueError("num_packets must be > 0")

        self._block_size = block_size
        self._data = self._pad(data)

        self._blocks = self._split_blocks(self._data, block_size)
        self._mac_blocks = self._calculate_mac_for_each_block()

        self._num_blocks = len(self._blocks)

        self._packets = self._encode(num_packets)

    @property
    def packets(self):
        return self._packets

    @property
    def num_blocks(self):
        return self._num_blocks

    @property
    def mac_blocks(self):
        return self._mac_blocks

    def _encode(self, num_packets):
        packets = []

        for _ in range(num_packets):
            degree = random.randint(1, self._num_blocks)
            indices = random.sample(range(self._num_blocks), degree)

            data = reduce(self._xor_bytes, (self._blocks[i] for i in indices))
            packets.append(Block(degree, indices, data))

        return packets

    def _pad(self, data):
        pad = self._block_size - (len(data) % self._block_size)
        if pad == 0:
            pad = self._block_size
        return data + bytes([pad]) * pad

    def _split_blocks(self, data, block_size):
        return [data[i : i + block_size] for i in range(0, len(data), block_size)]

    def _calculate_mac_for_each_block(self):
        mac_blocks = []
        for block in self._blocks:
            representation = ga.bytes_to_poly_coeffs(block)
            random_polynomial = ga.generate_challenge_polynomial()
            mac = LocalMac(
                polynomial=random_polynomial,
                mac=ga.gf2_poly_mod(representation, random_polynomial),
            )
            mac_blocks.append(mac)
        return mac_blocks

    @staticmethod
    def _xor_bytes(a, b):
        return bytes(x ^ y for x, y in zip(a, b))
