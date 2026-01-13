"""
Core financial calculation engine for PAMS.

CRITICAL: All functions are pure (no DB access). Use Decimal for all monetary calculations.

Average Price Rules:
- BUY: Calculate weighted average price
- SELL: Average price does NOT change (used for cost basis tracking)
"""

from decimal import Decimal
from typing import Tuple


def calculate_avg_price_on_buy(
    current_qty: Decimal,
    current_avg: Decimal,
    buy_qty: Decimal,
    buy_price: Decimal
) -> Decimal:
    """
    Calculate weighted average price when buying.

    Formula: (current_qty × current_avg + buy_qty × buy_price) / (current_qty + buy_qty)

    Args:
        current_qty: Current quantity held
        current_avg: Current average price
        buy_qty: Quantity being bought
        buy_price: Price per unit for this purchase

    Returns:
        New weighted average price

    Examples:
        >>> # First purchase
        >>> calculate_avg_price_on_buy(Decimal("0"), Decimal("0"), Decimal("10"), Decimal("100"))
        Decimal('100.0000')

        >>> # Second purchase at higher price
        >>> # Current: 10 shares @ $100 = $1000
        >>> # Buy: 5 shares @ $120 = $600
        >>> # New: 15 shares @ $106.67 = $1600
        >>> calculate_avg_price_on_buy(Decimal("10"), Decimal("100"), Decimal("5"), Decimal("120"))
        Decimal('106.6667')

        >>> # Third purchase at lower price
        >>> # Current: 15 shares @ $106.67
        >>> # Buy: 10 shares @ $90
        >>> # New: 25 shares @ $100
        >>> calculate_avg_price_on_buy(Decimal("15"), Decimal("106.6667"), Decimal("10"), Decimal("90"))
        Decimal('100.0000')
    """
    total_value = (current_qty * current_avg) + (buy_qty * buy_price)
    total_qty = current_qty + buy_qty

    if total_qty == 0:
        return Decimal("0").quantize(Decimal("0.0001"))

    avg_price = total_value / total_qty
    return avg_price.quantize(Decimal("0.0001"))  # 4 decimal places for prices


def calculate_avg_price_on_sell(current_avg: Decimal) -> Decimal:
    """
    Average price does NOT change on sell.

    The average price represents the cost basis and should remain unchanged
    when selling to allow proper profit/loss calculation.

    Args:
        current_avg: Current average price

    Returns:
        Unchanged average price

    Examples:
        >>> # Selling doesn't change average price
        >>> calculate_avg_price_on_sell(Decimal("100"))
        Decimal('100')

        >>> calculate_avg_price_on_sell(Decimal("75.50"))
        Decimal('75.50')
    """
    return current_avg


def calculate_unrealized_pl(
    quantity: Decimal,
    avg_price: Decimal,
    current_price: Decimal
) -> Tuple[Decimal, Decimal]:
    """
    Calculate unrealized profit/loss for a holding.

    Unrealized P/L = (Current Value) - (Cost Basis)
    Current Value = quantity × current_price
    Cost Basis = quantity × avg_price

    Args:
        quantity: Current quantity held
        avg_price: Average purchase price (cost basis per unit)
        current_price: Current market price

    Returns:
        Tuple of (pl_amount, pl_percent)
        - pl_amount: Absolute profit/loss amount
        - pl_percent: Percentage gain/loss

    Examples:
        >>> # Profitable position
        >>> # Bought 10 shares @ $100, now worth $150
        >>> # P/L = (10 × $150) - (10 × $100) = $500 profit (50%)
        >>> calculate_unrealized_pl(Decimal("10"), Decimal("100"), Decimal("150"))
        (Decimal('500.00'), Decimal('50.00'))

        >>> # Loss position
        >>> # Bought 10 shares @ $100, now worth $80
        >>> # P/L = (10 × $80) - (10 × $100) = -$200 loss (-20%)
        >>> calculate_unrealized_pl(Decimal("10"), Decimal("100"), Decimal("80"))
        (Decimal('-200.00'), Decimal('-20.00'))

        >>> # Breakeven
        >>> calculate_unrealized_pl(Decimal("10"), Decimal("100"), Decimal("100"))
        (Decimal('0.00'), Decimal('0.00'))

        >>> # Zero quantity (edge case)
        >>> calculate_unrealized_pl(Decimal("0"), Decimal("100"), Decimal("150"))
        (Decimal('0.00'), Decimal('0.00'))
    """
    cost_basis = quantity * avg_price
    current_value = quantity * current_price

    pl_amount = current_value - cost_basis
    pl_amount = pl_amount.quantize(Decimal("0.01"))  # 2 decimal places for money

    if cost_basis == 0:
        pl_percent = Decimal("0.00")
    else:
        pl_percent = (pl_amount / cost_basis * 100)
        pl_percent = pl_percent.quantize(Decimal("0.01"))

    return pl_amount, pl_percent


