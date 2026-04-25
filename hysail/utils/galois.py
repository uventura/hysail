import numpy as np
import secrets

from hysail.constant import POLYNOMIAL_LAMBDA
from hysail.utils.decorators import timeit

def bytes_to_poly_coeffs(message_block):
    bits = np.unpackbits(np.frombuffer(message_block, dtype=np.uint8))
    # Reverse to align index with power of x (index 0 = x^0)
    return bits[::-1].astype(int)


def _poly_coeffs_to_int(coeffs):
    value = 0
    for index, coeff in enumerate(coeffs):
        if int(coeff):
            value |= 1 << index
    return value


def _int_to_poly_coeffs(value, width):
    if width <= 0:
        return np.array([], dtype=np.uint8)

    return np.array([(value >> index) & 1 for index in range(width)], dtype=np.uint8)


def gf2_poly_mod(m_coeffs, p_coeffs):
    """
    Performs polynomial division m(x) % p(x) over GF(2).
    In GF(2), addition and subtraction are both XOR.
    """
    dividend_coeffs = list(m_coeffs)
    divisor_coeffs = list(p_coeffs)

    while divisor_coeffs and divisor_coeffs[-1] == 0:
        divisor_coeffs.pop()

    if not divisor_coeffs:
        raise ZeroDivisionError("Division by zero polynomial.")

    dividend = _poly_coeffs_to_int(dividend_coeffs)
    divisor = _poly_coeffs_to_int(divisor_coeffs)
    divisor_degree = divisor.bit_length() - 1
    current_dividend = dividend

    while current_dividend.bit_length() > divisor_degree:
        shift = current_dividend.bit_length() - divisor.bit_length()
        current_dividend ^= divisor << shift

    remainder_width = min(len(dividend_coeffs), len(divisor_coeffs) - 1)
    return _int_to_poly_coeffs(current_dividend, remainder_width)


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
