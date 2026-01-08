"""
Tests for account schema validators, including price_currency auto-inference.
"""
import pytest
from decimal import Decimal
from pydantic import ValidationError

from app.schemas.account_schema import InitialHoldingItem


class TestInitialHoldingItemPriceCurrency:
    """Test price_currency validation and auto-inference for InitialHoldingItem."""

    def test_korean_stock_auto_infers_krw(self):
        """Test that Korean stock ticker (6-digit numeric) auto-infers KRW price_currency."""
        item = InitialHoldingItem(
            ticker="005930",
            quantity=Decimal("10"),
            price=Decimal("75000")
        )
        assert item.price_currency == "KRW"

    def test_korean_stock_with_suffix_auto_infers_krw(self):
        """Test that Korean stock ticker with .KS suffix auto-infers KRW price_currency."""
        item = InitialHoldingItem(
            ticker="005930.KS",
            quantity=Decimal("10"),
            price=Decimal("75000")
        )
        assert item.price_currency == "KRW"

    def test_korean_stock_with_kq_suffix_auto_infers_krw(self):
        """Test that Korean stock ticker with .KQ suffix auto-infers KRW price_currency."""
        item = InitialHoldingItem(
            ticker="005930.KQ",
            quantity=Decimal("10"),
            price=Decimal("75000")
        )
        assert item.price_currency == "KRW"

    def test_japanese_stock_auto_infers_jpy(self):
        """Test that Japanese stock ticker with .T suffix auto-infers JPY price_currency."""
        item = InitialHoldingItem(
            ticker="7203.T",
            quantity=Decimal("100"),
            price=Decimal("2500")
        )
        assert item.price_currency == "JPY"

    def test_hong_kong_stock_auto_infers_hkd(self):
        """Test that Hong Kong stock ticker with .HK suffix auto-infers HKD price_currency."""
        item = InitialHoldingItem(
            ticker="0700.HK",
            quantity=Decimal("1000"),
            price=Decimal("400")
        )
        assert item.price_currency == "HKD"

    def test_us_stock_auto_infers_usd(self):
        """Test that US stock ticker auto-infers USD price_currency."""
        item = InitialHoldingItem(
            ticker="AAPL",
            quantity=Decimal("10"),
            price=Decimal("150.50")
        )
        assert item.price_currency == "USD"

    def test_ticker_auto_infers_usd(self):
        """Test that TSLA stock ticker auto-infers USD price_currency."""
        item = InitialHoldingItem(
            ticker="TSLA",
            quantity=Decimal("10"),
            price=Decimal("250.75")
        )
        assert item.price_currency == "USD"

    def test_manual_price_currency_override(self):
        """Test that manually specified price_currency is respected."""
        item = InitialHoldingItem(
            ticker="AAPL",
            quantity=Decimal("10"),
            price=Decimal("150.50"),
            price_currency="KRW"
        )
        assert item.price_currency == "KRW"

    def test_currency_ticker_rejects_price_currency(self):
        """Test that currency tickers (KRW, USD) reject price_currency."""
        with pytest.raises(ValidationError) as exc_info:
            InitialHoldingItem(
                ticker="KRW",
                quantity=Decimal("1000000"),
                price=None,
                price_currency="USD"
            )

        errors = exc_info.value.errors()
        assert any(
            "price_currency should not be provided for currency ticker KRW" in str(error)
            for error in errors
        )

    def test_currency_ticker_allows_no_price_currency(self):
        """Test that currency tickers work correctly without price_currency."""
        item = InitialHoldingItem(
            ticker="USD",
            quantity=Decimal("1000"),
            price=None,
            price_currency=None
        )
        assert item.price_currency is None

    def test_stock_without_price_rejects_price_currency(self):
        """Test that stock without price raises validation error for missing price."""
        # When price is None for a non-currency ticker, price validator should fail
        with pytest.raises(ValidationError) as exc_info:
            InitialHoldingItem(
                ticker="AAPL",
                quantity=Decimal("10"),
                price=None,
                price_currency=None
            )

        errors = exc_info.value.errors()
        assert any(
            "Price is required for asset ticker AAPL" in str(error)
            for error in errors
        )

    def test_stock_with_price_requires_price_currency(self):
        """Test that stock with price auto-infers price_currency if not provided."""
        item = InitialHoldingItem(
            ticker="AAPL",
            quantity=Decimal("10"),
            price=Decimal("150.50"),
            price_currency=None
        )
        # Auto-inference should happen
        assert item.price_currency == "USD"

    def test_lower_case_ticker_auto_infers(self):
        """Test that lower case ticker still auto-infers correctly."""
        item = InitialHoldingItem(
            ticker="aapl",
            quantity=Decimal("10"),
            price=Decimal("150.50")
        )
        assert item.price_currency == "USD"

    def test_lower_case_korean_ticker_auto_infers_krw(self):
        """Test that lower case Korean ticker still auto-infers KRW."""
        item = InitialHoldingItem(
            ticker="005930",
            quantity=Decimal("10"),
            price=Decimal("75000")
        )
        assert item.price_currency == "KRW"
