"""
Transaction type validation by account type.

This module enforces the transaction type restrictions defined in RULES.md
and TRANSACTION_PATTERNS.md. Each account type has specific allowed transaction
types based on its purpose.

Account Type Rules:
- Deposit: Cash-only operations (Deposit, Withdrawal, Transfers)
- Securities: Full investment capabilities (Buy, Sell, Dividend, Deposit, Withdrawal, Transfers)
- ForeignCurrency: Multi-currency operations (Exchange, Deposit, Withdrawal, Transfers)
- MoneyMarket: Interest-earning accounts (Interest, Deposit, Withdrawal, Transfers)
"""

from typing import Set, Dict


# Transaction type restrictions matrix
# Maps account type → set of allowed transaction types
ALLOWED_TRANSACTIONS: Dict[str, Set[str]] = {
    'Deposit': {
        'Deposit',
        'Withdrawal',
        'Transfer_In',
        'Transfer_Out'
    },
    'Securities': {
        'Deposit',
        'Withdrawal',
        'Transfer_In',
        'Transfer_Out',
        'Buy',
        'Sell',
        'Dividend'
    },
    'ForeignCurrency': {
        'Deposit',
        'Withdrawal',
        'Transfer_In',
        'Transfer_Out',
        'Exchange'
    },
    'MoneyMarket': {
        'Deposit',
        'Withdrawal',
        'Transfer_In',
        'Transfer_Out',
        'Interest'
    },
    'Savings': {
        'Deposit',
        'Withdrawal',
        'Transfer_In',
        'Transfer_Out',
        'Interest'
    }
}


def validate_transaction_type(account_type: str, transaction_type: str) -> None:
    """
    Validate that transaction type is allowed for account type.

    Args:
        account_type: The account type (Deposit, Securities, ForeignCurrency, MoneyMarket)
        transaction_type: The transaction type to validate

    Raises:
        ValueError: If transaction type is not allowed for this account type

    Examples:
        >>> validate_transaction_type('Deposit', 'Deposit')  # OK
        >>> validate_transaction_type('Deposit', 'Buy')  # Raises ValueError
        >>> validate_transaction_type('Securities', 'Buy')  # OK
    """
    allowed = ALLOWED_TRANSACTIONS.get(account_type, set())

    if transaction_type not in allowed:
        allowed_list = ', '.join(sorted(allowed))
        raise ValueError(
            f"Transaction type '{transaction_type}' is not allowed for "
            f"account type '{account_type}'. Allowed types: {allowed_list}"
        )


def get_allowed_transaction_types(account_type: str) -> Set[str]:
    """
    Get all allowed transaction types for an account type.

    Args:
        account_type: The account type

    Returns:
        Set of allowed transaction type strings

    Examples:
        >>> get_allowed_transaction_types('Deposit')
        {'Deposit', 'Withdrawal', 'Transfer_In', 'Transfer_Out'}
        >>> get_allowed_transaction_types('Securities')
        {'Deposit', 'Withdrawal', 'Transfer_In', 'Transfer_Out', 'Buy', 'Sell', 'Dividend'}
    """
    return ALLOWED_TRANSACTIONS.get(account_type, set())
