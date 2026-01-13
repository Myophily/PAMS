# TRANSACTION_PATTERNS.md - Personal Asset Management System

In-depth explanation of the 4 core transaction patterns with implementation examples.

---

## Transaction Type Restrictions by Account Type

The backend enforces which transaction types are allowed on each account type to maintain data integrity and reflect real-world financial operations.

### Allowed Transactions Matrix

| Transaction Type | Deposit | Securities | ForeignCurrency | MoneyMarket | Savings | Pattern |
|------------------|---------|------------|-----------------|-------------|---------|---------|
| `Deposit` | ✅ | ✅ | ✅ | ✅ | ✅ | Pattern ① |
| `Withdrawal` | ✅ | ✅ | ✅ | ✅ | ✅ | Pattern ① |
| `Transfer_In` | ✅ | ✅ | ✅* | ✅ | ✅ | Pattern ② |
| `Transfer_Out` | ✅ | ✅ | ✅* | ✅ | ✅ | Pattern ② |
| `Buy` | ❌ | ✅ | ❌ | ❌ | ❌ | Pattern ③ |
| `Sell` | ❌ | ✅ | ❌ | ❌ | ❌ | Pattern ③ |
| `Dividend` | ❌ | ✅ | ❌ | ❌ | ❌ | Pattern ① |
| `Exchange` | ❌ | ❌ | ✅ | ❌ | ❌ | Pattern ④ |
| `Interest` | ❌ | ❌ | ❌ | ✅ | ✅ | Pattern ① |

**Note:** * ForeignCurrency accounts use Exchange with `to_account_id` for cross-account transfers (4-transaction pattern). Simple Transfer_In/Out allowed for same-currency transfers only.

### Rationale

**Deposit Accounts:**
- Purpose: Daily spending, cash management, simple transfers
- Restriction: Cannot buy/sell securities or exchange currencies
- Rationale: Represents checking/savings accounts that only handle cash

**Securities Accounts:**
- Purpose: Investment management, stock/bond trading
- Allowed: All cash operations + Buy/Sell/Dividend
- Rationale: Brokerage accounts can hold both cash and securities

**ForeignCurrency Accounts:**
- Purpose: Foreign currency holdings (USD, EUR, etc.)
- Allowed: Cash operations + Exchange between currencies
- Rationale: Specialized for multi-currency management

**MoneyMarket Accounts:**
- Purpose: Money market funds earning interest
- Allowed: Cash operations + Interest income
- Rationale: Similar to deposit accounts but tracks interest earnings

**Savings Accounts:**
- Purpose: Savings accounts earning interest (any currency)
- Allowed: Cash operations + Interest income
- Rationale: Like MoneyMarket but supports multiple currencies

### Validation Error Example

```python
# Attempting to buy stock in a Deposit account
try:
    create_buy_transaction(
        account_id=1,  # Deposit account
        ticker="AAPL",
        quantity=10,
        price=150.00
    )
except ValueError as e:
    # Error: "Transaction type 'Buy' is not allowed for account type 'Deposit'.
    # Allowed types: Deposit, Withdrawal, Transfer_In, Transfer_Out"
```

---

## Overview

All financial activities in PAM must follow one of these 4 fundamental patterns. Each pattern has specific rules for:
- Which database records to create/update
- How total assets are affected
- What validation is required

---

## Pattern ① Pure Income/Expense

**Reality:** Money enters or leaves your financial system entirely.

**Examples:**
- Salary deposit
- Food expense
- Bill payment
- Stock dividend received

**Characteristic:** Single account involved, total assets change.

---

### Implementation

**Database Operations:**

1. **Create Transaction Record:**
```python
transaction = Transaction(
    account_id=account.id,
    type="Deposit",  # or "Withdrawal", "Dividend"
    ticker=None,  # Not applicable for simple deposits/withdrawals
    quantity=None,
    price=None,
    amount=1000000.00,  # Positive for income, negative for expense
    date=datetime(2024, 1, 15, 10, 30),
    linked_tx_id=None,  # No linked transaction
    description="Monthly salary"
)
db.add(transaction)
```

2. **Update Holding (CASH):**
```python
# Get or create CASH holding
cash_holding = db.query(Holding).filter(
    Holding.account_id == account.id,
    Holding.ticker == "CASH"
).first()

if not cash_holding:
    cash_holding = Holding(
        account_id=account.id,
        ticker="CASH",
        quantity=0,
        avg_price=1.0
    )
    db.add(cash_holding)

# Update balance
cash_holding.quantity += transaction.amount
```

3. **Update AssetSnapshot:**
```python
# Regenerate snapshot for transaction date
snapshot = generate_snapshot(transaction.date, db)
db.merge(snapshot)  # Insert or update
```

---

### Transaction Types

#### Deposit
**Use case:** Income entering the account (salary, gift, refund)

```python
Transaction(
    account_id=1,
    type="Deposit",
    amount=1000000.00,  # Positive amount
    date=datetime.now(),
    description="Monthly salary"
)
```

**Effect:**
- Account CASH balance: +1,000,000
- Total assets: +1,000,000

---

#### Withdrawal
**Use case:** Expense leaving the account (payment, fee, purchase)

