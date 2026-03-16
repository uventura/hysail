import random
from functools import reduce


class LtCodeEncode:
    def __init__(self, data, block_size):
        self._degree = 0
        self._indices = []
        self._packet = []

        self._encode(data, block_size)

    @property
    def degree(self):
        return self._degree

    @property
    def indices(self):
        return self._indices

    @property
    def packet(self):
        return self._packet

    def _encode(self, data, block_size):
        blocks = self._split_blocks(data, block_size)
        k = len(blocks)
        d = random.randint(1, k)
        indices = random.sample(range(k), d)
        packet = reduce(self._xor_bytes, [blocks[i] for i in indices])

        self._degree = d
        self._indices = indices
        self._packet = packet

    def _split_blocks(self, data, block_size):
        return [data[i : i + block_size] for i in range(0, len(data), block_size)]

    def _xor_bytes(self, a, b):
        return bytes(x ^ y for x, y in zip(a, b))
