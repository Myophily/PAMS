"""
Date validation and business day utilities for transaction processing.

CRITICAL: Transaction dates cannot be in the future. Past transactions trigger recalculation.
"""

from datetime import date, timedelta
from typing import Optional


def validate_transaction_date(transaction_date: date) -> None:
    """
    Validate that a transaction date is not in the future.

    Args:
        transaction_date: Date to validate

    Raises:
        ValueError: If date is in the future

    Examples:
        >>> validate_transaction_date(date(2024, 1, 1))  # Past date
        # No error

        >>> validate_transaction_date(date.today())  # Today
        # No error

        >>> validate_transaction_date(date(2099, 12, 31))  # Future date
        ValueError: Transaction date 2099-12-31 cannot be in the future
    """
    today = date.today()
    if transaction_date > today:
        raise ValueError(
            f"Transaction date {transaction_date} cannot be in the future (today is {today})"
        )


def is_past_transaction(transaction_date: date) -> bool:
    """
    Check if a transaction date is before today.

    Used to determine if recalculation needs to be triggered.

    Args:
        transaction_date: Date to check

    Returns:
        True if date is before today, False otherwise

    Examples:
        >>> is_past_transaction(date(2024, 1, 1))
        True  # Assuming today is later than 2024-01-01

        >>> is_past_transaction(date.today())
        False  # Today is not a past transaction

        >>> is_past_transaction(date.today() - timedelta(days=1))
        True  # Yesterday is a past transaction
    """
    return transaction_date < date.today()


def get_previous_business_day(target_date: date, max_lookback: int = 7) -> Optional[date]:
    """
    Get the previous business day (excludes weekends only).

    For MVP, we don't handle market holidays. We only exclude Saturday (5) and Sunday (6).

    Args:
        target_date: Date to find previous business day for
        max_lookback: Maximum days to look back (default: 7)

    Returns:
        Previous business day, or None if not found within max_lookback

    Examples:
        >>> get_previous_business_day(date(2024, 1, 8))  # Monday
        date(2024, 1, 5)  # Previous Friday

        >>> get_previous_business_day(date(2024, 1, 7))  # Sunday
        date(2024, 1, 5)  # Previous Friday

        >>> get_previous_business_day(date(2024, 1, 6))  # Saturday
        date(2024, 1, 5)  # Previous Friday

        >>> get_previous_business_day(date(2024, 1, 5))  # Friday
        date(2024, 1, 4)  # Previous Thursday
    """
    for i in range(1, max_lookback + 1):
        prev_date = target_date - timedelta(days=i)
        # weekday(): Monday=0, Tuesday=1, ..., Saturday=5, Sunday=6
        if prev_date.weekday() < 5:  # Monday-Friday (0-4)
            return prev_date
    return None


def is_weekend(target_date: date) -> bool:
    """
    Check if a date is a weekend (Saturday or Sunday).

    Args:
        target_date: Date to check

    Returns:
        True if weekend, False otherwise

    Examples:
        >>> is_weekend(date(2024, 1, 6))  # Saturday
        True

        >>> is_weekend(date(2024, 1, 7))  # Sunday
        True

        >>> is_weekend(date(2024, 1, 8))  # Monday
        False
    """
    return target_date.weekday() >= 5  # Saturday=5, Sunday=6


def get_date_range(start_date: date, end_date: date) -> list[date]:
    """
    Get a list of all dates between start_date and end_date (inclusive).

    Args:
        start_date: Start date
        end_date: End date

    Returns:
        List of dates from start_date to end_date

    Raises:
        ValueError: If start_date is after end_date

    Examples:
        >>> get_date_range(date(2024, 1, 1), date(2024, 1, 3))
        [date(2024, 1, 1), date(2024, 1, 2), date(2024, 1, 3)]

        >>> get_date_range(date(2024, 1, 1), date(2024, 1, 1))
        [date(2024, 1, 1)]
    """
    if start_date > end_date:
        raise ValueError(f"start_date {start_date} cannot be after end_date {end_date}")

    dates = []
    current_date = start_date
    while current_date <= end_date:
        dates.append(current_date)
        current_date += timedelta(days=1)

    return dates


def format_date_display(target_date: date) -> str:
    """
    Format a date for display (e.g., "2024-01-15 (Mon)").

    Args:
        target_date: Date to format

    Returns:
        Formatted date string

    Examples:
        >>> format_date_display(date(2024, 1, 15))
        '2024-01-15 (Mon)'
    """
    day_name = target_date.strftime("%a")  # Mon, Tue, Wed, etc.
    return f"{target_date} ({day_name})"
