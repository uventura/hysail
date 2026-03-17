import random
from functools import reduce


class LtPacket:
    def __init__(self, degree, indices, data):
        self.degree = degree
        self.indices = list(indices)
        self.data = data

    def copy(self):
        return LtPacket(self.degree, self.indices.copy(), self.data)


class LtCodeEncode:
    def __init__(self, data, block_size, num_packets=1):
        if not data:
            raise ValueError("Data cannot be empty")

        if num_packets <= 0:
            raise ValueError("num_packets must be > 0")

        self._block_size = block_size
        self._data = self._pad(data)

        self._blocks = self._split_blocks(self._data, block_size)
        self._num_blocks = len(self._blocks)

        self._packets = self._encode(num_packets)

    @property
    def packets(self):
        return self._packets

    @property
    def num_blocks(self):
        return self._num_blocks

    def _encode(self, num_packets):
        packets = []

        for _ in range(num_packets):
            degree = random.randint(1, self._num_blocks)
            indices = random.sample(range(self._num_blocks), degree)

            data = reduce(self._xor_bytes, (self._blocks[i] for i in indices))

            packets.append(LtPacket(degree, indices, data))

        return packets

    def _pad(self, data):
        pad = self._block_size - (len(data) % self._block_size)
        if pad == 0:
            pad = self._block_size
        return data + bytes([pad]) * pad

    def _split_blocks(self, data, block_size):
        return [data[i : i + block_size] for i in range(0, len(data), block_size)]

    @staticmethod
    def _xor_bytes(a, b):
        return bytes(x ^ y for x, y in zip(a, b))


class LtCodeDecode:
    def __init__(self, packets, num_blocks, remove_padding=True):
        if num_blocks <= 0:
            raise ValueError("num_blocks must be > 0")

        self._blocks = [None] * num_blocks
        self._decoded = False
        self._remove_padding = remove_padding

        self._num_blocks = num_blocks
        self._packets = [p.copy() for p in packets]

        self._validate_packets()
        self._decode()

    @property
    def blocks(self):
        return self._blocks

    @property
    def data(self):
        if not self._decoded:
            raise ValueError("Decoding not complete")

        data = b"".join(self._blocks)

        if self._remove_padding:
            data = self._strip_padding(data)

        return data

    @property
    def is_decoded(self):
        return self._decoded

    def _validate_packets(self):
        """
        Ensure all packet indices are within valid range.
        Prevents IndexError during decoding.
        """
        for pkt in self._packets:
            for idx in pkt.indices:
                if idx < 0 or idx >= self._num_blocks:
                    raise ValueError(f"Packet index out of range: {idx}")

    def _decode(self):
        progress = True

        while progress:
            progress = False

            for pkt in self._packets:
                if pkt.degree == 0:
                    continue

                self._reduce_packet(pkt)

                if self._try_resolve(pkt):
                    progress = True

        self._decoded = all(block is not None for block in self._blocks)

    def _reduce_packet(self, pkt):
        new_indices = []
        data = pkt.data

        for idx in pkt.indices:
            block = self._blocks[idx]

            if block is not None:
                data = self._xor_bytes(data, block)
            else:
                new_indices.append(idx)

        pkt.indices = new_indices
        pkt.degree = len(new_indices)
        pkt.data = data

    def _try_resolve(self, pkt):
        if pkt.degree != 1:
            return False

        idx = pkt.indices[0]

        if self._blocks[idx] is None:
            self._blocks[idx] = pkt.data
            return True

        return False

    def _strip_padding(self, data):
        if not data:
            return data

        pad = data[-1]

        if pad == 0 or pad > len(data):
            return data

        if data[-pad:] != bytes([pad]) * pad:
            return data

        return data[:-pad]

    @staticmethod
    def _xor_bytes(a, b):
        return bytes(x ^ y for x, y in zip(a, b))
