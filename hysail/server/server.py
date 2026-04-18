import glob
import pickle
import shutil
from pathlib import Path

import hysail.utils.galois as ga


class Server:
    def __init__(self, storage_location: str):
        self._storage_location = storage_location
        Path(self._storage_location).mkdir(parents=True, exist_ok=True)

    def storage_check_block(self, check_block):
        source_path = Path(check_block)
        destination_path = Path(self._storage_location) / source_path.name
        shutil.copyfile(source_path, destination_path)

    def download_block(self, block_index):
        block_path = self._find_check_block(block_index)
        if block_path is None:
            raise ValueError("Check block not found")

        return self._read_block_data(block_path)

    def receive_challenge(self, polynomial, check_block_index):
        block_path = self._find_check_block(check_block_index)
        if block_path is None:
            raise ValueError("Check block not found")

        response = self._compute_response(polynomial, block_path)
        return response

    def _find_check_block(self, check_block_index):
        pattern = str(
            Path(self._storage_location) / f"*_packet_{check_block_index}.pkl"
        )
        matches = glob.glob(pattern)
        return matches[0] if matches else None

    def _compute_response(self, polynomial, block_path):
        data = self._read_block_data(block_path)
        coefs = ga.bytes_to_poly_coeffs(data)
        return ga.gf2_poly_mod(coefs, polynomial)

    def _read_block_data(self, block_path):
        with open(block_path, "rb") as file:
            try:
                payload = pickle.load(file)
            except (pickle.UnpicklingError, EOFError):
                file.seek(0)
                return file.read()

        if hasattr(payload, "data"):
            return payload.data

        return payload