```python
Transaction(
    account_id=1,
    type="Withdrawal",
    amount=-50000.00,  # Negative amount
    date=datetime.now(),
    description="Grocery shopping"
)
```

**Effect:**
- Account CASH balance: -50,000
- Total assets: -50,000

---

#### Dividend
**Use case:** Stock dividend received

```python
Transaction(
    account_id=2,  # Brokerage account
    type="Dividend",
    ticker="AAPL",  # Stock that paid dividend
    amount=50.00,  # Dividend amount received
    date=datetime.now(),
    description="Apple quarterly dividend"
)
```

**Effect:**
- Account CASH balance: +50
- Total assets: +50
- (Dividend is new money, not from selling stock)

---

### Validation Rules

```python
def validate_deposit_withdrawal(transaction: Transaction, db: Session):
    """Validate deposit/withdrawal transaction."""
    # Check amount is non-zero
    if transaction.amount == 0:
        raise ValueError("Amount cannot be zero")

    # Check account exists
    account = db.query(Account).get(transaction.account_id)
    if not account:
        raise ValueError("Account not found")

    # For withdrawals, check sufficient balance
    if transaction.type == "Withdrawal":
        cash_holding = db.query(Holding).filter(
            Holding.account_id == account.id,
            Holding.ticker == "CASH"
        ).first()

        if not cash_holding or cash_holding.quantity < abs(transaction.amount):
            raise ValueError("Insufficient cash balance")

    # Check date is not in future
    if transaction.date > datetime.now():
        raise ValueError("Transaction date cannot be in the future")
```

---

## Pattern ② Simple Transfer

**Reality:** Moving money between your own accounts.

**Examples:**
- Transfer from checking account → brokerage account
- Transfer from savings → checking

**Characteristic:** Two accounts involved, total assets unchanged.

---

### Implementation

**Database Operations:**

1. **Create Two Linked Transaction Records:**
```python
# Transaction 1: Outflow from source account
tx_out = Transaction(
    account_id=source_account.id,
    type="Transfer_Out",
    amount=-500000.00,  # Negative (money leaving)
    date=datetime(2024, 1, 15, 10, 30),
    description=f"Transfer to {target_account.name}"
)
db.add(tx_out)
db.flush()  # Get tx_out.id

# Transaction 2: Inflow to target account
tx_in = Transaction(
    account_id=target_account.id,
    type="Transfer_In",
    amount=500000.00,  # Positive (money arriving)
    date=datetime(2024, 1, 15, 10, 30),
    description=f"Transfer from {source_account.name}"
)
db.add(tx_in)
db.flush()  # Get tx_in.id

# Link them (bidirectional)
tx_out.linked_tx_id = tx_in.id
tx_in.linked_tx_id = tx_out.id
```

2. **Update Holdings (CASH in both accounts):**
```python
# Update source account CASH
source_cash = get_or_create_cash_holding(source_account.id, db)
source_cash.quantity += tx_out.amount  # Decreases (negative amount)

# Update target account CASH
target_cash = get_or_create_cash_holding(target_account.id, db)
target_cash.quantity += tx_in.amount  # Increases (positive amount)
```

3. **Verify Invariant:**
```python
# Total assets before must equal total assets after
assert tx_out.amount + tx_in.amount == 0  # Should sum to zero
```

---

### Transaction Flow Example

**Scenario:** Transfer 500,000 KRW from Toss Checking to Kiwoom Brokerage

**Before:**
```
Account: Toss Checking (ID=1)
  - CASH: 1,000,000 KRW

Account: Kiwoom Brokerage (ID=2)
  - CASH: 0 KRW

Total Assets: 1,000,000 KRW
```

**Transactions Created:**
```sql
INSERT INTO transaction VALUES (
  101,  -- id
  1,    -- account_id (Toss Checking)
  'Transfer_Out',
  NULL, -- ticker
  NULL, -- quantity
  NULL, -- price
  -500000.00,  -- amount
  '2024-01-15',
  102,  -- linked_tx_id
  'Transfer to Kiwoom Brokerage',
  '2024-01-15 10:30:00',
  NULL  -- deleted_at
);

INSERT INTO transaction VALUES (
  102,  -- id
  2,    -- account_id (Kiwoom Brokerage)
  'Transfer_In',
  NULL,
  NULL,
  NULL,
  500000.00,  -- amount
  '2024-01-15',
  101,  -- linked_tx_id
  'Transfer from Toss Checking',
  '2024-01-15 10:30:00',
  NULL
);
```

**After:**
```
Account: Toss Checking (ID=1)
  - CASH: 500,000 KRW

Account: Kiwoom Brokerage (ID=2)
  - CASH: 500,000 KRW

Total Assets: 1,000,000 KRW  ← UNCHANGED
```

---

### Validation Rules

