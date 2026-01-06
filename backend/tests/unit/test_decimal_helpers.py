"""
Unit tests for decimal_helpers.py - Safe decimal conversion and validation.

These tests verify decimal conversion, validation functions, and safe division
to ensure monetary calculations maintain precision and handle edge cases.
"""

import pytest
from decimal import Decimal, InvalidOperation
from app.utils.decimal_helpers import (
    to_decimal,
    validate_positive,
    validate_non_negative,
    validate_non_zero,
    safe_divide,
    format_currency,
)


# =============================================================================
# DECIMAL CONVERSION TESTS
# =============================================================================

class TestToDecimal:
    """Test safe conversion to Decimal with precision control."""

    def test_convert_int(self):
        """Convert integer to Decimal."""
        result = to_decimal(100, precision=2)
        assert result == Decimal("100.00")
        assert isinstance(result, Decimal)

    def test_convert_float(self):
        """Convert float to Decimal (string intermediate to avoid precision loss)."""
        result = to_decimal(1500.00, precision=2)
        assert result == Decimal("1500.00")

    def test_convert_string(self):
        """Convert string to Decimal."""
        result = to_decimal("1234.5678", precision=4)
        assert result == Decimal("1234.5678")

    def test_convert_decimal(self):
        """Convert existing Decimal with precision adjustment."""
        input_decimal = Decimal("99.999")
        result = to_decimal(input_decimal, precision=2)
        assert result == Decimal("100.00")  # Rounded up

    def test_precision_2_decimal_places(self):
        """Default precision should be 2 decimal places for money."""
        result = to_decimal("1234.567")
        assert result == Decimal("1234.57")  # Rounded
        assert result.as_tuple().exponent == -2

    def test_precision_4_decimal_places(self):
        """Precision 4 for exchange rates."""
        result = to_decimal("1.23456789", precision=4)
        assert result == Decimal("1.2346")  # Rounded
        assert result.as_tuple().exponent == -4

    def test_precision_8_decimal_places(self):
        """Precision 8 for quantities."""
        result = to_decimal("10.123456789", precision=8)
        assert result == Decimal("10.12345679")  # Rounded
        assert result.as_tuple().exponent == -8

    def test_rounding_half_up(self):
        """Should use ROUND_HALF_UP rounding mode."""
        # 1.5 rounds to 2
        assert to_decimal("1.5", precision=0) == Decimal("2")
        # 2.5 rounds to 3
        assert to_decimal("2.5", precision=0) == Decimal("3")
        # 1.125 with precision 2 rounds to 1.13
        assert to_decimal("1.125", precision=2) == Decimal("1.13")

    def test_negative_numbers(self):
        """Handle negative numbers correctly."""
        result = to_decimal("-100.50", precision=2)
        assert result == Decimal("-100.50")

    def test_zero(self):
        """Handle zero correctly."""
        result = to_decimal(0, precision=2)
        assert result == Decimal("0.00")

    def test_invalid_string(self):
        """Invalid string should raise ValueError."""
        with pytest.raises(ValueError, match="Cannot convert"):
            to_decimal("not a number", precision=2)

    def test_none_value(self):
        """None should raise ValueError."""
        with pytest.raises((ValueError, AttributeError)):
            to_decimal(None, precision=2)


# =============================================================================
# VALIDATION TESTS
# =============================================================================

class TestValidatePositive:
    """Test positive value validation (> 0)."""

    def test_positive_value_passes(self):
        """Positive values should pass validation."""
        validate_positive(Decimal("100.00"), "Amount")
        validate_positive(Decimal("0.01"), "Amount")
        # No exception means success

    def test_zero_fails(self):
        """Zero should fail validation."""
        with pytest.raises(ValueError, match="Amount must be positive"):
            validate_positive(Decimal("0"), "Amount")

    def test_negative_fails(self):
        """Negative value should fail validation."""
        with pytest.raises(ValueError, match="Price must be positive"):
            validate_positive(Decimal("-50.00"), "Price")

    def test_custom_field_name(self):
        """Should use custom field name in error message."""
        with pytest.raises(ValueError, match="Quantity must be positive"):
            validate_positive(Decimal("0"), "Quantity")

    def test_very_small_positive(self):
        """Very small positive value should pass."""
        validate_positive(Decimal("0.0001"), "Amount")


class TestValidateNonNegative:
    """Test non-negative value validation (>= 0)."""

    def test_zero_passes(self):
        """Zero should pass validation."""
        validate_non_negative(Decimal("0"), "Balance")
        # No exception means success

    def test_positive_passes(self):
        """Positive values should pass validation."""
        validate_non_negative(Decimal("100.00"), "Balance")
        validate_non_negative(Decimal("0.01"), "Balance")

    def test_negative_fails(self):
        """Negative value should fail validation."""
        with pytest.raises(ValueError, match="Balance cannot be negative"):
            validate_non_negative(Decimal("-10.00"), "Balance")

    def test_custom_field_name(self):
        """Should use custom field name in error message."""
        with pytest.raises(ValueError, match="Quantity cannot be negative"):
            validate_non_negative(Decimal("-1"), "Quantity")


class TestValidateNonZero:
    """Test non-zero value validation."""

    def test_positive_passes(self):
        """Positive values should pass validation."""
        validate_non_zero(Decimal("100.00"), "Amount")
        validate_non_zero(Decimal("0.01"), "Amount")

    def test_negative_passes(self):
        """Negative values should pass validation."""
        validate_non_zero(Decimal("-100.00"), "Amount")

    def test_zero_fails(self):
        """Zero should fail validation."""
        with pytest.raises(ValueError, match="Amount cannot be zero"):
            validate_non_zero(Decimal("0"), "Amount")

    def test_custom_field_name(self):
        """Should use custom field name in error message."""
        with pytest.raises(ValueError, match="Quantity cannot be zero"):
            validate_non_zero(Decimal("0"), "Quantity")


