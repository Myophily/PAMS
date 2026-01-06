"""
Unit tests for calculation_engine.py - Pure financial calculation functions.

These tests verify the core financial calculations including average price,
profit/loss, and currency conversion functions. All functions are pure
(no database access) and use Decimal for precision.
"""

import pytest
from decimal import Decimal
from app.utils.calculation_engine import (
    calculate_avg_price_on_buy,
    calculate_avg_price_on_sell,
    calculate_unrealized_pl,
    calculate_realized_pl,
    calculate_total_value,
    calculate_cost_basis,
    calculate_exchange_rate,
    convert_currency,
    calculate_weight_percentage,
)


# =============================================================================
# AVERAGE PRICE CALCULATION TESTS
# =============================================================================

class TestAveragePriceOnBuy:
    """Test weighted average price calculation when buying."""

    def test_first_purchase(self):
        """First purchase should set avg_price to buy_price."""
        result = calculate_avg_price_on_buy(
            current_qty=Decimal("0"),
            current_avg=Decimal("0"),
            buy_qty=Decimal("10"),
            buy_price=Decimal("150.00")
        )
        assert result == Decimal("150.0000")

    def test_buy_at_higher_price(self):
        """Buying at higher price should increase weighted average."""
        # Current: 10 shares @ $100
        # Buy: 5 shares @ $120
        # Expected: (10×100 + 5×120) / 15 = 1600 / 15 = $106.6667
        result = calculate_avg_price_on_buy(
            current_qty=Decimal("10"),
            current_avg=Decimal("100.0000"),
            buy_qty=Decimal("5"),
            buy_price=Decimal("120.0000")
        )
        assert result == Decimal("106.6667")

    def test_buy_at_lower_price(self):
        """Buying at lower price should decrease weighted average."""
        # Current: 15 shares @ $106.67
        # Buy: 10 shares @ $90
        # Expected: (15×106.67 + 10×90) / 25 = 2500 / 25 = $100.00
        result = calculate_avg_price_on_buy(
            current_qty=Decimal("15"),
            current_avg=Decimal("106.6667"),
            buy_qty=Decimal("10"),
            buy_price=Decimal("90.0000")
        )
        assert result == Decimal("100.0000")

    def test_complex_weighted_average(self):
        """Test complex weighted average calculation."""
        # Current: 7 shares @ $85.50
        # Buy: 3 shares @ $92.75
        # Expected: (7×85.50 + 3×92.75) / 10 = (598.5 + 278.25) / 10 = $87.675
        result = calculate_avg_price_on_buy(
            current_qty=Decimal("7"),
            current_avg=Decimal("85.5000"),
            buy_qty=Decimal("3"),
            buy_price=Decimal("92.7500")
        )
        assert result == Decimal("87.6750")

    def test_zero_current_quantity(self):
        """Zero current quantity should behave like first purchase."""
        result = calculate_avg_price_on_buy(
            current_qty=Decimal("0"),
            current_avg=Decimal("0"),
            buy_qty=Decimal("5"),
            buy_price=Decimal("75.25")
        )
        assert result == Decimal("75.2500")

    def test_large_quantities(self):
        """Test with large quantities to ensure precision."""
        result = calculate_avg_price_on_buy(
            current_qty=Decimal("1000"),
            current_avg=Decimal("100.0000"),
            buy_qty=Decimal("500"),
            buy_price=Decimal("110.0000")
        )
        # (1000×100 + 500×110) / 1500 = 155000 / 1500 = 103.3333
        assert result == Decimal("103.3333")

    def test_decimal_precision_four_places(self):
        """Result should always be quantized to 4 decimal places."""
        result = calculate_avg_price_on_buy(
            current_qty=Decimal("3"),
            current_avg=Decimal("33.3333"),
            buy_qty=Decimal("2"),
            buy_price=Decimal("66.6667")
        )
        # (3×33.3333 + 2×66.6667) / 5 = 233.3333 / 5 = 46.66666
        # Should round to 46.6667
        assert result == Decimal("46.6667")
        assert result.as_tuple().exponent == -4


