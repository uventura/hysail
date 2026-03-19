import numpy as np

from dataclasses import dataclass


@dataclass
class LocalMac:
    polynomial: np.ndarray
    mac: np.ndarray
