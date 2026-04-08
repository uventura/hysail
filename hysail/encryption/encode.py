import random
from functools import reduce
import numpy as np

from hysail.encryption.block import Block
from hysail.encryption.local_mac import LocalMac
import hysail.utils.galois as ga
import hysail.utils.operators as op

POLYNOMIAL_SET_SIZE = 40


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
        self._polynomials = self._polynomial_set_generation()
        self._mac_blocks = self._calculate_mac_for_each_block()

        self._num_blocks = len(self._blocks)

        self._packets = self._encode()

    @property
    def packets(self):
        values = self._packets.values()
        return [pkt for sublist in values for pkt in sublist]

    @property
    def num_blocks(self):
        return self._num_blocks

    @property
    def mac_blocks(self):
        return self._mac_blocks

    @property
    def polynomials(self):
        return self._polynomials

    def _encode(self):
        packets = {}
        K = self._num_blocks
        overhead = 1.5
        num_to_send = int(K * overhead)
        probabilities = op.robust_soliton_distribution(K)

        for index in range(num_to_send):
            degree = np.random.choice(range(len(probabilities)), p=probabilities)
            # Ensure degree is at least 1 (the RSD can sometimes have a tiny p(0))
            degree = max(1, degree)
            indices = random.sample(range(K), degree)

            data = reduce(op.xor_bytes, (self._blocks[i] for i in indices))
            if degree not in packets:
                packets[degree] = []
            packets[degree].append(Block(index, int(degree), indices, data))
        return packets

    def _pad(self, data):
        pad = self._block_size - (len(data) % self._block_size)
        if pad == 0:
            pad = self._block_size
        return data + bytes([pad]) * pad

    def _split_blocks(self, data, block_size):
        return [data[i : i + block_size] for i in range(0, len(data), block_size)]

    def _calculate_mac_for_each_block(self):
        mac_blocks = {}
        for index, block in enumerate(self._blocks):
            representation = ga.bytes_to_poly_coeffs(block)
            mac_blocks[index] = []

            for p_index, polynomial in enumerate(self._polynomials):
                mac = LocalMac(
                    mac=ga.gf2_poly_mod(representation, polynomial),
                    polynomial_index=p_index,
                    block_index=index,
                )
                mac_blocks[index].append(mac)

        return mac_blocks

    def _polynomial_set_generation(self):
        polynomials = []
        for _ in range(POLYNOMIAL_SET_SIZE):
            polynomial = ga.generate_challenge_polynomial()
            if polynomial.tolist() not in [p.tolist() for p in polynomials]:
                polynomials.append(polynomial)
        return polynomials
