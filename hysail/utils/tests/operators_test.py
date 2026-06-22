from pathlib import Path

import numpy as np

from hysail.encryption.local_mac import LocalMac
import hysail.utils.galois as ga
from hysail.utils.operators import calculate_mac_for_block


def test_calculate_mac_for_block_returns_expected_local_mac():
    block = b"ABCD"
    representation = ga.bytes_to_poly_coeffs(block)
    polynomial = np.array([1, 1, 0, 1, 1], dtype=np.uint8)

    mac = calculate_mac_for_block(
        representation=representation,
        polynomial=polynomial,
        polynomial_index=2,
        block_index=7,
    )

    expected = ga.gf2_poly_mod(ga.bytes_to_poly_coeffs(block), polynomial)

    assert isinstance(mac, LocalMac)
    assert mac.polynomial_index == 2
    assert mac.block_index == 7
    assert np.array_equal(mac.mac, expected)


def test_calculate_mac_for_block_with_bad_apple_calculates_valid_macs():
    root = Path(__file__).resolve().parents[3]
    bad_apple_path = root / "examples" / "bad_apple.mp4"
    payload = bad_apple_path.read_bytes()

    block_size = 1024
    polynomial = np.array([1, 0, 1, 1, 0, 1], dtype=np.uint8)
    chunk_count = 10

    blocks = [
        payload[index : index + block_size]
        for index in range(0, len(payload), block_size)
    ]

    for block_index, block in enumerate(blocks[:chunk_count]):
        representation = ga.bytes_to_poly_coeffs(block)
        mac = calculate_mac_for_block(
            representation=representation,
            polynomial=polynomial,
            polynomial_index=0,
            block_index=block_index,
        )

        assert isinstance(mac, LocalMac)
        assert mac.block_index == block_index
        assert mac.polynomial_index == 0
        assert isinstance(mac.mac, np.ndarray)
        assert mac.mac.size == len(polynomial) - 1
