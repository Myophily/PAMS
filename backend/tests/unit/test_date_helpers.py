"""
Unit tests for date_helpers.py - Date validation and business day utilities.

These tests verify transaction date validation, past transaction detection,
business day calculations, and date range generation.
"""

import pytest
from datetime import date, timedelta
from freezegun import freeze_time
from app.utils.date_helpers import (
    validate_transaction_date,
    is_past_transaction,
    get_previous_business_day,
    is_weekend,
    get_date_range,
    format_date_display,
)


# =============================================================================
# TRANSACTION DATE VALIDATION TESTS
# =============================================================================

class TestValidateTransactionDate:
    """Test transaction date validation (cannot be in future)."""

    @freeze_time("2024-01-15")
    def test_today_passes(self):
        """Today's date should pass validation."""
        validate_transaction_date(date(2024, 1, 15))
        # No exception means success

    @freeze_time("2024-01-15")
    def test_past_date_passes(self):
        """Past dates should pass validation."""
        validate_transaction_date(date(2024, 1, 1))
        validate_transaction_date(date(2023, 12, 31))
        validate_transaction_date(date(2020, 1, 1))

    @freeze_time("2024-01-15")
    def test_future_date_fails(self):
        """Future dates should fail validation."""
        future_date = date(2024, 1, 16)
        with pytest.raises(ValueError, match="cannot be in the future"):
            validate_transaction_date(future_date)

    @freeze_time("2024-01-15")
    def test_far_future_fails(self):
        """Far future dates should fail validation."""
        with pytest.raises(ValueError, match="cannot be in the future"):
            validate_transaction_date(date(2099, 12, 31))

    @freeze_time("2024-01-15")
    def test_error_message_includes_dates(self):
        """Error message should include both transaction date and today."""
        with pytest.raises(ValueError, match="2024-01-16.*2024-01-15"):
            validate_transaction_date(date(2024, 1, 16))


# =============================================================================
# PAST TRANSACTION DETECTION TESTS
# =============================================================================

class TestIsPastTransaction:
    """Test detection of past transactions (triggers recalculation)."""

    @freeze_time("2024-01-15")
    def test_past_date_returns_true(self):
        """Dates before today should return True."""
        assert is_past_transaction(date(2024, 1, 14)) is True
        assert is_past_transaction(date(2024, 1, 1)) is True
        assert is_past_transaction(date(2023, 12, 31)) is True

    @freeze_time("2024-01-15")
    def test_today_returns_false(self):
        """Today should return False (not a past transaction)."""
        assert is_past_transaction(date(2024, 1, 15)) is False

    @freeze_time("2024-01-15")
    def test_yesterday_returns_true(self):
        """Yesterday should return True."""
        yesterday = date.today() - timedelta(days=1)
        assert is_past_transaction(yesterday) is True

    @freeze_time("2024-01-15")
    def test_last_week_returns_true(self):
        """Last week should return True."""
        last_week = date.today() - timedelta(days=7)
        assert is_past_transaction(last_week) is True

    @freeze_time("2024-01-15")
    def test_future_returns_false(self):
        """Future dates should return False (though they shouldn't exist)."""
        assert is_past_transaction(date(2024, 1, 16)) is False


# =============================================================================
# BUSINESS DAY CALCULATION TESTS
# =============================================================================

class TestGetPreviousBusinessDay:
    """Test previous business day calculation (excludes weekends)."""

    def test_monday_to_friday(self):
        """Monday should return previous Friday."""
        # 2024-01-08 is Monday
        result = get_previous_business_day(date(2024, 1, 8))
        assert result == date(2024, 1, 5)  # Friday

    def test_friday_to_thursday(self):
        """Friday should return previous Thursday."""
        # 2024-01-05 is Friday
        result = get_previous_business_day(date(2024, 1, 5))
        assert result == date(2024, 1, 4)  # Thursday

    def test_saturday_to_friday(self):
        """Saturday should return previous Friday."""
        # 2024-01-06 is Saturday
        result = get_previous_business_day(date(2024, 1, 6))
        assert result == date(2024, 1, 5)  # Friday

    def test_sunday_to_friday(self):
        """Sunday should return previous Friday."""
        # 2024-01-07 is Sunday
        result = get_previous_business_day(date(2024, 1, 7))
        assert result == date(2024, 1, 5)  # Friday

    def test_tuesday_to_monday(self):
        """Tuesday should return Monday."""
        # 2024-01-09 is Tuesday
        result = get_previous_business_day(date(2024, 1, 9))
        assert result == date(2024, 1, 8)  # Monday

    def test_max_lookback_exceeded(self):
        """Should return None if max_lookback exceeded."""
        # Create scenario where no business day found within lookback
        # This is theoretical - in practice won't happen with default 7 days
        result = get_previous_business_day(date(2024, 1, 5), max_lookback=0)
        assert result is None

    def test_custom_max_lookback(self):
        """Should respect custom max_lookback parameter."""
        # Monday Jan 8 to Friday Jan 5 is 3 days back (need max_lookback >= 3)
        result = get_previous_business_day(date(2024, 1, 8), max_lookback=3)
        assert result == date(2024, 1, 5)  # Friday, within 3 days


