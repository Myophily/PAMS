# RULES.md - Personal Asset Manager

## Core Development Principles

### 1. Reality Mirroring
- **Transaction Accuracy:** All financial activities must be recorded exactly as they occurred in reality
- **No Arbitrary Modifications:** Never directly modify current balances; all state changes must flow through transaction logs
- **Temporal Integrity:** When entering past transactions, always use the market data (exchange rates, stock prices) from that specific date

### 2. Data Integrity

#### Transaction Constraints
- Every transaction MUST have a valid `transaction_date` (the actual date it occurred)
- Linked transactions (transfers, exchanges) MUST maintain referential integrity via `Linked_Tx_ID`
- Total asset calculations MUST be deterministic and reproducible from transaction logs

#### Four Core Transaction Patterns

PAM formalizes the flow of money in reality into 4 fundamental patterns:

**Pattern ① Pure Income/Expense**
- **Rule:** The cash balance of a single account increases or decreases. Total assets change.
- **Examples:** Salary deposit, food expense, bill payment
- **Implementation:** Single `Transaction` record with type `Deposit`, `Withdrawal`, or `Dividend`
- **Validation:** Amount must be non-zero, account must exist

**Pattern ② Simple Transfer**
- **Rule:** Two linked transactions (Transfer_Out + Transfer_In). Total assets unchanged.
- **Example:** Transfer from Toss account → Kiwoom Securities account
- **Implementation:**
  - Create two `Transaction` records
  - Both must reference each other via `Linked_Tx_ID` (bidirectional)
  - Amounts must be equal but opposite signs
- **Validation:** Both transactions must exist, linked_tx_id must be mutual, total assets before = total assets after

**Pattern ③ Asset Form Conversion (Invest/Liquidate)**
- **Rule:** Cash decreases + Stock quantity increases within the same account. Total asset value unchanged at transaction time.
- **Example:** Buying Samsung Electronics with cash in a securities account
- **Implementation:**
  - Single `Transaction` record with type `Buy` or `Sell`
  - Updates two `Holding` records in the same account: CASH and the ticker
- **Validation:** Cash balance must be sufficient, quantity must be positive

**Pattern ④ Exchange**
- **Rule:** Withdrawal from Account A (KRW) + Deposit into Account A (USD). Exchange ratio recorded.
- **Example:** Selling KRW to buy USD
- **Implementation:**
  - Two `Transaction` records for the same account
  - Exchange rate must be recorded from `MarketData` or manual input
- **Validation:** Both currencies must be valid, exchange rate must be positive

### 3. Code Organization

#### Backend (FastAPI)
- **One responsibility per endpoint:** Each API route should handle exactly one business operation
- **Transaction atomicity:** Database operations that modify multiple records MUST use transactions
- **Calculation consistency:** All asset valuations must use the same market data snapshot
- **Error handling:** Always validate transaction data before persisting

#### Frontend (Next.js)
- **Server-side data fetching:** Use Next.js App Router patterns for initial data loads
- **Optimistic updates:** UI should reflect changes immediately, with rollback on failure
- **Type safety:** All API responses must be typed (TypeScript interfaces)
- **Rewrite proxy:** All backend calls go through `/api/*` rewrites to avoid CORS

### 4. Database Rules

#### Schema Constraints
- `Account.type` MUST be one of: `Checking`, `Brokerage`, `Foreign`, `MMF`
- `Transaction.type` MUST be one of: `Buy`, `Sell`, `Transfer_In`, `Transfer_Out`, `Deposit`, `Withdrawal`, `Dividend`, `Exchange`
- `Holding.ticker` includes special value `CASH` for account balances
- `MarketData` MUST have unique constraint on `(date, ticker)`

#### Data Consistency
- `Holding` table is a **computed state** - it should always be derivable from `Transaction` history
- When inserting a past transaction, trigger recalculation of all `Holding` and `AssetSnapshot` records after that date
- Soft delete transactions (mark as deleted) rather than hard delete to maintain audit trail

### 5. File Structure

```
PAM/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   ├── routers/             # API endpoint definitions
│   │   ├── services/            # Business logic layer
│   │   └── utils/               # Helper functions (calculations, market data)
│   ├── .env                     # Environment variables (API keys, DB path)
│   └── requirements.txt         # Python dependencies
├── frontend/
│   ├── app/                     # Next.js App Router
│   │   ├── page.tsx             # Dashboard (home page)
│   │   ├── accounts/            # Account list & details pages
│   │   │   ├── page.tsx         # Account list view
│   │   │   └── [id]/page.tsx    # Account detail view
│   │   └── api/                 # API route proxies (CORS handling)
│   ├── components/              # Reusable UI components
│   ├── lib/
│   │   ├── hooks/               # React Query hooks
│   │   └── types.ts             # TypeScript interfaces
│   └── package.json
├── asset_data.db                # SQLite database file
├── RULES.md                     # This file
├── CONTEXT.md                   # Project overview
├── TODO.md                      # Development roadmap
└── CLAUDE.md                    # AI assistant instructions
```

### 6. Testing Requirements

- **Unit tests:** All calculation functions (avg price, P/L, asset valuation)
- **Integration tests:** Transaction flow end-to-end
- **Data validation tests:** Ensure transaction linking works correctly
- **Time travel tests:** Verify past transaction insertion recalculates correctly

### 7. Security & Privacy

- **Local-first:** No data leaves the user's machine
- **No authentication:** Since it's single-user local app
- **Amount privacy:** Implement UI toggle to hide/show monetary values
- **Backup responsibility:** User owns the `.db` file backup

### 8. Performance Constraints

- **Calculation efficiency:** Asset graph recalculation should complete within 1 second for 10,000 transactions
- **UI responsiveness:** Dashboard should load within 500ms
- **Market data caching:** Cache exchange rates and stock prices to minimize API calls

### 9. Coding Style

#### Python (Backend)
- Follow PEP 8
- Use type hints for all functions
- Prefer `Decimal` over `float` for monetary calculations
- Use `datetime` objects, not strings, for dates

#### TypeScript (Frontend)
- Strict mode enabled
- Prefer functional components with hooks
- Use `const` by default
- Explicit return types for functions

### 10. Version Control

- **Atomic commits:** Each commit should represent one logical change
- **Descriptive messages:** Use conventional commits format
- **No secrets in repo:** `.env` files must be gitignored
- **Database in gitignore:** `asset_data.db` should never be committed

### 11. Market Data Policy

- **External API:** Use a free API (e.g., Alpha Vantage, Yahoo Finance) for stock prices and exchange rates
- **Graceful degradation:** If API fails, allow manual price entry
- **Historical accuracy:** When fetching past data, always request the specific date's closing price
- **Caching strategy:** Store fetched market data in `MarketData` table to avoid redundant API calls
