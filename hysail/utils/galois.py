import numpy as np
import secrets

from hysail.constant import POLYNOMIAL_LAMBDA
from hysail.utils.decorators import timeit

def bytes_to_poly_coeffs(message_block):
    bits = np.unpackbits(np.frombuffer(message_block, dtype=np.uint8))
    # Reverse to align index with power of x (index 0 = x^0)
    return bits[::-1].astype(int)


@timeit(runs=6)
def gf2_poly_mod(m_coeffs, p_coeffs):
    """
    Performs polynomial division m(x) % p(x) over GF(2).
    In GF(2), addition and subtraction are both XOR.
    """
    m = list(m_coeffs)
    p = list(p_coeffs)
    # print(f"M: {m}; P: {p}")

    while p and p[-1] == 0:
        p.pop()

    if not p:
        raise ZeroDivisionError("Division by zero polynomial.")

    while len(m) >= len(p):
        if m[-1] == 1:
            for i in range(len(p)):
                m[len(m) - len(p) + i] ^= p[i]
        m.pop()
    return np.array(m)


def generate_challenge_polynomial(degree=POLYNOMIAL_LAMBDA):
    """
    Generates a random polynomial to serve as a challenge P_j(x).
    Note: For true Hy-SAIL security, this should be a verified
    Primitive Polynomial, but a random odd polynomial is a starting point.
    """
    coeffs = [secrets.randbelow(2) for _ in range(degree + 1)]
    # Ensure the polynomial is at the target degree and non-zero at the constant
    coeffs[0] = 1
    coeffs[-1] = 1
    return np.array(coeffs)
