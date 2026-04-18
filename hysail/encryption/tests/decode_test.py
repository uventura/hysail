import pickle

import numpy as np

import hysail.utils.galois as ga
from hysail.encryption.block import Block, LocalBlock
from hysail.encryption.decode import Decode
from hysail.encryption.encoding_metadata import BlockMetadata, EncodingMetadata
from hysail.encryption.local_mac import LocalMac
from hysail.utils.operators import xor_bytes


class DummyServer:
    def __init__(self, data: bytes):
        self.data = data
        self.download_called = False

    def download_block(self, block_index):
        self.download_called = True
        return self.data


def _build_decoder(local_blocks=None, polynomials=None, local_mac=None):
    decoder = Decode.__new__(Decode)
    decoder._servers = []
    decoder._polynomials = polynomials or []
    decoder._local_blocks = local_blocks or {}
    decoder._local_mac = local_mac or []
    return decoder


def test_when_finding_num_blocks_to_retrieve_then_returns_total_block_count():
    local_blocks = {
        1: [Block(0, 1, [0], b"A")],
        2: [Block(1, 2, [0, 1], b"\x03")],
    }

    decoder = _build_decoder(local_blocks=local_blocks)

    assert decoder._find_num_blocks_to_retrieve() == 2


def test_when_counting_solvable_parts_then_returns_remaining_indices():
    block = Block(1, 2, [0, 1], b"\x03")
    decoder = _build_decoder()

    assert decoder._count_solvable_parts(block, set()) == 2
    assert decoder._count_solvable_parts(block, {0}) == 1
    assert decoder._count_solvable_parts(block, {0, 1}) == 0


def test_when_solving_partial_block_then_reduces_packet_with_retrieved_block():
    original = Block(1, 2, [0, 1], xor_bytes(b"A", b"B"))
    retrieved_data = {0: Block(0, 1, [0], b"A")}
    decoder = _build_decoder()

    partial = decoder._solve_partial_block(original, retrieved_data)

    assert partial.indices == [1]
    assert partial.data == b"B"
    assert partial.index == 1


def test_when_solving_partial_block_then_downloads_server_block_for_non_block_entry():
    server = DummyServer(b"C")
    local_block = LocalBlock(index=3, degree=1, indices=[0], server=server)

    polynomial = np.array([1, 1], dtype=np.uint8)
    answer = ga.gf2_poly_mod(ga.bytes_to_poly_coeffs(b"C"), polynomial)

    def receive_challenge(polynomial_arg, check_block_index):
        assert check_block_index == 3
        assert np.array_equal(polynomial_arg, polynomial)
        return answer

    server.receive_challenge = receive_challenge

    mac = ga.gf2_poly_mod(ga.bytes_to_poly_coeffs(b"C"), polynomial)
    local_mac = [[LocalMac(mac=mac, polynomial_index=0, block_index=0)]]

    decoder = _build_decoder(polynomials=[polynomial], local_mac=local_mac)

    partial = decoder._solve_partial_block(local_block, {})

    assert server.download_called is True
    assert isinstance(partial, Block)
    assert partial.data == b"C"
    assert partial.indices == [0]


def test_when_decoding_then_retrieves_blocks_in_index_order():
    local_blocks = {
        1: [Block(0, 1, [0], b"A")],
        2: [Block(1, 2, [0, 1], xor_bytes(b"A", b"B"))],
    }
    decoder = _build_decoder(local_blocks=local_blocks)

    assert decoder.decode() == b"AB"


def test_decode_loads_metadata_and_reconstructs_runtime_objects(tmp_path):
    server_dir = tmp_path / "server1"
    server_dir.mkdir()

    packet_a = Block(0, 1, [0], b"A")
    packet_b = Block(1, 1, [1], b"B")

    with open(server_dir / "payload_packet_0.pkl", "wb") as file:
        pickle.dump(packet_a, file)

    with open(server_dir / "payload_packet_1.pkl", "wb") as file:
        pickle.dump(packet_b, file)

    polynomial = np.array([1, 1], dtype=np.uint8)
    metadata = EncodingMetadata(
        polynomials=[polynomial],
        blocks=[
            BlockMetadata(
                mac_value=ga.gf2_poly_mod(ga.bytes_to_poly_coeffs(b"A"), polynomial),
                block_index=0,
                polynomial_index=0,
            ),
            BlockMetadata(
                mac_value=ga.gf2_poly_mod(ga.bytes_to_poly_coeffs(b"B"), polynomial),
                block_index=1,
                polynomial_index=0,
            ),
        ],
        packets=[],
    )
    metadata.add_packet(str(server_dir), 0, 1, [0])
    metadata.add_packet(str(server_dir), 1, 1, [1])

    metadata_file = tmp_path / "payload_metadata.pkl"
    metadata.save(metadata_file)

    server_file = tmp_path / "servers.json"
    server_file.write_text(
        '{"servers": [{"id": 1, "storage_location": "%s"}]}' % server_dir
    )

    decoder = Decode(metadata_file=metadata_file, server_file=server_file)

    assert len(decoder._local_blocks[1]) == 2
    assert isinstance(decoder._local_blocks[1][0], LocalBlock)
    assert decoder._local_mac[0][0].block_index == 0
    assert decoder._local_mac[1][0].block_index == 1
    assert decoder.decode() == b"AB"
