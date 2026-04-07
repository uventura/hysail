import numpy as np
import random


def xor_bytes(a, b):
    return bytes(x ^ y for x, y in zip(a, b))


def robust_soliton_distribution(K, c=0.1, delta=0.2):
    """
    Creates the probability distribution for picking the degree of each packet.
    """

    def _soliton_distribution(K):
        distribution = np.zeros(K + 1)
        distribution[1] = 1 / K
        for i in range(2, K + 1):
            distribution[i] = 1 / (i * (i - 1))
        return distribution

    def _tau_function(K, c, delta):
        S = c * np.log(K / delta) * np.sqrt(K)
        pos_step = int(np.floor(K / S))
        tau = np.zeros(K + 1)
        for i in range(1, pos_step):
            tau[i] = S / (K * i)
        tau[pos_step] = (S / K) * np.log(S / delta)
        return tau

    def _combine_and_normalize(rho, tau):
        Z = np.sum(rho + tau)
        return (rho + tau) / Z

    rho = _soliton_distribution(K)
    tau = _tau_function(K, c, delta)
    return _combine_and_normalize(rho, tau)
