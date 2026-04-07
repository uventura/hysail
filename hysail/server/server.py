import hysail.utils.galois as ga


class Server:
    def __init__(self):
        self._check_blocks = []

    def storage_check_block(self, check_block):
        self._check_blocks.append(check_block)

    def download_block(self, block_index):
        check_block = self._find_check_block(block_index)
        if check_block is None:
            raise ValueError("Check block not found")

        return check_block.data

    def receive_challenge(self, polynomial, check_block_index):
        check_block = self._find_check_block(check_block_index)
        if check_block is None:
            raise ValueError("Check block not found")

        response = self._compute_response(polynomial, check_block)
        return response

    def _find_check_block(self, check_block_index):
        for check_block in self._check_blocks:
            if check_block_index == check_block.index:
                return check_block
        return None

    def _compute_response(self, polynomial, check_block):
        coefs = ga.bytes_to_poly_coeffs(check_block.data)
        # print(f"Input: {check_block.data}; Coeficients: {coefs}")
        return ga.gf2_poly_mod(coefs, polynomial)