```python
def validate_transfer(from_account_id: int, to_account_id: int, amount: float, db: Session):
    """Validate transfer transaction."""
    # Check accounts exist
    from_account = db.query(Account).get(from_account_id)
    to_account = db.query(Account).get(to_account_id)

    if not from_account or not to_account:
        raise ValueError("Invalid account ID")

    # Cannot transfer to same account
    if from_account_id == to_account_id:
        raise ValueError("Cannot transfer to the same account")

    # Check sufficient balance in source account
    source_cash = db.query(Holding).filter(
        Holding.account_id == from_account_id,
        Holding.ticker == "CASH"
    ).first()

    if not source_cash or source_cash.quantity < amount:
        raise ValueError("Insufficient balance in source account")

    # Amount must be positive
    if amount <= 0:
        raise ValueError("Transfer amount must be positive")
```

---

## Pattern ③ Asset Form Conversion (Invest/Liquidate)

**Reality:** Changing the form of your assets within the same account.

**Examples:**
- Buy stock with cash (cash → stock)
- Sell stock for cash (stock → cash)

**Characteristic:** Single account, two holdings affected (CASH + ticker), total asset value unchanged at transaction time.

---

### Implementation

**Database Operations:**

1. **Create Transaction Record:**
```python
# Buy example
transaction = Transaction(
    account_id=account.id,
    type="Buy",  # or "Sell"
    ticker="AAPL",
    quantity=10,
    price=150.00,
    price_currency="USD",  # Currency of the price
    amount=-1500.00,  # Negative for buy (cash outflow)
    date=datetime(2024, 1, 15, 10, 30),
    linked_tx_id=None,
    description="Buy Apple stock"
)
db.add(transaction)
```

2. **Update CASH Holding:**
```python
cash_holding = get_or_create_cash_holding(account.id, db)
cash_holding.quantity += transaction.amount  # Decreases by 1500
```

3. **Update Stock Holding:**
```python
# Get or create stock holding
stock_holding = db.query(Holding).filter(
    Holding.account_id == account.id,
    Holding.ticker == transaction.ticker
).first()

if not stock_holding:
    stock_holding = Holding(
        account_id=account.id,
        ticker=transaction.ticker,
        quantity=0,
        avg_price=0
    )
    db.add(stock_holding)

# Update quantity and average price
if transaction.type == "Buy":
    # Weighted average price calculation
    total_value = (stock_holding.quantity * stock_holding.avg_price) + \
                  (transaction.quantity * transaction.price)
    total_qty = stock_holding.quantity + transaction.quantity
    stock_holding.avg_price = total_value / total_qty if total_qty > 0 else 0
    stock_holding.quantity = total_qty

elif transaction.type == "Sell":
    # Average price remains unchanged on sell
    stock_holding.quantity -= transaction.quantity

    if stock_holding.quantity < 0:
        raise ValueError("Cannot sell more than you own")
```

---

### Buy Transaction Example

**Scenario:** Buy 10 shares of AAPL at $150/share in Brokerage account

**Before:**
```
Account: Kiwoom Brokerage (ID=2)
  - CASH: 2,000 USD
  - AAPL: 0 shares @ $0 avg

Total Assets: $2,000
```

**Transaction:**
```python
Transaction(
    id=201,
    account_id=2,
    type="Buy",
    ticker="AAPL",
    quantity=10,
    price=150.00,
    price_currency="USD",
    amount=-1500.00,  # Cash outflow
    date='2024-01-15'
)
```

**After:**
```
Account: Kiwoom Brokerage (ID=2)
  - CASH: 500 USD
  - AAPL: 10 shares @ $150 avg

Total Assets: $2,000  ← UNCHANGED (at transaction time)
```

**Later (when AAPL price changes to $180):**
```
Account: Kiwoom Brokerage (ID=2)
  - CASH: 500 USD
  - AAPL: 10 shares @ $150 avg (current price: $180)
    - Current value: 10 × $180 = $1,800
    - Cost basis: 10 × $150 = $1,500
    - Unrealized P/L: $300 (+20%)

Total Assets: $2,300  ← NOW CHANGED due to market movement
```

---

### Sell Transaction Example

**Scenario:** Sell 5 shares of AAPL at $180/share

**Before:**
```
Account: Kiwoom Brokerage (ID=2)
  - CASH: 500 USD
  - AAPL: 10 shares @ $150 avg (current price: $180)
```

**Transaction:**
```python
Transaction(
    id=202,
    account_id=2,
    type="Sell",
    ticker="AAPL",
    quantity=5,
    price=180.00,
    price_currency="USD",
    amount=900.00,  # Cash inflow (5 × $180)
    date='2024-01-20'
)
```

**After:**
```
Account: Kiwoom Brokerage (ID=2)
  - CASH: 1,400 USD  (500 + 900)
  - AAPL: 5 shares @ $150 avg  ← avg_price UNCHANGED

Realized P/L: 5 × ($180 - $150) = $150
```

---

### Average Price Calculation Logic

**Buying increases quantity and updates average price:**