def calculate_realized_pl(
    sell_qty: Decimal,
    avg_price: Decimal,
    sell_price: Decimal
) -> Tuple[Decimal, Decimal]:
    """
    Calculate realized profit/loss on a sell transaction.

    Realized P/L = (Proceeds) - (Cost Basis)
    Proceeds = sell_qty × sell_price
    Cost Basis = sell_qty × avg_price

    Args:
        sell_qty: Quantity being sold
        avg_price: Average purchase price (cost basis)
        sell_price: Selling price per unit

    Returns:
        Tuple of (pl_amount, pl_percent)
        - pl_amount: Absolute profit/loss amount
        - pl_percent: Percentage gain/loss

    Examples:
        >>> # Profitable sale
        >>> # Bought @ $100, selling 5 shares @ $120
        >>> # P/L = (5 × $120) - (5 × $100) = $100 profit (20%)
        >>> calculate_realized_pl(Decimal("5"), Decimal("100"), Decimal("120"))
        (Decimal('100.00'), Decimal('20.00'))

        >>> # Loss sale
        >>> # Bought @ $100, selling 5 shares @ $80
        >>> # P/L = (5 × $80) - (5 × $100) = -$100 loss (-20%)
        >>> calculate_realized_pl(Decimal("5"), Decimal("100"), Decimal("80"))
        (Decimal('-100.00'), Decimal('-20.00'))

        >>> # Breakeven sale
        >>> calculate_realized_pl(Decimal("10"), Decimal("50"), Decimal("50"))
        (Decimal('0.00'), Decimal('0.00'))
    """
    cost_basis = sell_qty * avg_price
    proceeds = sell_qty * sell_price

    pl_amount = proceeds - cost_basis
    pl_amount = pl_amount.quantize(Decimal("0.01"))

    if cost_basis == 0:
        pl_percent = Decimal("0.00")
    else:
        pl_percent = (pl_amount / cost_basis * 100)
        pl_percent = pl_percent.quantize(Decimal("0.01"))

    return pl_amount, pl_percent


def calculate_total_value(
    quantity: Decimal,
    price: Decimal
) -> Decimal:
    """
    Calculate total value of a holding.

    Args:
        quantity: Quantity held
        price: Price per unit

    Returns:
        Total value (quantity × price)

    Examples:
        >>> calculate_total_value(Decimal("10"), Decimal("150"))
        Decimal('1500.00')

        >>> calculate_total_value(Decimal("0"), Decimal("100"))
        Decimal('0.00')
    """
    total = quantity * price
    return total.quantize(Decimal("0.01"))


def calculate_cost_basis(
    quantity: Decimal,
    avg_price: Decimal
) -> Decimal:
    """
    Calculate cost basis of a holding.

    Args:
        quantity: Quantity held
        avg_price: Average purchase price

    Returns:
        Cost basis (quantity × avg_price)

    Examples:
        >>> calculate_cost_basis(Decimal("10"), Decimal("100"))
        Decimal('1000.00')

        >>> calculate_cost_basis(Decimal("5.5"), Decimal("75.25"))
        Decimal('413.88')
    """
    cost = quantity * avg_price
    return cost.quantize(Decimal("0.01"))


def calculate_exchange_rate(
    from_amount: Decimal,
    to_amount: Decimal
) -> Decimal:
    """
    Calculate exchange rate from two currency amounts.

    Formula: exchange_rate = from_amount / to_amount
    Meaning: 1 unit of to_currency = exchange_rate units of from_currency

    Args:
        from_amount: Amount of source currency
        to_amount: Amount of target currency

    Returns:
        Exchange rate (4 decimal places)

    Raises:
        ValueError: If to_amount is zero

    Examples:
        >>> # 1,300,000 KRW = 1,000 USD
        >>> # Rate: 1 USD = 1,300 KRW
        >>> calculate_exchange_rate(Decimal("1300000"), Decimal("1000"))
        Decimal('1300.0000')

        >>> # 100 USD = 130,000 KRW
        >>> # Rate: 1 USD = 1,300 KRW
        >>> calculate_exchange_rate(Decimal("130000"), Decimal("100"))
        Decimal('1300.0000')
    """
    if to_amount == 0:
        raise ValueError("Cannot calculate exchange rate with zero target amount")

    rate = from_amount / to_amount
    return rate.quantize(Decimal("0.0001"))  # 4 decimal places for exchange rates


def convert_currency(
    amount: Decimal,
    exchange_rate: Decimal
) -> Decimal:
    """
    Convert an amount using an exchange rate.

    Args:
        amount: Amount to convert
        exchange_rate: Exchange rate

    Returns:
        Converted amount

    Examples:
        >>> # Convert 1,000 USD to KRW at rate 1,300
        >>> convert_currency(Decimal("1000"), Decimal("1300"))
        Decimal('1300000.00')

        >>> # Convert 100,000 KRW to USD at rate 0.00077 (1/1300)
        >>> convert_currency(Decimal("100000"), Decimal("0.0007692"))
        Decimal('76.92')
    """
    converted = amount * exchange_rate
    return converted.quantize(Decimal("0.01"))


def calculate_weight_percentage(
    part: Decimal,
    total: Decimal
) -> Decimal:
    """
    Calculate percentage weight of a part within a total.

    Args:
        part: Part value
        total: Total value

    Returns:
        Percentage (0-100)

    Examples:
        >>> # Asset worth $4000 in portfolio of $10000 = 40%
        >>> calculate_weight_percentage(Decimal("4000"), Decimal("10000"))
        Decimal('40.00')

        >>> # Edge case: zero total
        >>> calculate_weight_percentage(Decimal("1000"), Decimal("0"))
        Decimal('0.00')
    """
    if total == 0:
        return Decimal("0.00")

    percentage = (part / total * 100)
    return percentage.quantize(Decimal("0.01"))
