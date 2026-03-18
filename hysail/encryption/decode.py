class Decode:
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
