"""
Date validation and business day utilities for transaction processing.

CRITICAL: Transaction dates cannot be in the future. Past transactions trigger recalculation.
"""

from datetime import datetime, date, timedelta
from typing import Optional, Union


def get_current_datetime_truncated() -> datetime:
    """Get current datetime with minute precision (seconds/microseconds = 0)."""
    return datetime.now().replace(second=0, microsecond=0)


def validate_transaction_date(transaction_date: Union[date, datetime]) -> None:
    """
    Validate that a transaction date or datetime is not in the future.

    Args:
        transaction_date: Date or datetime to validate (datetime uses minute precision)

    Raises:
        ValueError: If date/datetime is in the future

    Examples:
        >>> validate_transaction_date(date(2024, 1, 1))  # Past date
        # No error

        >>> validate_transaction_date(datetime(2024, 1, 1, 10, 30))  # Past datetime
        # No error

        >>> validate_transaction_date(date(2099, 12, 31))  # Future date
        ValueError: Transaction date 2099-12-31 cannot be in the future

        >>> validate_transaction_date(datetime(2099, 12, 31, 10, 30))  # Future datetime
        ValueError: Transaction datetime 2099-12-31 10:30:00 cannot be in the future
    """
    now = datetime.now().replace(second=0, microsecond=0)

    # Handle date-only objects (compare dates, not datetimes)
    if isinstance(transaction_date, date) and not isinstance(transaction_date, datetime):
        today = now.date()
        if transaction_date > today:
            raise ValueError(
                f"Transaction date {transaction_date} cannot be in the future (today is {today})"
            )
        return

    # Handle datetime objects (compare minute precision)
    transaction_dt = transaction_date.replace(second=0, microsecond=0)
    if transaction_dt > now:
        raise ValueError(
            f"Transaction datetime {transaction_dt} cannot be in the future (now is {now})"
        )


def is_past_transaction(transaction_date: Union[date, datetime]) -> bool:
    """
    Check if a transaction date/datetime is before current time.

    Used to determine if recalculation needs to be triggered.

    Args:
        transaction_date: Date or datetime to check (datetime uses minute precision)

    Returns:
        True if date/datetime is before current time, False otherwise

    Examples:
        >>> is_past_transaction(date(2024, 1, 1))
        True  # Assuming now is later than 2024-01-01

        >>> is_past_transaction(datetime(2024, 1, 1, 10, 30))
        True  # Assuming now is later than 2024-01-01 10:30

        >>> is_past_transaction(datetime.now())
        False  # Current time is not a past transaction

        >>> is_past_transaction(datetime.now() - timedelta(hours=1))
        True  # One hour ago is a past transaction
    """
    now = datetime.now().replace(second=0, microsecond=0)

    # Handle date-only objects
    if isinstance(transaction_date, date) and not isinstance(transaction_date, datetime):
        return transaction_date < now.date()

    # Handle datetime objects (include current minute to trigger recalculation)
    return transaction_date.replace(second=0, microsecond=0) <= now


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