# =============================================================================
# SAFE DIVISION TESTS
# =============================================================================

class TestSafeDivide:
    """Test safe division with zero handling."""

    def test_normal_division(self):
        """Normal division should work correctly."""
        result = safe_divide(Decimal("100"), Decimal("4"), precision=4)
        assert result == Decimal("25.0000")

    def test_division_by_zero_returns_zero(self):
        """Division by zero should return zero instead of error."""
        result = safe_divide(Decimal("100"), Decimal("0"), precision=4)
        assert result == Decimal("0.0000")

    def test_precision_control(self):
        """Should respect precision parameter."""
        # 10 / 3 with precision 2
        result = safe_divide(Decimal("10"), Decimal("3"), precision=2)
        assert result == Decimal("3.33")
        assert result.as_tuple().exponent == -2

    def test_precision_4_decimal_places(self):
        """Default precision should be 4 decimal places."""
        result = safe_divide(Decimal("10"), Decimal("3"))
        assert result == Decimal("3.3333")
        assert result.as_tuple().exponent == -4

    def test_rounding(self):
        """Should use ROUND_HALF_UP for rounding."""
        # 10 / 3 = 3.333... should round to 3.3333
        result = safe_divide(Decimal("10"), Decimal("3"), precision=4)
        assert result == Decimal("3.3333")

        # 1 / 3 with precision 2 = 0.333... should round to 0.33
        result = safe_divide(Decimal("1"), Decimal("3"), precision=2)
        assert result == Decimal("0.33")

    def test_negative_division(self):
        """Should handle negative numbers correctly."""
        result = safe_divide(Decimal("-100"), Decimal("4"), precision=2)
        assert result == Decimal("-25.00")

    def test_zero_numerator(self):
        """Zero divided by anything should be zero."""
        result = safe_divide(Decimal("0"), Decimal("100"), precision=2)
        assert result == Decimal("0.00")


# =============================================================================
# CURRENCY FORMATTING TESTS
# =============================================================================

class TestFormatCurrency:
    """Test currency formatting for display."""

    def test_format_krw(self):
        """Format KRW currency."""
        result = format_currency(Decimal("1500000"), "KRW")
        assert result == "1,500,000.00 KRW"

    def test_format_usd(self):
        """Format USD currency."""
        result = format_currency(Decimal("1234.56"), "USD")
        assert result == "1,234.56 USD"

    def test_format_small_amount(self):
        """Format small amounts."""
        result = format_currency(Decimal("99.99"), "USD")
        assert result == "99.99 USD"

    def test_format_zero(self):
        """Format zero amount."""
        result = format_currency(Decimal("0"), "KRW")
        assert result == "0.00 KRW"

    def test_format_negative(self):
        """Format negative amount."""
        result = format_currency(Decimal("-500.00"), "USD")
        assert result == "-500.00 USD"

    def test_format_large_number(self):
        """Format very large number with thousand separators."""
        result = format_currency(Decimal("1234567890.12"), "USD")
        assert result == "1,234,567,890.12 USD"

    def test_always_two_decimal_places(self):
        """Should always show 2 decimal places."""
        # Integer input
        result = format_currency(Decimal("100"), "KRW")
        assert result == "100.00 KRW"

        # Many decimal places
        result = format_currency(Decimal("100.123456"), "USD")
        assert result == "100.12 USD"  # Truncated/rounded


# =============================================================================
# INTEGRATION & EDGE CASES
# =============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_large_decimal(self):
        """Handle very large decimals."""
        large = Decimal("999999999999.99")
        result = to_decimal(large, precision=2)
        assert result == Decimal("999999999999.99")

    def test_very_small_decimal(self):
        """Handle very small decimals."""
        small = Decimal("0.00000001")
        result = to_decimal(small, precision=8)
        assert result == Decimal("0.00000001")

    def test_scientific_notation(self):
        """Handle scientific notation."""
        result = to_decimal("1.5e3", precision=2)  # 1500
        assert result == Decimal("1500.00")

    def test_precision_chain(self):
        """Test multiple precision conversions."""
        # Start with high precision
        value = to_decimal("100.123456789", precision=8)
        assert value == Decimal("100.12345679")

        # Convert to lower precision
        value = to_decimal(value, precision=2)
        assert value == Decimal("100.12")


class TestValidationCombinations:
    """Test combinations of validations."""

    def test_positive_and_non_zero(self):
        """Value can pass both positive and non-zero checks."""
        value = Decimal("100.00")
        validate_positive(value)
        validate_non_zero(value)

    def test_zero_passes_non_negative_fails_positive(self):
        """Zero should pass non-negative but fail positive."""
        value = Decimal("0")

        validate_non_negative(value)  # Should pass

        with pytest.raises(ValueError):
            validate_positive(value)  # Should fail

    def test_negative_fails_both(self):
        """Negative should fail both positive and non-negative."""
        value = Decimal("-10")

        with pytest.raises(ValueError):
            validate_positive(value)

        with pytest.raises(ValueError):
            validate_non_negative(value)

    def test_division_with_validation(self):
        """Combine safe division with validation."""
        numerator = Decimal("100")
        denominator = Decimal("5")

        # Validate inputs
        validate_positive(numerator)
        validate_positive(denominator)

        # Divide safely
        result = safe_divide(numerator, denominator, precision=2)
        assert result == Decimal("20.00")

        # Validate output
        validate_positive(result)