```python
def calculate_avg_price_on_buy(current_qty, current_avg, buy_qty, buy_price):
    """
    Weighted average price calculation.

    Example 1: First purchase
      Current: 0 shares @ $0
      Buy: 10 shares @ $100
      New avg: (0*0 + 10*100) / (0+10) = $100

    Example 2: Second purchase at higher price
      Current: 10 shares @ $100
      Buy: 5 shares @ $120
      New avg: (10*100 + 5*120) / (10+5) = 1600/15 = $106.67

    Example 3: Third purchase at lower price
      Current: 15 shares @ $106.67
      Buy: 10 shares @ $90
      New avg: (15*106.67 + 10*90) / (15+10) = 2500/25 = $100
    """
    total_value = (current_qty * current_avg) + (buy_qty * buy_price)
    total_qty = current_qty + buy_qty
    return total_value / total_qty if total_qty > 0 else 0
```

**Selling decreases quantity but keeps average price:**

```python
def calculate_avg_price_on_sell(current_qty, current_avg, sell_qty):
    """
    Average price does NOT change on sell.

    Example:
      Current: 10 shares @ $100
      Sell: 5 shares
      Remaining: 5 shares @ $100  ← avg stays $100

    This allows tracking cost basis for remaining shares.
    Realized P/L is calculated separately: sell_qty × (sell_price - avg_price)
    """
    if sell_qty > current_qty:
        raise ValueError(f"Cannot sell {sell_qty} shares (only have {current_qty})")

    return current_avg  # Unchanged
```

---

### Validation Rules

```python
def validate_buy_sell(transaction: Transaction, db: Session):
    """Validate buy/sell transaction."""
    # Check required fields
    if not transaction.ticker or not transaction.quantity or not transaction.price:
        raise ValueError("Ticker, quantity, and price are required")

    # Quantity must be positive
    if transaction.quantity <= 0:
        raise ValueError("Quantity must be positive")

    # Price must be positive
    if transaction.price <= 0:
        raise ValueError("Price must be positive")

    # For Buy: check sufficient cash
    if transaction.type == "Buy":
        cash_needed = transaction.quantity * transaction.price

        cash_holding = db.query(Holding).filter(
            Holding.account_id == transaction.account_id,
            Holding.ticker == "CASH"
        ).first()

        if not cash_holding or cash_holding.quantity < cash_needed:
            raise ValueError(f"Insufficient cash (need {cash_needed})")

    # For Sell: check sufficient shares
    if transaction.type == "Sell":
        stock_holding = db.query(Holding).filter(
            Holding.account_id == transaction.account_id,
            Holding.ticker == transaction.ticker
        ).first()

        if not stock_holding or stock_holding.quantity < transaction.quantity:
            raise ValueError(f"Insufficient shares to sell")
```

---

## Pattern ① (Variant): Interest Transaction

**Reality:** Interest earned on savings or money market accounts increases cash balance.

**Examples:**
- Monthly interest on savings account
- Daily interest on money market fund
- Certificate of deposit interest payment

**Characteristic:** Single account involved, single holding (CASH) affected, total assets increase.

---

### Implementation

**Database Operations:**

1. **Create Transaction Record:**
```python
transaction = Transaction(
    account_id=account.id,
    type="Interest",
    ticker="KRW",  # Currency earning interest
    quantity=None,
    price=None,
    price_currency=None,
    amount=50000.00,  # Positive inflow
    date=datetime.now(),
    linked_tx_id=None,
    description="Monthly interest payment"
)
db.add(transaction)
```

2. **Update CASH Holding:**
```python
cash_holding = get_or_create_cash_holding(account.id, db)
cash_holding.quantity += transaction.amount  # Increases by interest amount
```

3. **Update AssetSnapshot (if past date):**
```python
if transaction.date < datetime.now():
    recalculate_from_date(transaction.date, db)
```

---

### Interest Transaction Example

**Scenario:** Receive 50,000 KRW monthly interest on Money Market account

**Before:**
```
Account: Toss Money Market (ID=4)
  - CASH: 10,000,000 KRW

Total Assets: 10,000,000 KRW
```

**Transaction:**
```python
Transaction(
    id=301,
    account_id=4,
    type="Interest",
    ticker="KRW",
    amount=50000.00,
    date='2024-01-31'
)
```

**After:**
```
Account: Toss Money Market (ID=4)
  - CASH: 10,050,000 KRW

Total Assets: 10,050,000 KRW  ← INCREASED by interest
```

---

### Validation Rules

```python
def validate_interest_transaction(transaction, account, db):
    """Validate Interest transaction."""

    # Only allowed on MoneyMarket and Savings accounts
    if account.type not in ['MoneyMarket', 'Savings']:
        raise ValueError(f"Interest transactions only allowed on MoneyMarket and Savings accounts")

    # Amount must be positive
    if transaction.amount <= 0:
        raise ValueError("Interest amount must be positive")

    # Ticker must be a currency (not a stock)
    if transaction.ticker not in ['KRW', 'USD', 'EUR', 'JPY']:
        raise ValueError("Interest ticker must be a currency code")
```

---

### Business Rules

1. **Account type restriction:** Only MoneyMarket and Savings accounts can have Interest transactions
2. **Total assets change:** Unlike Pattern ③ (Buy/Sell), Interest increases total asset value
3. **Similar to Deposit:** Functionally similar to Deposit, but semantically different (earned vs. deposited)
4. **Frequency:** Can be daily, monthly, or quarterly depending on account terms
5. **Compounding:** Each interest transaction is independent; compounding calculated by creating new Interest transactions based on previous balance

