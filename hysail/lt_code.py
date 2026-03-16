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


class LtCodeDecode:
    def __init__(self, packets, k):
        self._blocks = [None] * k
        self._decoded = False

        self._decode(packets)

    @property
    def blocks(self):
        return self._blocks

    @property
    def data(self):
        if not self._decoded:
            raise ValueError("Decoding not complete")
        return b"".join(self._blocks)

    @property
    def is_decoded(self):
        return self._decoded

    def _decode(self, packets):
        working_packets = self._normalize_packets(packets)

        progress = True
        while progress:
            progress = False

            for pkt in working_packets:
                if pkt["degree"] == 0:
                    continue

                self._reduce_packet(pkt)

                if self._try_resolve(pkt):
                    progress = True

        self._decoded = all(b is not None for b in self._blocks)

    def _normalize_packets(self, packets):
        return [
            {
                "degree": pkt["degree"],
                "indices": list(pkt["indices"]),
                "data": pkt["data"],
            }
            for pkt in packets
        ]

    def _reduce_packet(self, pkt):
        new_indices = []
        data = pkt["data"]

        for idx in pkt["indices"]:
            if self._blocks[idx] is not None:
                data = self._xor_bytes(data, self._blocks[idx])
            else:
                new_indices.append(idx)

        pkt["indices"] = new_indices
        pkt["degree"] = len(new_indices)
        pkt["data"] = data

    def _try_resolve(self, pkt):
        if pkt["degree"] != 1:
            return False

        idx = pkt["indices"][0]

        if self._blocks[idx] is None:
            self._blocks[idx] = pkt["data"]
            return True

        return False

    @staticmethod
    def _xor_bytes(a, b):
        return bytes(x ^ y for x, y in zip(a, b))
