"""
Decimal helper utilities for safe monetary calculations.

CRITICAL: Always use Decimal for monetary values to avoid floating point precision errors.
"""

from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from typing import Union


def to_decimal(value: Union[int, float, str, Decimal], precision: int = 2) -> Decimal:
    """
    Safely convert a value to Decimal with specified precision.

    Args:
        value: Value to convert (int, float, str, or Decimal)
        precision: Number of decimal places (default: 2 for money, 4 for exchange rates, 8 for quantities)

    Returns:
        Decimal with specified precision

    Raises:
        ValueError: If conversion fails

    Examples:
        >>> to_decimal(1500.00)
        Decimal('1500.00')

        >>> to_decimal("1234.5678", precision=4)
        Decimal('1234.5678')

        >>> to_decimal(100, precision=2)
        Decimal('100.00')
    """
    if isinstance(value, Decimal):
        return value.quantize(Decimal(10) ** -precision, rounding=ROUND_HALF_UP)

    try:
        # Convert to string first to avoid float precision issues
        d = Decimal(str(value))
        return d.quantize(Decimal(10) ** -precision, rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError) as e:
        raise ValueError(f"Cannot convert {value} to Decimal: {e}")


def validate_positive(value: Decimal, field_name: str = "Value") -> None:
    """
    Validate that a Decimal value is positive (> 0).

    Args:
        value: Decimal value to validate
        field_name: Name of the field for error message

    Raises:
        ValueError: If value is not positive

    Examples:
        >>> validate_positive(Decimal("100.00"), "Amount")
        # No error

        >>> validate_positive(Decimal("0"), "Amount")
        ValueError: Amount must be positive

        >>> validate_positive(Decimal("-50"), "Price")
        ValueError: Price must be positive
    """
    if value <= 0:
        raise ValueError(f"{field_name} must be positive (got {value})")


def validate_non_negative(value: Decimal, field_name: str = "Value") -> None:
    """
    Validate that a Decimal value is non-negative (>= 0).

    Args:
        value: Decimal value to validate
        field_name: Name of the field for error message

    Raises:
        ValueError: If value is negative

    Examples:
        >>> validate_non_negative(Decimal("0"), "Balance")
        # No error

        >>> validate_non_negative(Decimal("100"), "Balance")
        # No error

        >>> validate_non_negative(Decimal("-10"), "Balance")
        ValueError: Balance cannot be negative
    """
    if value < 0:
        raise ValueError(f"{field_name} cannot be negative (got {value})")


def validate_non_zero(value: Decimal, field_name: str = "Value") -> None:
    """
    Validate that a Decimal value is not zero.

    Args:
        value: Decimal value to validate
        field_name: Name of the field for error message

    Raises:
        ValueError: If value is zero

    Examples:
        >>> validate_non_zero(Decimal("100"), "Amount")
        # No error

        >>> validate_non_zero(Decimal("0"), "Amount")
        ValueError: Amount cannot be zero
    """
    if value == 0:
        raise ValueError(f"{field_name} cannot be zero")


def safe_divide(numerator: Decimal, denominator: Decimal, precision: int = 4) -> Decimal:
    """
    Safely divide two Decimal values, handling division by zero.

    Args:
        numerator: Dividend
        denominator: Divisor
        precision: Number of decimal places for result

    Returns:
        Result of division, or Decimal("0") if denominator is zero

    Examples:
        >>> safe_divide(Decimal("100"), Decimal("4"))
        Decimal('25.0000')

        >>> safe_divide(Decimal("100"), Decimal("0"))
        Decimal('0.0000')

        >>> safe_divide(Decimal("10"), Decimal("3"), precision=2)
        Decimal('3.33')
    """
    if denominator == 0:
        return Decimal("0").quantize(Decimal(10) ** -precision)

    result = numerator / denominator
    return result.quantize(Decimal(10) ** -precision, rounding=ROUND_HALF_UP)


def format_currency(value: Decimal, currency: str = "KRW") -> str:
    """
    Format a Decimal value as currency string.

    Args:
        value: Decimal value to format
        currency: Currency code (KRW, USD, etc.)

    Returns:
        Formatted currency string

    Examples:
        >>> format_currency(Decimal("1500000"), "KRW")
        '1,500,000.00 KRW'

        >>> format_currency(Decimal("1234.56"), "USD")
        '1,234.56 USD'
    """
    # Format with thousand separators and 2 decimal places
    formatted = f"{value:,.2f}"
    return f"{formatted} {currency}"
