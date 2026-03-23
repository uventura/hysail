import numpy as np

from dataclasses import dataclass


@dataclass
class LocalMac:
    mac: np.ndarray
    polynomial_index: np.ndarray
    block_index: int
