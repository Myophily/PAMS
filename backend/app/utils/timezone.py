"""
Timezone utilities for Korea (Seoul) timezone handling.

All datetime operations in this application use KST (Asia/Seoul) timezone.
"""

from datetime import datetime, date
from zoneinfo import ZoneInfo
from typing import Union

# Constant for Seoul timezone
SEOUL_TZ = ZoneInfo("Asia/Seoul")


def now_kst() -> datetime:
    """
    Get current datetime in KST timezone (aware).

    Replaces: datetime.now() and datetime.utcnow()

    Returns:
        datetime: Timezone-aware datetime in Asia/Seoul

    Example:
        >>> now = now_kst()
        >>> now.tzinfo
        ZoneInfo(key='Asia/Seoul')
        >>> now
        datetime(2024, 1, 15, 14, 30, 0, tzinfo=ZoneInfo(key='Asia/Seoul'))
    """
    return datetime.now(SEOUL_TZ)


def now_kst_truncated() -> datetime:
    """
    Get current KST datetime with minute precision (seconds/microseconds = 0).

    Replaces: datetime.now().replace(second=0, microsecond=0)

    Returns:
        datetime: Timezone-aware datetime truncated to minutes

    Example:
        >>> now = now_kst_truncated()
        >>> now.second
        0
        >>> now.microsecond
        0
    """
    return datetime.now(SEOUL_TZ).replace(second=0, microsecond=0)


def today_kst() -> date:
    """
    Get today's date in KST timezone.

    Replaces: date.today()

    Important: This ensures "today" is always in KST timezone, regardless of
    system timezone. For example, at 2AM UTC (11AM KST), system's date.today()
    might differ from KST's today.

    Returns:
        date: Today's date in KST timezone

    Example:
        >>> today = today_kst()
        >>> today
        date(2024, 1, 15)
    """
    return now_kst().date()


def make_kst_aware(dt: datetime) -> datetime:
    """
    Convert naive datetime to KST-aware datetime.
    Assumes naive datetime is already in KST (no UTC conversion).

    Args:
        dt: Naive datetime object

    Returns:
        datetime: Timezone-aware datetime in Asia/Seoul

    Raises:
        ValueError: If datetime is already timezone-aware

    Example:
        >>> naive = datetime(2024, 1, 15, 14, 30)
        >>> aware = make_kst_aware(naive)
        >>> aware.tzinfo
        ZoneInfo(key='Asia/Seoul')
        >>> aware.hour
        14
    """
    if dt.tzinfo is not None:
        raise ValueError("Datetime is already timezone-aware")
    return dt.replace(tzinfo=SEOUL_TZ)


def date_to_kst_datetime(d: date, hour: int = 0, minute: int = 0) -> datetime:
    """
    Convert date object to KST-aware datetime.

    Args:
        d: Date object
        hour: Hour (0-23), default 0
        minute: Minute (0-59), default 0

    Returns:
        datetime: Timezone-aware datetime in Asia/Seoul

    Example:
        >>> d = date(2024, 1, 15)
        >>> dt = date_to_kst_datetime(d, hour=9, minute=0)
        >>> dt
        datetime(2024, 1, 15, 9, 0, tzinfo=ZoneInfo(key='Asia/Seoul'))
    """
    return datetime(d.year, d.month, d.day, hour, minute, tzinfo=SEOUL_TZ)


def kst_to_date(dt: datetime) -> date:
    """
    Extract date from KST datetime (for comparison with date-only fields).

    Args:
        dt: Timezone-aware datetime

    Returns:
        date: Date object

    Example:
        >>> dt = now_kst()
        >>> d = kst_to_date(dt)
        >>> d
        date(2024, 1, 15)
    """
    return dt.date()


def parse_iso_to_kst(iso_string: str) -> datetime:
    """
    Parse ISO 8601 string from frontend to KST-aware datetime.
    Assumes frontend sends naive strings that represent KST.

    Args:
        iso_string: ISO format datetime string (e.g., "2024-01-15T14:30")

    Returns:
        datetime: Timezone-aware datetime in Asia/Seoul

    Example:
        >>> dt = parse_iso_to_kst("2024-01-15T14:30")
        >>> dt.tzinfo
        ZoneInfo(key='Asia/Seoul')
        >>> dt.hour
        14
    """
    # Remove 'Z' suffix if present (indicates UTC, but we treat as naive KST)
    naive_dt = datetime.fromisoformat(iso_string.replace('Z', ''))
    return make_kst_aware(naive_dt)