---

## Pattern ④ Exchange (EVOLVED - Now Cross-Account Only)

**Note:** Pattern ④ has evolved from single-account same-currency exchange to cross-account exchange-transfer only.

**Previous behavior (deprecated):** Same-account exchange within a single Foreign Currency Account
**Current behavior:** All exchange operations now require a target account and create 4 transactions using Pattern ④+② (see Cross-Account Exchange-Transfer section below).

**Why the change:** Cross-account exchanges with automatic currency conversion better reflect real-world financial operations and provide clearer transaction tracking.

**Characteristic:** Single account, two currency holdings affected, total asset value unchanged at transaction time (same account, different currencies).

---

### Implementation

**Database Operations:**

1. **Create Two Linked Transaction Records:**
```python
# Transaction 1: Currency being sold (outflow)
tx_sell = Transaction(
    account_id=account.id,
    type="Exchange",
    ticker="KRW",  # Currency being sold
    amount=-1300000.00,  # Negative (currency leaving)
    date=datetime(2024, 1, 15, 10, 30),
    description="Exchange KRW to USD"
)
db.add(tx_sell)
db.flush()

# Transaction 2: Currency being bought (inflow)
tx_buy = Transaction(
    account_id=account.id,
    type="Exchange",
    ticker="USD",  # Currency being bought
    amount=1000.00,  # Positive (currency arriving)
    date=datetime(2024, 1, 15, 10, 30),
    description="Exchange KRW to USD"
)
db.add(tx_buy)
db.flush()

# Link them
tx_sell.linked_tx_id = tx_buy.id
tx_buy.linked_tx_id = tx_sell.id
```

2. **Update Holdings for Both Currencies:**
```python
# Update KRW holding
krw_holding = get_or_create_holding(account.id, "KRW", db)
krw_holding.quantity += tx_sell.amount  # Decreases

# Update USD holding
usd_holding = get_or_create_holding(account.id, "USD", db)
usd_holding.quantity += tx_buy.amount  # Increases
```

3. **Record Exchange Rate in MarketData:**
```python
exchange_rate = abs(tx_sell.amount) / abs(tx_buy.amount)  # 1300000 / 1000 = 1300

market_data = MarketData(
    ticker="USD_KRW",  # Format: {BASE}_{QUOTE}
    date=transaction.date,
    exchange_rate=exchange_rate,  # 1 USD = 1300 KRW
    source="user_input"
)
db.merge(market_data)  # Insert or update
```

---

### Exchange Transaction Example

**Scenario:** Exchange 1,300,000 KRW for 1,000 USD (rate: 1 USD = 1,300 KRW)

**Before:**
```
Account: Foreign Currency Account (ID=3)
  - KRW: 2,000,000
  - USD: 0

Total Assets (in KRW): 2,000,000
```

**Transactions:**
```sql
INSERT INTO transaction VALUES (
  301,  -- id
  3,    -- account_id
  'Exchange',
  'KRW',  -- ticker (currency being sold)
  NULL,   -- quantity
  NULL,   -- price
  -1300000.00,  -- amount
  '2024-01-15',
  302,  -- linked_tx_id
  'Exchange KRW to USD',
  '2024-01-15 11:00:00',
  NULL
);

INSERT INTO transaction VALUES (
  302,
  3,
  'Exchange',
  'USD',  -- ticker (currency being bought)
  NULL,
  NULL,
  1000.00,
  '2024-01-15',
  301,  -- linked_tx_id
  'Exchange KRW to USD',
  '2024-01-15 11:00:00',
  NULL
);
```

**After:**
```
Account: Foreign Currency Account (ID=3)
  - KRW: 700,000
  - USD: 1,000

Total Assets (in KRW): 700,000 + (1,000 × 1,300) = 2,000,000  ← UNCHANGED
```

**Later (when exchange rate changes to 1 USD = 1,350 KRW):**
```
Account: Foreign Currency Account (ID=3)
  - KRW: 700,000
  - USD: 1,000 (current rate: 1,350 KRW)

Total Assets (in KRW): 700,000 + (1,000 × 1,350) = 2,050,000  ← INCREASED by 50,000
```

---

### Validation Rules

```python
def validate_exchange(from_ticker: str, to_ticker: str, from_amount: float,
                      to_amount: float, account_id: int, db: Session):
    """Validate currency exchange transaction."""
    # Check both currencies are different
    if from_ticker == to_ticker:
        raise ValueError("Cannot exchange same currency")

    # Check amounts are positive
    if from_amount <= 0 or to_amount <= 0:
        raise ValueError("Exchange amounts must be positive")

    # Check sufficient balance in source currency
    source_holding = db.query(Holding).filter(
        Holding.account_id == account_id,
        Holding.ticker == from_ticker
    ).first()

    if not source_holding or source_holding.quantity < from_amount:
        raise ValueError(f"Insufficient {from_ticker} balance")

    # Calculate and validate exchange rate
    exchange_rate = from_amount / to_amount

    # Fetch market rate for comparison (warning only)
    market_rate = get_exchange_rate(to_ticker, from_ticker, datetime.now(), db)
    if market_rate:
        deviation = abs(exchange_rate - market_rate) / market_rate
        if deviation > 0.05:  # >5% deviation
            print(f"Warning: Exchange rate deviates {deviation*100:.1f}% from market rate")
```