class TestAveragePriceOnSell:
    """Test that average price remains unchanged when selling."""

    def test_avg_price_unchanged(self):
        """Selling should not change average price."""
        current_avg = Decimal("100.0000")
        result = calculate_avg_price_on_sell(current_avg)
        assert result == current_avg

    def test_avg_price_unchanged_decimal_places(self):
        """Average price precision should be preserved."""
        current_avg = Decimal("75.5000")
        result = calculate_avg_price_on_sell(current_avg)
        assert result == Decimal("75.5000")

    def test_avg_price_unchanged_complex(self):
        """Complex average price should remain unchanged."""
        current_avg = Decimal("106.6667")
        result = calculate_avg_price_on_sell(current_avg)
        assert result == Decimal("106.6667")


# =============================================================================
# UNREALIZED P/L TESTS
# =============================================================================

class TestUnrealizedProfitLoss:
    """Test unrealized profit/loss calculations."""

    def test_profit_scenario(self):
        """Profitable position should return positive P/L."""
        # Bought 10 shares @ $100, now worth $150
        # P/L = (10 × $150) - (10 × $100) = $500 profit (50%)
        pl_amount, pl_percent = calculate_unrealized_pl(
            quantity=Decimal("10"),
            avg_price=Decimal("100.00"),
            current_price=Decimal("150.00")
        )
        assert pl_amount == Decimal("500.00")
        assert pl_percent == Decimal("50.00")

    def test_loss_scenario(self):
        """Loss position should return negative P/L."""
        # Bought 10 shares @ $100, now worth $80
        # P/L = (10 × $80) - (10 × $100) = -$200 loss (-20%)
        pl_amount, pl_percent = calculate_unrealized_pl(
            quantity=Decimal("10"),
            avg_price=Decimal("100.00"),
            current_price=Decimal("80.00")
        )
        assert pl_amount == Decimal("-200.00")
        assert pl_percent == Decimal("-20.00")

    def test_breakeven_scenario(self):
        """Breakeven position should return zero P/L."""
        pl_amount, pl_percent = calculate_unrealized_pl(
            quantity=Decimal("10"),
            avg_price=Decimal("100.00"),
            current_price=Decimal("100.00")
        )
        assert pl_amount == Decimal("0.00")
        assert pl_percent == Decimal("0.00")

    def test_zero_quantity(self):
        """Zero quantity should return zero P/L."""
        pl_amount, pl_percent = calculate_unrealized_pl(
            quantity=Decimal("0"),
            avg_price=Decimal("100.00"),
            current_price=Decimal("150.00")
        )
        assert pl_amount == Decimal("0.00")
        assert pl_percent == Decimal("0.00")

    def test_small_gain(self):
        """Test small percentage gains."""
        # 100 shares @ $50, now $51 = $100 profit (2%)
        pl_amount, pl_percent = calculate_unrealized_pl(
            quantity=Decimal("100"),
            avg_price=Decimal("50.00"),
            current_price=Decimal("51.00")
        )
        assert pl_amount == Decimal("100.00")
        assert pl_percent == Decimal("2.00")

    def test_large_gain(self):
        """Test large percentage gains."""
        # 5 shares @ $10, now $100 = $450 profit (900%)
        pl_amount, pl_percent = calculate_unrealized_pl(
            quantity=Decimal("5"),
            avg_price=Decimal("10.00"),
            current_price=Decimal("100.00")
        )
        assert pl_amount == Decimal("450.00")
        assert pl_percent == Decimal("900.00")

    def test_fractional_shares(self):
        """Test with fractional share quantities."""
        # 5.5 shares @ $75.25, now $80.50
        # Cost basis = 5.5 × 75.25 = $413.875
        # Current value = 5.5 × 80.50 = $442.75
        # P/L = $28.88 (6.97%)
        pl_amount, pl_percent = calculate_unrealized_pl(
            quantity=Decimal("5.5"),
            avg_price=Decimal("75.25"),
            current_price=Decimal("80.50")
        )
        assert pl_amount == Decimal("28.88")
        # Percentage: 28.875 / 413.875 * 100 ≈ 6.98%
        assert pl_percent == Decimal("6.98")


