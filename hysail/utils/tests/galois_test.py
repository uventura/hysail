import numpy as np

from hysail.utils.galois import (
    bytes_to_poly_coeffs,
    gf2_poly_mod,
    generate_challenge_polynomial,
)


######################################
# Tests: bytes_to_poly_coeffs
######################################
def test_when_converting_bytes_to_poly_then_coefficients_are_binary_mapped():
    msg = b"\x0a"
    result = bytes_to_poly_coeffs(msg)
    expected = np.array([0, 1, 0, 1, 0, 0, 0, 0])
    np.testing.assert_array_equal(result, expected)


######################################
# Tests: gf2_poly_mod
######################################
def test_when_message_is_identical_to_primitive_then_mac_is_empty():
    m_x = np.array([1, 0, 1, 1])
    p_x = np.array([1, 0, 1, 1])
    mac = gf2_poly_mod(m_x, p_x)
    assert len(mac) == 0 or np.all(mac == 0)


######################################
# Tests: generate_challenge_polynomial
######################################
def test_when_degree_is_provided_then_output_length_is_correct():
    """
    The polynomial array length should be degree + 1 to include the
    constant term (x^0) up to x^degree.
    """
    degree = 127  # Standard Hy-SAIL security parameter [cite: 291]
    poly = generate_challenge_polynomial(degree)
    print(f"Len: {len(poly)}")
    assert len(poly) == degree + 1


def test_when_polynomial_is_generated_then_coefficients_are_binary():
    """
    Hy-SAIL operates in GF(2), so all coefficients must be 0 or 1[cite: 225].
    """
    degree = 16
    poly = generate_challenge_polynomial(degree)
    assert np.all((poly == 0) | (poly == 1))


def test_when_challenge_is_created_then_it_is_highest_degree():
    """
    The coefficient of the highest power (x^degree) must be 1 to
    ensure the polynomial actually has that degree[cite: 118].
    """
    degree = 127
    poly = generate_challenge_polynomial(degree)
    assert poly[-1] == 1


def test_when_challenge_is_created_then_constant_term_is_non_zero():
    """
    For primitive polynomials used in MACs, the constant term (x^0)
    is typically 1 to ensure it doesn't simply divide by x[cite: 118].
    """
    degree = 127
    poly = generate_challenge_polynomial(degree)
    assert poly[0] == 1


def test_when_multiple_challenges_generated_then_they_are_randomly_distributed():
    """
    Hy-SAIL requires uniform selection from the set of primitive
    polynomials to maintain the 2-UHF security property[cite: 290, 298].
    """
    degree = 64
    poly1 = generate_challenge_polynomial(degree)
    poly2 = generate_challenge_polynomial(degree)
    # Probability of two random 64-degree polynomials being identical is negligible
    assert not np.array_equal(poly1, poly2)


######################################
# def test_when_verifying_homomorphic_property_then_xor_sum_matches_mac_sum():
#     """
#     Validates the core Hy-SAIL property: f(m1) ⊕ f(m2) = f(m1 ⊕ m2).
#     This allows verifying check blocks without the original message[cite: 211, 231].
#     """
#     p_j = np.array([1, 1, 1])  # The challenge Pj(x) [cite: 230]
#     m1 = np.array([1, 1, 0, 1])
#     m2 = np.array([0, 1, 1, 1])

#     # Calculate individual MACs [cite: 234]
#     mac1 = gf2_poly_mod(m1, p_j)
#     mac2 = gf2_poly_mod(m2, p_j)

#     # Calculate MAC of the XORed block [cite: 238, 242]
#     combined_msg = m1 ^ m2
#     mac_combined = gf2_poly_mod(combined_msg, p_j)

#     # XOR the MACs together [cite: 243]
#     # Pad for equal length before XORing
#     max_len = max(len(mac1), len(mac2))
#     mac1_p = np.pad(mac1, (0, max_len - len(mac1)))
#     mac2_p = np.pad(mac2, (0, max_len - len(mac2)))
#     sum_of_macs = np.trim_zeros(mac1_p ^ mac2_p, 'b')

#     np.testing.assert_array_equal(mac_combined, sum_of_macs)

# def test_when_redistribution_occurs_then_reconstructed_block_is_mathematically_valid():
#     """
#     Tests if a lost check block can be reconstructed using XOR
#     operations on remaining blocks[cite: 401, 405].
#     """
#     # Simulate: Check Block C3 = M1 ^ M2
#     m1 = np.array([1, 0, 1])
#     m2 = np.array([0, 1, 1])
#     c3_original = m1 ^ m2

#     # In Redistribution, we reconstruct the block [cite: 405]
#     c3_reconstructed = m1 ^ m2

#     np.testing.assert_array_equal(c3_reconstructed, c3_original)