---

## Pattern ④+② Cross-Account Exchange-Transfer

**Reality:** Transferring money from/to a Foreign Currency Account requires automatic currency conversion.

**Examples:**
- Transfer USD from Foreign Currency Account to Deposit Account (convert to KRW first)
- Transfer KRW from Deposit Account to Foreign Currency Account holding USD (convert to USD after transfer)

**Characteristic:** Two accounts involved, one must be ForeignCurrency type, creates 4 transactions total (Exchange + Transfer), total asset value unchanged.

**Important:** Direct transfers between two Foreign Currency accounts are NOT supported. User must perform separate Exchange and Transfer operations.

---

### Implementation

This is a composite operation that combines Pattern ④ (Exchange) and Pattern ② (Transfer):

**Case 1: Foreign Currency Account → Non-Foreign Currency Account**

1. Exchange foreign currency to KRW in source account (2 transactions, Pattern ④)
2. Transfer KRW from source to target account (2 transactions, Pattern ②)
3. Total: 4 transactions

**Case 2: Non-Foreign Currency Account → Foreign Currency Account**

1. Transfer KRW from source to target account (2 transactions, Pattern ②)
2. Exchange KRW to foreign currency in target account (2 transactions, Pattern ④)
3. Total: 4 transactions

**Database Operations:**

```python
# Case 1: Foreign Currency (USD) → Deposit (KRW)
# Assumption: Source has 100 USD, rate = 1 USD = 1,300 KRW

# Step 1a: Exchange USD → KRW in source account
tx1 = Transaction(
    account_id=source_account_id,
    type="Exchange",
    ticker="USD",
    amount=-100.00,  # Sell USD
    date=transaction_date,
    linked_tx_id=None  # Will be set to tx2.id
)

tx2 = Transaction(
    account_id=source_account_id,
    type="Exchange",
    ticker="KRW",
    amount=130000.00,  # Receive KRW
    date=transaction_date,
    linked_tx_id=tx1.id
)

# Step 1b: Update holdings in source account
usd_holding.quantity -= 100  # Decrease USD
krw_holding.quantity += 130000  # Increase KRW

# Step 2a: Transfer KRW between accounts
tx3 = Transaction(
    account_id=source_account_id,
    type="Transfer_Out",
    ticker="KRW",
    amount=-130000.00,  # Send KRW
    date=transaction_date,
    linked_tx_id=None  # Will be set to tx4.id
)

tx4 = Transaction(
    account_id=target_account_id,
    type="Transfer_In",
    ticker="KRW",
    amount=130000.00,  # Receive KRW
    date=transaction_date,
    linked_tx_id=tx3.id
)

# Step 2b: Update KRW holdings in both accounts
source_krw_holding.quantity -= 130000
target_krw_holding.quantity += 130000
```

---

### Cross-Account Exchange-Transfer Example

**Scenario:** Transfer $100 USD from Foreign Currency Account to Deposit Account

**Before:**
```
Source Account: Foreign Currency Account (ID=1)
  - USD: 100
  - KRW: 0
Total Value: 130,000 KRW (at rate 1 USD = 1,300 KRW)

Target Account: Deposit Account (ID=2)
  - KRW: 500,000
Total Value: 500,000 KRW

Overall Total Assets: 630,000 KRW
```

**Transactions Created:**
```sql
-- Exchange: USD → KRW in source account
INSERT INTO transaction VALUES (401, 1, 'Exchange', 'USD', NULL, NULL, -100.00, '2024-01-20', 402, 'Exchange for transfer', ...);
INSERT INTO transaction VALUES (402, 1, 'Exchange', 'KRW', NULL, NULL, 130000.00, '2024-01-20', 401, 'Exchange for transfer', ...);

-- Transfer: KRW from source to target
INSERT INTO transaction VALUES (403, 1, 'Transfer_Out', 'KRW', NULL, NULL, -130000.00, '2024-01-20', 404, 'Transfer to deposit', ...);
INSERT INTO transaction VALUES (404, 2, 'Transfer_In', 'KRW', NULL, NULL, 130000.00, '2024-01-20', 403, 'Transfer to deposit', ...);
```

**After:**
```
Source Account: Foreign Currency Account (ID=1)
  - USD: 0
  - KRW: 0
Total Value: 0 KRW

Target Account: Deposit Account (ID=2)
  - KRW: 630,000
Total Value: 630,000 KRW

Overall Total Assets: 630,000 KRW (UNCHANGED)
```

---

### API Usage

**Backend Endpoint:**
```http
POST /api/transactions/exchange
Content-Type: application/json

{
  "account_id": 1,
  "from_ticker": "USD",
  "to_ticker": "KRW",
  "from_amount": 100,
  "to_amount": 130000,
  "to_account_id": 2,
  "date": "2024-01-20T10:00:00",
  "description": "Transfer USD to deposit account"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "exchange_sell_id": 401,
    "exchange_buy_id": 402,
    "transfer_out_id": 403,
    "transfer_in_id": 404
  }
}
```