# =============================================================================
# REALIZED P/L TESTS
# =============================================================================

class TestRealizedProfitLoss:
    """Test realized profit/loss on sell transactions."""

    def test_profitable_sale(self):
        """Selling at profit should return positive P/L."""
        # Bought @ $100, selling 5 shares @ $120
        # P/L = (5 × $120) - (5 × $100) = $100 profit (20%)
        pl_amount, pl_percent = calculate_realized_pl(
            sell_qty=Decimal("5"),
            avg_price=Decimal("100.00"),
            sell_price=Decimal("120.00")
        )
        assert pl_amount == Decimal("100.00")
        assert pl_percent == Decimal("20.00")

    def test_loss_sale(self):
        """Selling at loss should return negative P/L."""
        # Bought @ $100, selling 5 shares @ $80
        # P/L = (5 × $80) - (5 × $100) = -$100 loss (-20%)
        pl_amount, pl_percent = calculate_realized_pl(
            sell_qty=Decimal("5"),
            avg_price=Decimal("100.00"),
            sell_price=Decimal("80.00")
        )
        assert pl_amount == Decimal("-100.00")
        assert pl_percent == Decimal("-20.00")

    def test_breakeven_sale(self):
        """Selling at breakeven should return zero P/L."""
        pl_amount, pl_percent = calculate_realized_pl(
            sell_qty=Decimal("10"),
            avg_price=Decimal("50.00"),
            sell_price=Decimal("50.00")
        )
        assert pl_amount == Decimal("0.00")
        assert pl_percent == Decimal("0.00")

    def test_partial_position_sale(self):
        """Test selling partial position."""
        # Bought 15 @ $100, selling 5 @ $150
        # Only calculate P/L on the 5 shares sold
        pl_amount, pl_percent = calculate_realized_pl(
            sell_qty=Decimal("5"),
            avg_price=Decimal("100.00"),
            sell_price=Decimal("150.00")
        )
        assert pl_amount == Decimal("250.00")
        assert pl_percent == Decimal("50.00")


# =============================================================================
# VALUE & COST BASIS TESTS
# =============================================================================

class TestTotalValue:
    """Test total value calculation."""

    def test_standard_calculation(self):
        """Standard total value calculation."""
        result = calculate_total_value(
            quantity=Decimal("10"),
            price=Decimal("150.00")
        )
        assert result == Decimal("1500.00")

    def test_zero_quantity(self):
        """Zero quantity should return zero value."""
        result = calculate_total_value(
            quantity=Decimal("0"),
            price=Decimal("100.00")
        )
        assert result == Decimal("0.00")

    def test_fractional_quantities(self):
        """Test with fractional shares."""
        result = calculate_total_value(
            quantity=Decimal("5.5"),
            price=Decimal("75.25")
        )
        assert result == Decimal("413.88")


class TestCostBasis:
    """Test cost basis calculation."""

    def test_standard_calculation(self):
        """Standard cost basis calculation."""
        result = calculate_cost_basis(
            quantity=Decimal("10"),
            avg_price=Decimal("100.00")
        )
        assert result == Decimal("1000.00")

    def test_fractional_quantities(self):
        """Test with fractional shares."""
        result = calculate_cost_basis(
            quantity=Decimal("5.5"),
            avg_price=Decimal("75.25")
        )
        assert result == Decimal("413.88")


# =============================================================================
# CURRENCY CONVERSION TESTS
# =============================================================================