# =============================================================================
# WEEKEND DETECTION TESTS
# =============================================================================

class TestIsWeekend:
    """Test weekend detection."""

    def test_saturday_is_weekend(self):
        """Saturday should be weekend."""
        # 2024-01-06 is Saturday
        assert is_weekend(date(2024, 1, 6)) is True

    def test_sunday_is_weekend(self):
        """Sunday should be weekend."""
        # 2024-01-07 is Sunday
        assert is_weekend(date(2024, 1, 7)) is True

    def test_monday_not_weekend(self):
        """Monday should not be weekend."""
        # 2024-01-08 is Monday
        assert is_weekend(date(2024, 1, 8)) is False

    def test_friday_not_weekend(self):
        """Friday should not be weekend."""
        # 2024-01-05 is Friday
        assert is_weekend(date(2024, 1, 5)) is False

    def test_wednesday_not_weekend(self):
        """Wednesday should not be weekend."""
        # 2024-01-10 is Wednesday
        assert is_weekend(date(2024, 1, 10)) is False


# =============================================================================
# DATE RANGE GENERATION TESTS
# =============================================================================

class TestGetDateRange:
    """Test date range generation for snapshot calculations."""

    def test_single_day_range(self):
        """Single day should return list with one date."""
        result = get_date_range(date(2024, 1, 1), date(2024, 1, 1))
        assert result == [date(2024, 1, 1)]

    def test_three_day_range(self):
        """Three day range should return three dates."""
        result = get_date_range(date(2024, 1, 1), date(2024, 1, 3))
        assert result == [
            date(2024, 1, 1),
            date(2024, 1, 2),
            date(2024, 1, 3)
        ]

    def test_one_week_range(self):
        """One week range should return 8 dates (inclusive)."""
        result = get_date_range(date(2024, 1, 1), date(2024, 1, 8))
        assert len(result) == 8
        assert result[0] == date(2024, 1, 1)
        assert result[-1] == date(2024, 1, 8)

    def test_month_boundary(self):
        """Should handle month boundaries correctly."""
        result = get_date_range(date(2024, 1, 30), date(2024, 2, 2))
        assert result == [
            date(2024, 1, 30),
            date(2024, 1, 31),
            date(2024, 2, 1),
            date(2024, 2, 2)
        ]

    def test_year_boundary(self):
        """Should handle year boundaries correctly."""
        result = get_date_range(date(2023, 12, 30), date(2024, 1, 2))
        assert len(result) == 4
        assert result[0] == date(2023, 12, 30)
        assert result[-1] == date(2024, 1, 2)

    def test_leap_year_february(self):
        """Should handle leap year February correctly."""
        result = get_date_range(date(2024, 2, 28), date(2024, 3, 1))
        assert result == [
            date(2024, 2, 28),
            date(2024, 2, 29),  # Leap day
            date(2024, 3, 1)
        ]

    def test_non_leap_year_february(self):
        """Should handle non-leap year February correctly."""
        result = get_date_range(date(2023, 2, 28), date(2023, 3, 1))
        assert result == [
            date(2023, 2, 28),
            date(2023, 3, 1)  # No Feb 29
        ]

    def test_start_after_end_raises_error(self):
        """Start date after end date should raise ValueError."""
        with pytest.raises(ValueError, match="cannot be after"):
            get_date_range(date(2024, 1, 5), date(2024, 1, 1))

    def test_chronological_order(self):
        """Dates should be in chronological order."""
        result = get_date_range(date(2024, 1, 1), date(2024, 1, 10))
        for i in range(len(result) - 1):
            assert result[i] < result[i + 1]


# =============================================================================
# DATE FORMATTING TESTS
# =============================================================================