---

### Validation Rules

```python
def validate_cross_account_exchange(
    source_account: Account,
    target_account: Account,
    from_ticker: str,
    to_ticker: str
) -> None:
    """Validate cross-account exchange-transfer constraints."""

    # Rule 1: Cannot transfer between two Foreign Currency accounts
    if (source_account.type == 'ForeignCurrency' and
        target_account.type == 'ForeignCurrency'):
        raise ValueError(
            "Transfer between Foreign Currency accounts not supported. "
            "Use separate Exchange and Transfer operations."
        )

    # Rule 2: Foreign → Non-Foreign must convert to KRW
    if (source_account.type == 'ForeignCurrency' and
        target_account.type != 'ForeignCurrency'):
        if to_ticker != 'KRW':
            raise ValueError(
                "Must convert to KRW before transferring to non-Foreign Currency account"
            )

    # Rule 3: Non-Foreign → Foreign must use KRW
    if (source_account.type != 'ForeignCurrency' and
        target_account.type == 'ForeignCurrency'):
        if from_ticker != 'KRW':
            raise ValueError(
                "Must transfer KRW to Foreign Currency account before exchange"
            )

    # Rule 4: Both accounts must exist and be active
    if not source_account or not target_account:
        raise ValueError("Source and target accounts must exist")

    if source_account.deleted_at or target_account.deleted_at:
        raise ValueError("Cannot transfer to/from deleted accounts")
```

---

## Pattern Summary Table

| Pattern | Accounts Involved | Holdings Updated | Total Assets Change | Linked Transactions |
|---------|-------------------|------------------|---------------------|---------------------|
| ① Income/Expense | 1 | 1 (CASH) | Yes | No |
| ② Transfer | 2 | 2 (both CASH) | No | Yes (2 transactions) |
| ③ Buy/Sell | 1 | 2 (CASH + ticker) | No (at transaction time) | No |
| ~~④ Exchange~~ | ~~1~~ | ~~2 (currency A + B)~~ | ~~No~~ | **REMOVED** |
| ④+② Cross-Account Exchange-Transfer | 2 | 4 (2 in each account) | No | Yes (4 transactions total) |

---

## Service Layer Implementation

**Complete service method example:**

```python
from sqlalchemy.orm import Session
from datetime import datetime
from models import Transaction, Holding, Account, MarketData
from decimal import Decimal

class TransactionService:
    """Business logic for transaction operations."""

    def create_buy_transaction(
        self,
        account_id: int,
        ticker: str,
        quantity: Decimal,
        price: Decimal,
        transaction_date: date,
        description: str,
        db: Session
    ) -> Transaction:
        """
        Create a buy transaction (Pattern ③).

        Args:
            account_id: Account ID
            ticker: Stock ticker symbol
            quantity: Number of shares to buy
            price: Price per share
            transaction_date: Date of transaction
            description: User notes
            db: Database session

        Returns:
            Created transaction

        Raises:
            ValueError: If validation fails
        """
        # Validate
        account = db.query(Account).get(account_id)
        if not account:
            raise ValueError("Account not found")

        if quantity <= 0 or price <= 0:
            raise ValueError("Quantity and price must be positive")

        cash_needed = quantity * price

        # Check sufficient cash
        cash_holding = db.query(Holding).filter(
            Holding.account_id == account_id,
            Holding.ticker == "CASH"
        ).first()

        if not cash_holding or cash_holding.quantity < cash_needed:
            raise ValueError(f"Insufficient cash (need {cash_needed})")

        # Create transaction
        transaction = Transaction(
            account_id=account_id,
            type="Buy",
            ticker=ticker,
            quantity=quantity,
            price=price,
            amount=-cash_needed,  # Negative for cash outflow
            date=transaction_date,
            description=description
        )
        db.add(transaction)
        db.flush()

        # Update CASH holding
        cash_holding.quantity -= cash_needed

        # Update stock holding
        stock_holding = db.query(Holding).filter(
            Holding.account_id == account_id,
            Holding.ticker == ticker
        ).first()

        if not stock_holding:
            stock_holding = Holding(
                account_id=account_id,
                ticker=ticker,
                quantity=0,
                avg_price=0
            )
            db.add(stock_holding)

        # Calculate new average price
        total_value = (stock_holding.quantity * stock_holding.avg_price) + (quantity * price)
        total_qty = stock_holding.quantity + quantity
        stock_holding.avg_price = total_value / total_qty
        stock_holding.quantity = total_qty

        # Trigger recalculation if past transaction
        if transaction_date < datetime.now():
            self.recalculate_from_date(transaction_date, db)

        db.commit()
        return transaction

    def recalculate_from_date(self, start_date: date, db: Session):
        """
        Recalculate holdings and snapshots from a specific date.
        Called when a past transaction is inserted.
        """
        # Implementation in SETUP.md
        pass
```

---

## Testing Transaction Patterns

**Unit test examples:**

