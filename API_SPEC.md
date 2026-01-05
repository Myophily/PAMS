# API_SPEC.md - Personal Asset Manager

Complete API endpoint specifications for the PAM backend.

## Base URL

**Local Development:** `http://localhost:8000`
**Frontend Proxy:** `/api` (Next.js rewrites to `localhost:8000`)

---

## Authentication

**Not implemented** - This is a single-user local application with no authentication.

---

## Common Response Formats

### Success Response
```json
{
  "status": "success",
  "data": { /* endpoint-specific data */ }
}
```

### Error Response
```json
{
  "status": "error",
  "message": "Human-readable error description",
  "code": "ERROR_CODE",
  "details": { /* optional error details */ }
}
```

---

## Endpoints

### 1. Accounts

#### `POST /api/accounts`
Create a new account.

**Request Body:**
```json
{
  "name": "Toss Checking",
  "type": "Checking",  // Checking | Brokerage | Foreign | MMF
  "currency": "KRW",   // KRW | USD | EUR | etc.
  "initial_balance": 1000000.00,
  "initial_balance_date": "2024-01-01"  // Optional, defaults to today
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "id": 1,
    "name": "Toss Checking",
    "type": "Checking",
    "currency": "KRW",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

**Business Logic:**
1. Create `Account` record
2. Create initial `Transaction` record with type `Deposit` if `initial_balance` > 0
3. Create `Holding` record for `CASH` with the initial balance
4. Fetch market data (exchange rate) for `initial_balance_date` if not today

**Validation:**
- `name` must be unique per user
- `type` must be valid enum value
- `currency` must be valid currency code
- `initial_balance` must be >= 0

---

#### `GET /api/accounts`
List all accounts.

**Query Parameters:**
- `type` (optional) - Filter by account type
- `currency` (optional) - Filter by currency

**Response:**
```json
{
  "status": "success",
  "data": {
    "accounts": [
      {
        "id": 1,
        "name": "Toss Checking",
        "type": "Checking",
        "currency": "KRW",
        "balance": 1500000.00,
        "balance_usd": 1153.85,  // Converted using current exchange rate
        "holdings_count": 1  // Number of different assets (including CASH)
      }
    ]
  }
}
```

**Business Logic:**
1. Query all accounts
2. For each account, calculate current balance by summing holdings
3. Convert balance to USD using latest exchange rate from `MarketData`

---

#### `GET /api/accounts/{id}`
Get detailed account information.

**Path Parameters:**
- `id` - Account ID

**Response:**
```json
{
  "status": "success",
  "data": {
    "account": {
      "id": 1,
      "name": "Kiwoom Brokerage",
      "type": "Brokerage",
      "currency": "KRW",
      "created_at": "2024-01-01T00:00:00Z"
    },
    "summary": {
      "total_value": 5000000.00,  // Current total value
      "cash_balance": 1000000.00,
      "invested_amount": 4000000.00,  // Cost basis
      "unrealized_pl": 500000.00,  // Profit/Loss
      "unrealized_pl_percent": 12.5
    },
    "holdings": [
      {
        "ticker": "CASH",
        "quantity": 1000000.00,
        "avg_price": 1.0,
        "current_price": 1.0,
        "current_value": 1000000.00,
        "cost_basis": 1000000.00,
        "unrealized_pl": 0.00,
        "unrealized_pl_percent": 0.00
      },
      {
        "ticker": "005930.KS",
        "ticker_name": "Samsung Electronics",
        "quantity": 50,
        "avg_price": 70000.00,
        "current_price": 80000.00,
        "current_value": 4000000.00,
        "cost_basis": 3500000.00,
        "unrealized_pl": 500000.00,
        "unrealized_pl_percent": 14.29
      }
    ]
  }
}
```

**Business Logic:**
1. Fetch account details
2. Query all holdings for this account
3. For each holding (except CASH):
   - Fetch current price from `MarketData` (latest date)
   - Calculate current value = quantity × current_price
   - Calculate cost basis = quantity × avg_price
   - Calculate unrealized P/L
4. Sum all holdings for summary statistics

---

#### `PUT /api/accounts/{id}`
Update account name or settings.

**Request Body:**
```json
{
  "name": "New Account Name"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "id": 1,
    "name": "New Account Name",
    "type": "Checking",
    "currency": "KRW"
  }
}
```

**Validation:**
- Cannot change `type` or `currency` after creation (would invalidate transaction history)

---

#### `DELETE /api/accounts/{id}`
Soft delete an account.

**Response:**
```json
{
  "status": "success",
  "message": "Account deleted successfully"
}
```

**Business Logic:**
1. Check if account has transactions - if yes, soft delete only (mark as deleted)
2. If no transactions, hard delete account and related holdings
3. Recalculate total assets after deletion

**Validation:**
- Cannot delete account with active holdings (must liquidate first)

---

### 2. Transactions

#### `POST /api/transactions`
Create a new transaction.

**Request Body (Deposit/Withdrawal):**
```json
{
  "account_id": 1,
  "type": "Deposit",  // Deposit | Withdrawal
  "amount": 1000000.00,
  "date": "2024-01-15",
  "description": "Monthly salary"  // Optional
}
```

**Request Body (Buy/Sell):**
```json
{
  "account_id": 2,
  "type": "Buy",  // Buy | Sell
  "ticker": "005930.KS",
  "quantity": 10,
  "price": 70000.00,
  "date": "2024-01-15",
  "description": "Samsung stock purchase"  // Optional
}
```

**Request Body (Transfer):**
```json
{
  "type": "Transfer",
  "from_account_id": 1,
  "to_account_id": 2,
  "amount": 500000.00,
  "date": "2024-01-15",
  "description": "Fund brokerage account"  // Optional
}
```

**Request Body (Exchange):**
```json
{
  "account_id": 3,
  "type": "Exchange",
  "from_ticker": "KRW",
  "to_ticker": "USD",
  "from_amount": 1300000.00,
  "to_amount": 1000.00,
  "exchange_rate": 1300.00,  // Optional, auto-fetch if not provided
  "date": "2024-01-15",
  "description": "Buy USD for travel"  // Optional
}
```

**Request Body (Dividend):**
```json
{
  "account_id": 2,
  "type": "Dividend",
  "ticker": "AAPL",
  "amount": 50.00,  // Dividend amount received
  "date": "2024-01-15",
  "description": "Apple quarterly dividend"  // Optional
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "transaction_id": 123,
    "linked_transaction_id": 124,  // Only for Transfer/Exchange
    "message": "Transaction recorded successfully"
  }
}
```

**Business Logic:**

**For Deposit/Withdrawal (Pattern ①):**
1. Create single `Transaction` record
2. Update `Holding` for CASH in the account
3. If date is in past, trigger recalculation from that date

**For Buy/Sell (Pattern ③):**
1. Create single `Transaction` record
2. Update two `Holding` records:
   - CASH: decrease/increase by (quantity × price)
   - Ticker: increase/decrease quantity, recalculate avg_price
3. Fetch market data for the date if not cached
4. If date is in past, trigger recalculation

**For Transfer (Pattern ②):**
1. Create two linked `Transaction` records (Transfer_Out + Transfer_In)
2. Set mutual `linked_tx_id` references
3. Update `Holding` for CASH in both accounts
4. Validate total assets before = total assets after

**For Exchange (Pattern ④):**
1. Create two `Transaction` records for same account
2. Update two `Holding` records (e.g., KRW and USD)
3. Record exchange rate in `MarketData` if not exists
4. Validate amounts match exchange rate

**For Dividend:**
1. Create single `Transaction` record with type `Dividend`
2. Update `Holding` for CASH (increase)
3. Total assets increase by dividend amount

**Validation:**
- `date` cannot be in the future
- For Buy: account must have sufficient cash
- For Transfer: from_account must have sufficient balance
- For Exchange: exchange rate must be positive
- All monetary amounts must be > 0

---

#### `GET /api/transactions`
List transactions with filtering and pagination.

**Query Parameters:**
- `account_id` (optional) - Filter by account
- `type` (optional) - Filter by transaction type
- `start_date` (optional) - Filter by date range (inclusive)
- `end_date` (optional) - Filter by date range (inclusive)
- `ticker` (optional) - Filter by ticker symbol
- `limit` (optional, default: 50) - Number of results per page
- `offset` (optional, default: 0) - Pagination offset

**Response:**
```json
{
  "status": "success",
  "data": {
    "transactions": [
      {
        "id": 123,
        "account_id": 2,
        "account_name": "Kiwoom Brokerage",
        "type": "Buy",
        "ticker": "005930.KS",
        "quantity": 10,
        "price": 70000.00,
        "amount": -700000.00,  // Negative for cash outflow
        "date": "2024-01-15",
        "description": "Samsung stock purchase",
        "linked_tx_id": null,
        "created_at": "2024-01-15T10:30:00Z"
      }
    ],
    "total": 245,  // Total matching transactions
    "limit": 50,
    "offset": 0
  }
}
```

**Business Logic:**
1. Query `Transaction` table with filters
2. Join with `Account` table to get account name
3. Order by date DESC (most recent first)
4. Apply pagination

---

#### `GET /api/transactions/{id}`
Get single transaction details.

**Response:**
```json
{
  "status": "success",
  "data": {
    "transaction": {
      "id": 123,
      "account_id": 2,
      "account_name": "Kiwoom Brokerage",
      "type": "Buy",
      "ticker": "005930.KS",
      "ticker_name": "Samsung Electronics",
      "quantity": 10,
      "price": 70000.00,
      "amount": -700000.00,
      "date": "2024-01-15",
      "description": "Samsung stock purchase",
      "linked_tx_id": null,
      "created_at": "2024-01-15T10:30:00Z"
    },
    "market_data": {
      "price_at_transaction": 70000.00,
      "current_price": 80000.00,
      "price_change_percent": 14.29
    }
  }
}
```

---

#### `PUT /api/transactions/{id}`
Edit an existing transaction.

**Request Body:**
```json
{
  "amount": 1100000.00,
  "description": "Updated description"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "transaction": { /* updated transaction */ }
  }
}
```

**Business Logic:**
1. Validate change doesn't violate transaction pattern rules
2. Update `Transaction` record
3. Recalculate holdings from transaction date forward
4. Update `AssetSnapshot` records if needed

**Validation:**
- Cannot change `type`, `account_id`, or `date` (would invalidate history)
- For linked transactions (transfers), must update both transactions

---

#### `DELETE /api/transactions/{id}`
Soft delete a transaction.

**Response:**
```json
{
  "status": "success",
  "message": "Transaction deleted successfully"
}
```

**Business Logic:**
1. Mark transaction as deleted (soft delete)
2. If linked transaction exists, mark it as deleted too
3. Recalculate holdings from transaction date forward
4. Update `AssetSnapshot` records

**Validation:**
- Cannot delete if it would result in negative balance

---

### 3. Dashboard

#### `GET /api/dashboard/summary`
Get total assets summary and statistics.

**Response:**
```json
{
  "status": "success",
  "data": {
    "total_assets": {
      "krw": 10000000.00,
      "usd": 7692.31
    },
    "current_exchange_rate": {
      "usd_to_krw": 1300.00,
      "updated_at": "2024-01-15T09:00:00Z"
    },
    "changes": {
      "day": {
        "amount_krw": 50000.00,
        "amount_usd": 38.46,
        "percent": 0.5
      },
      "month": {
        "amount_krw": 200000.00,
        "amount_usd": 153.85,
        "percent": 2.0
      },
      "year": {
        "amount_krw": 1000000.00,
        "amount_usd": 769.23,
        "percent": 10.0
      }
    },
    "allocation": {
      "by_type": [
        { "type": "Cash", "value_krw": 3000000.00, "percent": 30.0 },
        { "type": "Stocks", "value_krw": 6000000.00, "percent": 60.0 },
        { "type": "Foreign Currency", "value_krw": 1000000.00, "percent": 10.0 }
      ],
      "by_risk": [
        { "type": "Safe", "value_krw": 4000000.00, "percent": 40.0 },
        { "type": "Risk", "value_krw": 6000000.00, "percent": 60.0 }
      ]
    },
    "top_assets": [
      {
        "ticker": "005930.KS",
        "name": "Samsung Electronics",
        "value_krw": 4000000.00,
        "percent": 40.0
      },
      {
        "ticker": "CASH_KRW",
        "name": "Korean Won",
        "value_krw": 3000000.00,
        "percent": 30.0
      }
    ]
  }
}
```

**Business Logic:**
1. Query all accounts and holdings
2. Fetch current market prices for all tickers
3. Calculate total asset value in KRW and USD
4. Query `AssetSnapshot` for past dates to calculate changes
5. Group holdings by type and risk category
6. Sort by value to get top N assets

---

#### `GET /api/dashboard/chart`
Get asset volatility time series data.

**Query Parameters:**
- `period` (optional, default: "1M") - Time period: "1W" | "1M" | "3M" | "6M" | "1Y" | "ALL"
- `currency` (optional, default: "KRW") - Currency for values: "KRW" | "USD"

**Response:**
```json
{
  "status": "success",
  "data": {
    "chart_data": [
      {
        "date": "2024-01-01",
        "total_assets": 9500000.00,
        "principal": 9000000.00,  // Total deposited - withdrawn
        "gain_loss": 500000.00
      },
      {
        "date": "2024-01-02",
        "total_assets": 9550000.00,
        "principal": 9000000.00,
        "gain_loss": 550000.00
      }
      // ... more data points
    ],
    "period": "1M",
    "currency": "KRW"
  }
}
```

**Business Logic:**
1. Query `AssetSnapshot` table for the specified period
2. Filter by date range based on period parameter
3. Return daily snapshots (or aggregate by week/month for long periods)

---

### 4. Market Data

#### `GET /api/market-data/price`
Fetch stock price or exchange rate.

**Query Parameters:**
- `ticker` (required) - Stock ticker symbol or "USD", "EUR", etc.
- `date` (optional, default: today) - Date for historical price

**Response:**
```json
{
  "status": "success",
  "data": {
    "ticker": "AAPL",
    "date": "2024-01-15",
    "closing_price": 185.50,
    "currency": "USD",
    "source": "yahoo_finance",  // cache | yahoo_finance | alpha_vantage
    "cached": true
  }
}
```

**Business Logic:**
1. Check `MarketData` table for cached price
2. If not cached, fetch from external API (Yahoo Finance/Alpha Vantage)
3. Store fetched price in `MarketData` table
4. Return price

**Error Handling:**
- If API fails, return error with option to manually enter price
- If date is weekend/holiday, use closest previous trading day

---

#### `GET /api/market-data/exchange-rate`
Get exchange rate between two currencies.

**Query Parameters:**
- `from` (required) - Source currency (e.g., "KRW")
- `to` (required) - Target currency (e.g., "USD")
- `date` (optional, default: today) - Date for historical rate

**Response:**
```json
{
  "status": "success",
  "data": {
    "from": "USD",
    "to": "KRW",
    "rate": 1300.00,
    "date": "2024-01-15",
    "source": "cache"
  }
}
```

**Business Logic:**
1. Check `MarketData` table for cached rate
2. If not cached, fetch from external API
3. Store in `MarketData` table
4. Return rate

---

### 5. Holdings

#### `GET /api/holdings`
Get all holdings across all accounts.

**Query Parameters:**
- `account_id` (optional) - Filter by account
- `ticker` (optional) - Filter by ticker

**Response:**
```json
{
  "status": "success",
  "data": {
    "holdings": [
      {
        "id": 1,
        "account_id": 2,
        "account_name": "Kiwoom Brokerage",
        "ticker": "005930.KS",
        "ticker_name": "Samsung Electronics",
        "quantity": 50,
        "avg_price": 70000.00,
        "current_price": 80000.00,
        "current_value": 4000000.00,
        "cost_basis": 3500000.00,
        "unrealized_pl": 500000.00,
        "unrealized_pl_percent": 14.29
      }
    ]
  }
}
```

---

### 6. Recalculation (Internal)

#### `POST /api/internal/recalculate`
Trigger recalculation of holdings and snapshots from a specific date.

**Request Body:**
```json
{
  "start_date": "2024-01-01",
  "account_id": 2  // Optional, recalculate specific account only
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "recalculated_holdings": 15,
    "updated_snapshots": 45,
    "time_taken_ms": 234
  }
}
```

**Business Logic:**
1. Get all transactions from `start_date` to present
2. Replay transactions to rebuild holdings
3. Update `Holding` table
4. Regenerate `AssetSnapshot` records for affected date range

---

## Error Codes

| Code | Description |
|------|-------------|
| `ACCOUNT_NOT_FOUND` | Account does not exist |
| `INSUFFICIENT_BALANCE` | Not enough cash/quantity for transaction |
| `INVALID_DATE` | Date is in the future or invalid format |
| `INVALID_TRANSACTION_TYPE` | Transaction type not recognized |
| `LINKED_TX_MISSING` | Linked transaction reference broken |
| `MARKET_DATA_UNAVAILABLE` | Cannot fetch market data for date/ticker |
| `DUPLICATE_ACCOUNT_NAME` | Account name already exists |
| `CANNOT_DELETE_ACCOUNT` | Account has active holdings |

---

## Rate Limiting

**Not implemented** - Local application with no rate limits.

For external market data APIs:
- Yahoo Finance: ~2000 requests/hour (free tier)
- Alpha Vantage: 5 requests/minute (free tier)

Cache all fetched data in `MarketData` table to avoid hitting limits.

---

## Data Types

### Decimal Precision
- All monetary amounts: 2 decimal places
- Exchange rates: 4 decimal places
- Stock quantities: Integer (no fractional shares for MVP)
- Percentages: 2 decimal places

### Date Format
- API requests/responses: ISO 8601 (`YYYY-MM-DD`)
- Database storage: SQLite DATE type
- Timezone: All dates are in local timezone (no timezone conversion needed for local app)
