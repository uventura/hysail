import random
from functools import reduce
import numpy as np

from hysail.encryption.block import Block
from hysail.encryption.local_mac import LocalMac
from hysail.logger.progress import get_progress
import hysail.utils.galois as ga
import hysail.utils.operators as op
from hysail.utils.padding import add_padding
from hysail.constant import POLYNOMIAL_SET_SIZE


# It uses LtCode
class Encode:
    def __init__(self, data, block_size):
        if not data:
            raise ValueError("Data cannot be empty")

        self._progress = get_progress()
        self._block_size = block_size

        prepare_task_id = None
        if self._progress is not None:
            prepare_task_id = self._progress.add_task(
                "Preparing data for encoding", total=2
            )

        self._data = add_padding(data, self._block_size)
        if prepare_task_id is not None:
            self._progress.advance(prepare_task_id)

        self._blocks = self._split_blocks(self._data, block_size)
        if prepare_task_id is not None:
            self._progress.advance(prepare_task_id)

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
        overhead = 6
        num_to_send = int(K * overhead)
        probabilities = op.robust_soliton_distribution(K)

        task_id = None
        if self._progress is not None:
            task_id = self._progress.add_task("Encoding packets", total=num_to_send)

        for index in range(num_to_send):
            packet = self._generate_packet(index, K, probabilities)
            degree = packet.degree
            if degree not in packets:
                packets[degree] = []
            packets[degree].append(packet)

            if task_id is not None:
                self._progress.advance(task_id)

        return packets

    def _generate_packet(self, index, K, probabilities):
        degree = np.random.choice(range(len(probabilities)), p=probabilities)
        # Ensure degree is at least 1 (the RSD can sometimes have a tiny p(0))
        degree = max(1, degree)
        indices = random.sample(range(K), degree)

        data = reduce(op.xor_bytes, (self._blocks[i] for i in indices))
        return Block(index, int(degree), indices, data)

    def _split_blocks(self, data, block_size):
        return [data[i : i + block_size] for i in range(0, len(data), block_size)]

    def _calculate_mac_for_each_block(self):
        mac_blocks = {}
        task_id = None
        if self._progress is not None:
            task_id = self._progress.add_task(
                "Calculating MAC blocks",
                total=len(self._blocks) * len(self._polynomials),
            )

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
                if task_id is not None:
                    self._progress.advance(task_id)

        return mac_blocks

    def _polynomial_set_generation(self):
        polynomials = []
        task_id = None
        if self._progress is not None:
            task_id = self._progress.add_task(
                "Generating challenge polynomials", total=POLYNOMIAL_SET_SIZE
            )

        while len(polynomials) < POLYNOMIAL_SET_SIZE:
            polynomial = ga.generate_challenge_polynomial()
            if polynomial.tolist() not in [p.tolist() for p in polynomials]:
                polynomials.append(polynomial)
                if task_id is not None:
                    self._progress.advance(task_id)

        return polynomials