class TestFormatDateDisplay:
    """Test date formatting for display."""

    def test_format_monday(self):
        """Format Monday."""
        # 2024-01-08 is Monday
        result = format_date_display(date(2024, 1, 8))
        assert result == "2024-01-08 (Mon)"

    def test_format_friday(self):
        """Format Friday."""
        # 2024-01-05 is Friday
        result = format_date_display(date(2024, 1, 5))
        assert result == "2024-01-05 (Fri)"

    def test_format_saturday(self):
        """Format Saturday."""
        # 2024-01-06 is Saturday
        result = format_date_display(date(2024, 1, 6))
        assert result == "2024-01-06 (Sat)"

    def test_format_sunday(self):
        """Format Sunday."""
        # 2024-01-07 is Sunday
        result = format_date_display(date(2024, 1, 7))
        assert result == "2024-01-07 (Sun)"

    def test_format_includes_year(self):
        """Formatted string should include year."""
        result = format_date_display(date(2024, 12, 31))
        assert "2024" in result

    def test_format_includes_day_name(self):
        """Formatted string should include abbreviated day name."""
        result = format_date_display(date(2024, 1, 10))
        assert "(Wed)" in result


# =============================================================================
# INTEGRATION & EDGE CASES
# =============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_new_years_day(self):
        """Test with New Year's Day."""
        # 2024-01-01 is Monday
        assert is_weekend(date(2024, 1, 1)) is False
        prev_day = get_previous_business_day(date(2024, 1, 1))
        # Should skip weekend and get Friday Dec 29
        assert prev_day == date(2023, 12, 29)

    def test_christmas_day_weekend(self):
        """Test when holiday falls on weekend."""
        # 2021-12-25 was Saturday
        assert is_weekend(date(2021, 12, 25)) is True

    @freeze_time("2024-02-29")  # Leap day
    def test_leap_day_validation(self):
        """Test transaction on leap day."""
        validate_transaction_date(date(2024, 2, 29))
        assert is_past_transaction(date(2024, 2, 28)) is True
        assert is_past_transaction(date(2024, 2, 29)) is False

    def test_century_boundary(self):
        """Test dates around century boundary."""
        date_range = get_date_range(date(1999, 12, 31), date(2000, 1, 2))
        assert len(date_range) == 3
        assert date_range[0] == date(1999, 12, 31)
        assert date_range[1] == date(2000, 1, 1)
        assert date_range[2] == date(2000, 1, 2)


class TestIntegrationScenarios:
    """Test realistic multi-function scenarios."""

    @freeze_time("2024-01-15")
    def test_validate_and_check_past(self):
        """Validate a date and check if it's past."""
        transaction_date = date(2024, 1, 10)

        # Should pass validation (not in future)
        validate_transaction_date(transaction_date)

        # Should be detected as past transaction
        assert is_past_transaction(transaction_date) is True

    @freeze_time("2024-01-15")
    def test_today_transaction_workflow(self):
        """Test workflow for today's transaction."""
        today = date.today()

        # Today should pass validation
        validate_transaction_date(today)

        # Today should NOT be past transaction (no recalculation needed)
        assert is_past_transaction(today) is False

    def test_date_range_excluding_weekends(self):
        """Generate date range and filter out weekends."""
        all_dates = get_date_range(date(2024, 1, 5), date(2024, 1, 8))
        # Friday, Saturday, Sunday, Monday

        business_days = [d for d in all_dates if not is_weekend(d)]
        assert business_days == [
            date(2024, 1, 5),  # Friday
            date(2024, 1, 8)   # Monday
        ]

    def test_previous_business_day_chain(self):
        """Get multiple previous business days in sequence."""
        # Start from Wednesday 2024-01-10
        day1 = get_previous_business_day(date(2024, 1, 10))
        assert day1 == date(2024, 1, 9)  # Tuesday

        day2 = get_previous_business_day(day1)
        assert day2 == date(2024, 1, 8)  # Monday

        day3 = get_previous_business_day(day2)
        assert day3 == date(2024, 1, 5)  # Friday (skips weekend)

    @freeze_time("2024-01-15")
    def test_snapshot_generation_date_range(self):
        """Simulate snapshot generation for past week."""
        end_date = date.today()
        start_date = end_date - timedelta(days=7)

        # Validate dates
        validate_transaction_date(start_date)
        validate_transaction_date(end_date)

        # Generate date range
        dates = get_date_range(start_date, end_date)
        assert len(dates) == 8  # 7 days + today

        # Filter business days only
        business_days = [d for d in dates if not is_weekend(d)]
        assert len(business_days) >= 5  # At least 5 business days in a week
