import numpy as np
import pytest

import hysail.utils.galois as ga
from hysail.server.server import Server


def test_when_server_initialized_then_storage_dir_created(tmp_path):
    storage_dir = tmp_path / "storage"
    Server(str(storage_dir))

    assert storage_dir.exists()
    assert storage_dir.is_dir()


def test_when_storage_check_block_then_file_is_copied(tmp_path):
    storage_dir = tmp_path / "storage"
    server = Server(str(storage_dir))

    block_file = tmp_path / "input_packet_0.pkl"
    block_data = b"test-data"
    block_file.write_bytes(block_data)

    server.storage_check_block(block_file)

    saved_file = storage_dir / block_file.name
    assert saved_file.exists()
    assert saved_file.read_bytes() == block_data


def test_when_download_block_then_returns_block_bytes(tmp_path):
    server = Server(str(tmp_path / "storage"))
    block_file = tmp_path / "input_packet_1.pkl"
    block_data = b"\x01\x02"
    block_file.write_bytes(block_data)

    server.storage_check_block(block_file)

    assert server.download_block(1) == block_data


def test_when_download_block_missing_then_raises(tmp_path):
    server = Server(str(tmp_path / "storage"))

    with pytest.raises(ValueError, match="Check block not found"):
        server.download_block(5)


def test_when_receive_challenge_then_returns_expected_response(tmp_path):
    server = Server(str(tmp_path / "storage"))
    block_file = tmp_path / "input_packet_2.pkl"
    block_data = b"\x01"
    block_file.write_bytes(block_data)

    server.storage_check_block(block_file)

    polynomial = np.array([1, 1])
    expected = ga.gf2_poly_mod(ga.bytes_to_poly_coeffs(block_data), polynomial)

    result = server.receive_challenge(polynomial, 2)

    assert np.array_equal(result, expected)


def test_when_receive_challenge_missing_then_raises(tmp_path):
    server = Server(str(tmp_path / "storage"))

    with pytest.raises(ValueError, match="Check block not found"):
        server.receive_challenge(np.array([1, 1]), 3)