class TestExchangeRateCalculation:
    """Test exchange rate calculation from amounts."""

    def test_usd_to_krw_rate(self):
        """Calculate USD to KRW exchange rate."""
        # 1,300,000 KRW = 1,000 USD
        # Rate: 1 USD = 1,300 KRW
        rate = calculate_exchange_rate(
            from_amount=Decimal("1300000"),
            to_amount=Decimal("1000")
        )
        assert rate == Decimal("1300.0000")

    def test_smaller_amounts(self):
        """Test with smaller amounts."""
        # 100 USD = 130,000 KRW
        # Rate: 1 USD = 1,300 KRW
        rate = calculate_exchange_rate(
            from_amount=Decimal("130000"),
            to_amount=Decimal("100")
        )
        assert rate == Decimal("1300.0000")

    def test_reciprocal_rate(self):
        """Test reciprocal exchange rate (KRW to USD)."""
        # 1,000 KRW = 0.769 USD (approx)
        # Rate: 1 KRW = 0.00077 USD (1/1300)
        rate = calculate_exchange_rate(
            from_amount=Decimal("1000"),
            to_amount=Decimal("1300000")
        )
        assert rate == Decimal("0.0008")  # Rounded to 4 decimal places

    def test_division_by_zero(self):
        """Should raise ValueError when to_amount is zero."""
        with pytest.raises(ValueError, match="Cannot calculate exchange rate with zero target amount"):
            calculate_exchange_rate(
                from_amount=Decimal("100"),
                to_amount=Decimal("0")
            )

    def test_decimal_precision_four_places(self):
        """Exchange rate should be quantized to 4 decimal places."""
        rate = calculate_exchange_rate(
            from_amount=Decimal("100"),
            to_amount=Decimal("3")
        )
        # 100 / 3 = 33.333... → should be 33.3333
        assert rate == Decimal("33.3333")
        assert rate.as_tuple().exponent == -4


class TestCurrencyConversion:
    """Test currency amount conversion."""

    def test_usd_to_krw_conversion(self):
        """Convert USD to KRW."""
        # 1,000 USD at rate 1,300
        result = convert_currency(
            amount=Decimal("1000"),
            exchange_rate=Decimal("1300")
        )
        assert result == Decimal("1300000.00")

    def test_krw_to_usd_conversion(self):
        """Convert KRW to USD."""
        # 100,000 KRW at rate 0.0007692 (1/1300)
        result = convert_currency(
            amount=Decimal("100000"),
            exchange_rate=Decimal("0.0007692")
        )
        assert result == Decimal("76.92")

    def test_small_amounts(self):
        """Test conversion with small amounts."""
        result = convert_currency(
            amount=Decimal("10"),
            exchange_rate=Decimal("1.5")
        )
        assert result == Decimal("15.00")

    def test_decimal_precision_two_places(self):
        """Converted amount should be quantized to 2 decimal places."""
        result = convert_currency(
            amount=Decimal("100"),
            exchange_rate=Decimal("1.333")
        )
        # 100 × 1.333 = 133.3 → should be 133.30
        assert result == Decimal("133.30")
        assert result.as_tuple().exponent == -2


# =============================================================================
# WEIGHT PERCENTAGE TESTS
# =============================================================================

class TestWeightPercentage:
    """Test percentage weight calculation."""

    def test_standard_percentage(self):
        """Calculate standard percentage weight."""
        # $4,000 in portfolio of $10,000 = 40%
        result = calculate_weight_percentage(
            part=Decimal("4000"),
            total=Decimal("10000")
        )
        assert result == Decimal("40.00")

    def test_small_percentage(self):
        """Test small percentage calculation."""
        result = calculate_weight_percentage(
            part=Decimal("50"),
            total=Decimal("10000")
        )
        assert result == Decimal("0.50")

    def test_100_percent(self):
        """Part equals total should be 100%."""
        result = calculate_weight_percentage(
            part=Decimal("5000"),
            total=Decimal("5000")
        )
        assert result == Decimal("100.00")

    def test_zero_total(self):
        """Zero total should return 0% (edge case)."""
        result = calculate_weight_percentage(
            part=Decimal("1000"),
            total=Decimal("0")
        )
        assert result == Decimal("0.00")

    def test_zero_part(self):
        """Zero part should return 0%."""
        result = calculate_weight_percentage(
            part=Decimal("0"),
            total=Decimal("10000")
        )
        assert result == Decimal("0.00")

    def test_decimal_precision_two_places(self):
        """Percentage should be quantized to 2 decimal places."""
        result = calculate_weight_percentage(
            part=Decimal("3333"),
            total=Decimal("10000")
        )
        # 3333 / 10000 × 100 = 33.33%
        assert result == Decimal("33.33")
        assert result.as_tuple().exponent == -2