```python
import pytest
from decimal import Decimal
from datetime import datetime

def test_deposit_transaction(db_session):
    """Test Pattern ① - Deposit."""
    # Setup
    account = create_test_account("Checking", db_session)

    # Execute
    service = TransactionService()
    tx = service.create_deposit(
        account_id=account.id,
        amount=Decimal("1000.00"),
        transaction_date=datetime.now(),
        description="Test deposit",
        db=db_session
    )

    # Verify
    assert tx.type == "Deposit"
    assert tx.amount == Decimal("1000.00")

    cash_holding = db_session.query(Holding).filter(
        Holding.account_id == account.id,
        Holding.ticker == "CASH"
    ).first()

    assert cash_holding.quantity == Decimal("1000.00")

def test_transfer_transaction(db_session):
    """Test Pattern ② - Transfer."""
    # Setup
    account1 = create_test_account("Checking", db_session)
    account2 = create_test_account("Brokerage", db_session)

    # Fund account1
    fund_account(account1.id, Decimal("1000.00"), db_session)

    # Execute
    service = TransactionService()
    tx_out, tx_in = service.create_transfer(
        from_account_id=account1.id,
        to_account_id=account2.id,
        amount=Decimal("500.00"),
        transaction_date=datetime.now(),
        description="Test transfer",
        db=db_session
    )

    # Verify transactions are linked
    assert tx_out.linked_tx_id == tx_in.id
    assert tx_in.linked_tx_id == tx_out.id

    # Verify amounts
    assert tx_out.amount == Decimal("-500.00")
    assert tx_in.amount == Decimal("500.00")

    # Verify holdings
    cash1 = get_cash_holding(account1.id, db_session)
    cash2 = get_cash_holding(account2.id, db_session)

    assert cash1.quantity == Decimal("500.00")
    assert cash2.quantity == Decimal("500.00")

def test_buy_transaction(db_session):
    """Test Pattern ③ - Buy stock."""
    # Setup
    account = create_test_account("Brokerage", db_session)
    fund_account(account.id, Decimal("2000.00"), db_session)

    # Execute
    service = TransactionService()
    tx = service.create_buy_transaction(
        account_id=account.id,
        ticker="AAPL",
        quantity=Decimal("10"),
        price=Decimal("150.00"),
        transaction_date=datetime.now(),
        description="Buy Apple",
        db=db_session
    )

    # Verify cash decreased
    cash = get_cash_holding(account.id, db_session)
    assert cash.quantity == Decimal("500.00")  # 2000 - 1500

    # Verify stock holding created
    stock = get_holding(account.id, "AAPL", db_session)
    assert stock.quantity == Decimal("10")
    assert stock.avg_price == Decimal("150.00")

def test_exchange_transaction(db_session):
    """Test Pattern ④ - Currency exchange."""
    # Setup
    account = create_test_account("Foreign", db_session)
    fund_account_currency(account.id, "KRW", Decimal("2000000.00"), db_session)

    # Execute
    service = TransactionService()
    tx_sell, tx_buy = service.create_exchange(
        account_id=account.id,
        from_ticker="KRW",
        to_ticker="USD",
        from_amount=Decimal("1300000.00"),
        to_amount=Decimal("1000.00"),
        transaction_date=datetime.now(),
        description="Buy USD",
        db=db_session
    )

    # Verify transactions linked
    assert tx_sell.linked_tx_id == tx_buy.id
    assert tx_buy.linked_tx_id == tx_sell.id

    # Verify holdings
    krw = get_holding(account.id, "KRW", db_session)
    usd = get_holding(account.id, "USD", db_session)

    assert krw.quantity == Decimal("700000.00")
    assert usd.quantity == Decimal("1000.00")
```

---

## Common Mistakes to Avoid

1. **Forgetting to link transfer transactions:**
   ```python
   # ❌ WRONG - Missing linked_tx_id
   tx_out = Transaction(type="Transfer_Out", ...)
   tx_in = Transaction(type="Transfer_In", ...)

   # ✅ CORRECT
   tx_out.linked_tx_id = tx_in.id
   tx_in.linked_tx_id = tx_out.id
   ```

2. **Changing avg_price on sell:**
   ```python
   # ❌ WRONG
   if transaction.type == "Sell":
       holding.avg_price = transaction.price  # NO!

   # ✅ CORRECT
   if transaction.type == "Sell":
       holding.quantity -= transaction.quantity
       # avg_price stays the same
   ```

3. **Not recalculating on past transactions:**
   ```python
   # ❌ WRONG - Forgetting time-travel recalculation
   if transaction.date < datetime.now():
       pass  # Do nothing

   # ✅ CORRECT
   if transaction.date < datetime.now():
       recalculate_from_date(transaction.date, db)
   ```

4. **Using float instead of Decimal:**
   ```python
   # ❌ WRONG - Float precision issues
   amount = 1500.00

   # ✅ CORRECT
   from decimal import Decimal
   amount = Decimal("1500.00")
   ```

5. **Not validating sufficient balance:**
   ```python
   # ❌ WRONG - No balance check
   cash_holding.quantity -= transaction.amount

   # ✅ CORRECT
   if cash_holding.quantity < transaction.amount:
       raise ValueError("Insufficient balance")
   cash_holding.quantity -= transaction.amount
   ```
