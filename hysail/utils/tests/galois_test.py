import numpy as np

from hysail.utils.galois import (
    bytes_to_poly_coeffs,
    gf2_poly_mod,
    generate_challenge_polynomial,
)


def test_when_converting_bytes_to_poly_then_coefficients_are_binary_mapped():
    msg = b"\x0a"
    result = bytes_to_poly_coeffs(msg)
    expected = np.array([0, 1, 0, 1, 0, 0, 0, 0])
    np.testing.assert_array_equal(result, expected)


def test_when_message_is_identical_to_primitive_then_mac_is_empty():
    m_x = np.array([1, 0, 1, 1])
    p_x = np.array([1, 0, 1, 1])
    mac = gf2_poly_mod(m_x, p_x)
    np.testing.assert_array_equal(mac, np.array([0, 0, 0], dtype=np.uint8))


def test_gf2_poly_mod_returns_expected_remainder_for_known_division():
    m_x = np.array([1, 1, 0, 1])
    p_x = np.array([1, 1, 1])

    mac = gf2_poly_mod(m_x, p_x)

    np.testing.assert_array_equal(mac, np.array([0, 1], dtype=np.uint8))


def test_gf2_poly_mod_preserves_remainder_width_for_zero_dividend():
    m_x = np.array([0, 0, 0], dtype=np.uint8)
    p_x = np.array([1, 1], dtype=np.uint8)

    mac = gf2_poly_mod(m_x, p_x)

    np.testing.assert_array_equal(mac, np.array([0], dtype=np.uint8))


def test_when_degree_is_provided_then_output_length_is_correct():
    degree = 127
    poly = generate_challenge_polynomial(degree)
    print(f"Len: {len(poly)}")
    assert len(poly) == degree + 1


def test_when_polynomial_is_generated_then_coefficients_are_binary():
    degree = 16
    poly = generate_challenge_polynomial(degree)
    assert np.all((poly == 0) | (poly == 1))


def test_when_challenge_is_created_then_it_is_highest_degree():
    degree = 127
    poly = generate_challenge_polynomial(degree)
    assert poly[-1] == 1


def test_when_challenge_is_created_then_constant_term_is_non_zero():
    degree = 127
    poly = generate_challenge_polynomial(degree)
    assert poly[0] == 1


def test_when_multiple_challenges_generated_then_they_are_randomly_distributed():
    degree = 64
    poly1 = generate_challenge_polynomial(degree)
    poly2 = generate_challenge_polynomial(degree)
    assert not np.array_equal(poly1, poly2)