# =============================================================================
# EDGE CASES & INTEGRATION TESTS
# =============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_small_numbers(self):
        """Test with very small decimal numbers."""
        pl_amount, pl_percent = calculate_unrealized_pl(
            quantity=Decimal("0.001"),
            avg_price=Decimal("0.01"),
            current_price=Decimal("0.02")
        )
        assert pl_amount == Decimal("0.00")  # Too small, rounds to 0.00
        # When pl_amount rounds to 0.00, percent is also 0.00
        assert pl_percent == Decimal("0.00")

    def test_very_large_numbers(self):
        """Test with very large numbers."""
        pl_amount, pl_percent = calculate_unrealized_pl(
            quantity=Decimal("1000000"),
            avg_price=Decimal("50.00"),
            current_price=Decimal("51.00")
        )
        assert pl_amount == Decimal("1000000.00")
        assert pl_percent == Decimal("2.00")

    def test_negative_pl_percentage_precision(self):
        """Test negative P/L percentage precision."""
        pl_amount, pl_percent = calculate_unrealized_pl(
            quantity=Decimal("100"),
            avg_price=Decimal("100.00"),
            current_price=Decimal("33.33")
        )
        # Loss = (100 × 33.33) - (100 × 100) = -6667.00 (-66.67%)
        assert pl_amount == Decimal("-6667.00")
        assert pl_percent == Decimal("-66.67")


class TestIntegrationScenarios:
    """Test realistic multi-step scenarios."""

    def test_complete_buy_sell_cycle(self):
        """Test a complete buy and sell cycle."""
        # Step 1: First buy
        avg1 = calculate_avg_price_on_buy(
            Decimal("0"), Decimal("0"), Decimal("10"), Decimal("100")
        )
        assert avg1 == Decimal("100.0000")

        # Step 2: Second buy at higher price
        avg2 = calculate_avg_price_on_buy(
            Decimal("10"), avg1, Decimal("5"), Decimal("120")
        )
        assert avg2 == Decimal("106.6667")

        # Step 3: Price goes up - check unrealized P/L
        pl_amount, pl_percent = calculate_unrealized_pl(
            quantity=Decimal("15"),
            avg_price=avg2,
            current_price=Decimal("150")
        )
        # Current value = 15 × 150 = 2250
        # Cost basis = 15 × 106.6667 = 1600
        # P/L = 650.00 (40.62%)
        assert pl_amount == Decimal("650.00")
        assert pl_percent == Decimal("40.62")

        # Step 4: Sell half
        sell_pl_amount, sell_pl_percent = calculate_realized_pl(
            sell_qty=Decimal("7.5"),
            avg_price=avg2,
            sell_price=Decimal("150")
        )
        # Realized P/L = (7.5 × 150) - (7.5 × 106.6667) = 1125 - 800 = 325
        assert sell_pl_amount == Decimal("325.00")

        # Step 5: Average price should remain unchanged after sell
        avg_after_sell = calculate_avg_price_on_sell(avg2)
        assert avg_after_sell == avg2

    def test_currency_exchange_roundtrip(self):
        """Test currency conversion roundtrip."""
        # USD to KRW and back
        usd_amount = Decimal("1000")
        usd_to_krw_rate = Decimal("1300.0000")

        # Convert USD to KRW
        krw_amount = convert_currency(usd_amount, usd_to_krw_rate)
        assert krw_amount == Decimal("1300000.00")

        # Calculate reverse rate
        krw_to_usd_rate = calculate_exchange_rate(
            from_amount=Decimal("1"),
            to_amount=usd_to_krw_rate
        )
        assert krw_to_usd_rate == Decimal("0.0008")  # 1/1300 rounded

        # Convert back (note: rounding means won't be exact)
        usd_back = convert_currency(krw_amount, krw_to_usd_rate)
        # Due to rounding, this will be approximately 1040.00
        assert usd_back == Decimal("1040.00")
