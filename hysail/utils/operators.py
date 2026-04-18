import numpy as np


def xor_bytes(a, b):
    return bytes(x ^ y for x, y in zip(a, b))


def robust_soliton_distribution(K, c=0.2, delta=0.01):
    # """
    # Creates the probability distribution for picking the degree of each packet.
    # """

    # def _soliton_distribution(K):
    #     distribution = np.zeros(K + 1)
    #     distribution[1] = 1 / K
    #     for i in range(2, K + 1):
    #         distribution[i] = 1 / (i * (i - 1))
    #     return distribution

    # def _tau_function(K, c, delta):
    #     S = c * np.log(K / delta) * np.sqrt(K)
    #     pos_step = int(np.floor(K / S))
    #     tau = np.zeros(K + 1)
    #     for i in range(1, pos_step):
    #         tau[i] = S / (K * i)
    #     tau[pos_step] = (S / K) * np.log(S / delta)
    #     return tau

    # def _combine_and_normalize(rho, tau):
    #     Z = np.sum(rho + tau)
    #     return (rho + tau) / Z

    # rho = _soliton_distribution(K)
    # tau = _tau_function(K, c, delta)
    # return _combine_and_normalize(rho, tau)
    """
    K: Number of source symbols
    c: Constant > 0 (usually 0.1 to 0.2)
    delta: Desired failure probability (e.g., 0.05 for 5%)
    """
    # 1. Calculate the 'ripple' size parameter
    R = c * np.log(K / delta) * np.sqrt(K)

    # 2. Ideal Soliton Distribution (rho)
    rho = np.zeros(K + 1)
    rho[1] = 1 / K
    for i in range(2, K + 1):
        rho[i] = 1 / (i * (i - 1))

    # 3. The Robust 'Redundancy' Component (tau)
    tau = np.zeros(K + 1)
    M = int(np.floor(K / R))  # The 'Spike' location

    for i in range(1, M):
        tau[i] = R / (i * K)

    # The spike at M ensures there is always a Degree-1 symbol available
    tau[M] = (R * np.log(R / delta)) / K

    # 4. Normalization (to make probabilities sum to 1)
    beta = np.sum(rho + tau)
    mu = (rho + tau) / beta

    return mu
