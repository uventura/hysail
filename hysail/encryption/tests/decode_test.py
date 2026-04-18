from hysail.encryption.block import Block, LocalBlock
from hysail.encryption.decode import Decode
from hysail.utils.operators import xor_bytes


class DummyServer:
    def __init__(self, data: bytes):
        self.data = data
        self.download_called = False

    def download_block(self, block_index):
        self.download_called = True
        return self.data


def test_when_finding_num_blocks_to_retrieve_then_returns_max_block_index():
    local_blocks = {
        1: [Block(1, 1, [1], b"A")],
        2: [Block(2, 2, [1, 2], b"\x03")],
    }

    decoder = Decode(
        servers=[], polynomials=[], local_blocks=local_blocks, local_mac=[]
    )

    assert decoder._find_num_blocks_to_retrieve() == 2


def test_when_counting_solvable_parts_then_returns_remaining_indices():
    block = Block(2, 2, [1, 2], b"\x03")
    decoder = Decode(servers=[], polynomials=[], local_blocks={}, local_mac=[])

    assert decoder._count_solvable_parts(block, set()) == 2
    assert decoder._count_solvable_parts(block, {1}) == 1
    assert decoder._count_solvable_parts(block, {1, 2}) == 0


def test_when_solving_partial_block_then_reduces_packet_with_retrieved_block():
    original = Block(2, 2, [1, 2], xor_bytes(b"A", b"B"))
    retrieved_data = {1: Block(1, 1, [1], b"A")}
    decoder = Decode(servers=[], polynomials=[], local_blocks={}, local_mac=[])

    partial = decoder._solve_partial_block(original, retrieved_data)

    assert partial.indices == [2]
    assert partial.data == b"B"
    assert partial.index == 2


def test_when_solving_partial_block_then_downloads_server_block_for_non_block_entry():
    import numpy as np
    import hysail.utils.galois as ga

    server = DummyServer(b"C")
    local_block = LocalBlock(index=3, degree=1, indices=[1], server=server)

    polynomial = np.array([1, 1], dtype=np.uint8)
    answer = ga.gf2_poly_mod(ga.bytes_to_poly_coeffs(b"C"), polynomial)

    def receive_challenge(polynomial_arg, check_block_index):
        assert check_block_index == 3
        assert np.array_equal(polynomial_arg, polynomial)
        return answer

    server.receive_challenge = receive_challenge

    from hysail.encryption.local_mac import LocalMac

    mac = ga.gf2_poly_mod(ga.bytes_to_poly_coeffs(b"C"), polynomial)
    local_mac = [[], [LocalMac(mac=mac, polynomial_index=0, block_index=1)]]

    decoder = Decode(
        servers=[],
        polynomials=[polynomial],
        local_blocks={},
        local_mac=local_mac,
    )

    partial = decoder._solve_partial_block(local_block, {})

    assert server.download_called is True
    assert isinstance(partial, Block)
    assert partial.data == b"C"
    assert partial.indices == [1]


def test_when_decoding_then_retrieves_blocks_in_index_order():
    local_blocks = {
        1: [Block(1, 1, [1], b"A")],
        2: [Block(2, 2, [1, 2], xor_bytes(b"A", b"B"))],
    }
    decoder = Decode(
        servers=[], polynomials=[], local_blocks=local_blocks, local_mac=[]
    )

    assert decoder.decode() == b"AB"
