# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Project Context

**Personal Asset Manager (PAM)** is a local-first financial dashboard application - a professional Asset Management System (PMS) beyond a simple household ledger.

- **Backend:** FastAPI + SQLAlchemy + SQLite
- **Frontend:** Next.js 14 (App Router) + TypeScript + React Query
- **Architecture:** Standalone local application (no cloud deployment, no Docker/Nginx)

---

## 🚨 Essential Reading (READ THESE FIRST)

**CRITICAL:** Before making ANY changes to code, you MUST read these documents in order:

1. **[CONTEXT.md](CONTEXT.md)** → Project philosophy, core concepts, and architecture decisions
2. **[RULES.md](RULES.md)** → Development constraints and the 4 core transaction patterns
3. **[TODO.md](TODO.md)** → Current development priorities and roadmap

**Failure to read these will result in code that violates fundamental project principles.**

---

## 📚 Documentation Quick Reference

When you need detailed information on specific topics, refer to these files:

| Topic | File | Use When |
|-------|------|----------|
| **API endpoints** | [API_SPEC.md](API_SPEC.md) | Creating/modifying backend endpoints, request/response formats |
| **Database schema** | [DATABASE.md](DATABASE.md) | Querying or modifying database structure, understanding relationships |
| **Transaction logic** | [TRANSACTION_PATTERNS.md](TRANSACTION_PATTERNS.md) | Implementing transaction flows, calculation logic |
| **UI components** | [FRONTEND_COMPONENTS.md](FRONTEND_COMPONENTS.md) | Building/modifying frontend components, React Query hooks |
| **Setup & troubleshooting** | [SETUP.md](SETUP.md) | Setting up dev environment, fixing issues |

---

## Application Structure

### Pages & Routes
- **Dashboard (`/`)** → Total asset overview, allocation charts, volatility graph
- **Account List (`/accounts`)** → Card-based account management with action buttons
- **Account Details (`/accounts/[id]`)** → 3-tab view (Holdings, Transactions, Analysis)
- **Modals** → Account creation, transaction entry, transfers, exchanges

**For detailed component specs:** [FRONTEND_COMPONENTS.md](FRONTEND_COMPONENTS.md)

### Architecture Layers

**Backend (FastAPI):**
- **Routers** → HTTP request/response handling only
- **Services** → Business logic, implement 4 transaction patterns
- **Models** → Database schema (Account, Transaction, Holding, MarketData, AssetSnapshot)
- **Schemas** → Pydantic validation (mirror frontend TypeScript types)

**Frontend (Next.js):**
- **Pages** → Dashboard, Account List, Account Details
- **Components** → Reusable UI (Cards, Charts, Modals, Tables)
- **Hooks** → React Query for data fetching and state management
- **Types** → TypeScript interfaces (mirror backend schemas)

**Database (SQLite):**
- `Account` → Financial accounts
- `Transaction` → **Immutable log** (source of truth)
- `Holding` → **Computed state** (derived from transactions)
- `MarketData` → Cached prices and exchange rates
- `AssetSnapshot` → Daily total asset values

**For detailed specs:** [API_SPEC.md](API_SPEC.md), [DATABASE.md](DATABASE.md), [FRONTEND_COMPONENTS.md](FRONTEND_COMPONENTS.md)

---

## The Four Core Transaction Patterns

All financial activities in PAM must follow one of these 4 patterns. **For detailed implementation with SQL examples, calculation logic, and test cases:** [TRANSACTION_PATTERNS.md](TRANSACTION_PATTERNS.md)

| Pattern | Description | Accounts | Holdings | Total Assets | Linked? |
|---------|-------------|----------|----------|--------------|---------|
| **① Income/Expense** | Salary, expense, dividend | 1 | 1 (CASH) | **Changes** | No |
| **② Transfer** | Move money between accounts | 2 | 2 (CASH) | Unchanged | Yes |
| **③ Buy/Sell** | Convert cash ↔ stock | 1 | 2 (CASH + ticker) | Unchanged* | No |
| **④ Exchange** | Convert currency | 1 | 2 (currencies) | Unchanged* | Yes |

*Unchanged at transaction time; changes later due to market movements.

### Pattern Quick Reference

```python
# Pattern ① - Single transaction, total assets change
Transaction(account_id=1, type="Deposit", amount=1000, date=date.today())

# Pattern ② - Two linked transactions, total assets unchanged
tx1 = Transaction(account_id=1, type="Transfer_Out", amount=-500)
tx2 = Transaction(account_id=2, type="Transfer_In", amount=500)
tx1.linked_tx_id = tx2.id
tx2.linked_tx_id = tx1.id

# Pattern ③ - Single transaction, updates CASH + ticker
Transaction(account_id=2, type="Buy", ticker="AAPL", quantity=10, price=150, amount=-1500)

# Pattern ④ - Two linked transactions for same account, different currencies
tx1 = Transaction(account_id=3, type="Exchange", ticker="KRW", amount=-1300000)
tx2 = Transaction(account_id=3, type="Exchange", ticker="USD", amount=1000)
tx1.linked_tx_id = tx2.id
```

---

## 🔒 Critical Implementation Rules

### Data Integrity (NEVER violate these)

1. **Holdings are computed, not manual**
   `Holding` table is ALWAYS derived from `Transaction` history. Never modify holdings directly.

2. **Transactions are immutable**
   Use soft delete (`deleted_at`), never hard delete. Transaction history must be preserved.

3. **Linked transactions are bidirectional**
   `linked_tx_id` must reference each other mutually. Always validate both directions.

4. **Past transactions trigger recalculation**
   Update `Holding` and `AssetSnapshot` from that date forward. Never skip this step.

5. **Use Decimal for money**
   NEVER use `float` for monetary calculations. Always use `Decimal` type.

### Transaction Pattern Rules

- **Pattern ①:** 1 transaction → 1 holding → total assets **CHANGE**
- **Pattern ②:** 2 linked transactions → 2 holdings → total assets **UNCHANGED**
- **Pattern ③:** 1 transaction → 2 holdings (CASH + ticker) → total assets **UNCHANGED** at transaction time
- **Pattern ④:** 2 linked transactions → 2 holdings (currencies) → total assets **UNCHANGED** at transaction time
- **Pattern ④+②:** 4 linked transactions → 4 holdings (2 accounts) → total assets **UNCHANGED** (cross-account exchange-transfer)

### Account Type Transaction Enforcement

**NEW:** The backend enforces which transaction types are allowed on each account type:

- **Deposit accounts:** Only `Deposit`, `Withdrawal`, `Transfer_In`, `Transfer_Out` (cash operations only)
- **Securities accounts:** All transaction types including `Buy`, `Sell`, `Dividend` (full investment capabilities)
- **ForeignCurrency accounts:** `Deposit`, `Withdrawal`, `Exchange` only
  - **Transfer removed** - use Exchange with `to_account_id` for cross-account transfers
  - Cross-account transfers automatically convert currency and create 4 transactions
  - **Direct transfers between Foreign Currency accounts NOT SUPPORTED**
- **MoneyMarket accounts:** Cash operations + `Interest` (interest-earning accounts)

**Validation:** Attempting to create an invalid transaction type for an account (e.g., `Buy` on a Deposit account, or `Transfer_Out` on a ForeignCurrency account) will result in HTTP 400 error. See [TRANSACTION_PATTERNS.md](TRANSACTION_PATTERNS.md#transaction-type-restrictions-by-account-type) for full matrix.

### Type Safety

- **Backend:** Use Pydantic schemas for ALL API request/response models
- **Frontend:** Define TypeScript interfaces for ALL data structures
- **Never use `any`** → Use `unknown` and type guards if needed
- **Backend:** Use `Decimal` for money, `datetime.date` for dates
- **Frontend:** Mirror backend types exactly

---

## Common Implementation Patterns

### Adding a New Transaction Type

1. **Determine pattern** → Which of the 4 patterns does it follow?
2. **Determine allowed account types** → Which account types can use this transaction?
3. **Backend:**
   - Add enum to `Transaction.type` in `app/models/transaction.py`
   - Create Pydantic schema in `app/schemas/transaction_schema.py`
   - Update `ALLOWED_TRANSACTIONS` in `app/services/transaction_validation.py`
   - Implement business logic in `app/services/transaction_service.py`
   - Add API endpoint in `app/routers/transactions.py`
4. **Frontend:**
   - Update TypeScript types in `lib/types.ts`
   - Update `ACCOUNT_ACTIONS` in account components to show the action button
   - Create React Query hook in `lib/hooks/useTransactions.ts`
   - Create UI modal component
5. **Test** → Verify pattern rules are followed and account type validation works

**Detailed examples:** [TRANSACTION_PATTERNS.md](TRANSACTION_PATTERNS.md#service-layer-implementation)

### Creating a New API Endpoint

**Quick template:**
1. **Backend:** Router → Service → Model (separation of concerns)
2. **Frontend:** Hook → Component
3. **Types:** Mirror Pydantic schemas in TypeScript

**Complete examples:**
- Backend: [API_SPEC.md](API_SPEC.md)
- Frontend: [FRONTEND_COMPONENTS.md](FRONTEND_COMPONENTS.md#react-query-hooks)

### Time-Travel Recalculation

**CRITICAL:** When inserting a past transaction, you MUST trigger recalculation:

```python
if transaction.date < date.today():
    recalculate_from_date(transaction.date, db)
```

**Implementation details:** [TRANSACTION_PATTERNS.md](TRANSACTION_PATTERNS.md#common-mistakes-to-avoid)

---

## Development Workflow

### Quick Start

**Terminal 1 (Backend):**
```bash
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
uvicorn app.main:app --reload
```

**Terminal 2 (Frontend):**
```bash
cd frontend
npm run dev
```

**Browser:** `http://localhost:3000`

**Detailed setup:** [SETUP.md](SETUP.md)

---

## Code Review Checklist

### Backend
- [ ] All monetary values use `Decimal`, not `float`
- [ ] All dates use `datetime.date`, not strings
- [ ] Database operations use proper transactions (wrap multi-record operations)
- [ ] API endpoints have proper error handling (try/except)
- [ ] Pydantic schemas validate all inputs
- [ ] Business logic is in services, not routers
- [ ] Type hints are present on all functions
- [ ] Past transactions trigger `recalculate_from_date()`
- [ ] Transaction types are validated against account type (use `validate_transaction_type()`)

### Frontend
- [ ] API calls go through `/api/*` routes (Next.js rewrites)
- [ ] React Query is used for all data fetching
- [ ] Loading and error states are handled
- [ ] TypeScript interfaces match backend schemas
- [ ] Forms have validation
- [ ] Optimistic updates rollback on failure
- [ ] No inline styles (use Tailwind classes)

### Database
- [ ] Foreign key constraints are defined
- [ ] Unique constraints where needed (e.g., `(account_id, ticker)` on Holding)
- [ ] Indexes on frequently queried columns
- [ ] No direct SQL strings (use ORM)
- [ ] Transactions use bidirectional `linked_tx_id`

---

## Common Debugging Scenarios

| Issue | First Steps | Reference |
|-------|-------------|-----------|
| **Total assets don't match** | Query `Transaction` table → Check `Holding` calculation → Verify market data | [DATABASE.md](DATABASE.md) |
| **Past transaction didn't recalculate** | Verify `recalculate_from_date()` called → Check `AssetSnapshot` table | [TRANSACTION_PATTERNS.md](TRANSACTION_PATTERNS.md) |
| **API 500 error** | Check FastAPI console → Verify DB connection → Check foreign keys | [API_SPEC.md](API_SPEC.md) |
| **Frontend stale data** | Check React Query cache → Verify `queryKey` → Call `invalidateQueries` | [FRONTEND_COMPONENTS.md](FRONTEND_COMPONENTS.md) |

**Troubleshooting guide:** [SETUP.md](SETUP.md#troubleshooting)

---

## File Naming Conventions

### Backend
- Models: `app/models/account.py` (singular)
- Schemas: `app/schemas/account_schema.py` (singular)
- Services: `app/services/transaction_service.py` (singular)
- Routers: `app/routers/accounts.py` (plural)

### Frontend
- Pages: `app/accounts/page.tsx` (plural)
- Components: `components/AccountCard.tsx` (PascalCase)
- Hooks: `lib/hooks/useAccounts.ts` (camelCase, starts with 'use')
- Types: `lib/types.ts` (centralized)

---

## Testing Strategy

**Focus areas:**
- **Unit Tests:** Calculation logic (avg price, P/L, asset valuation)
- **Integration Tests:** Transaction flows (deposit, transfer, buy/sell, exchange)
- **E2E Tests:** Complete user workflows (create account → add transaction → view dashboard)

**Test examples:** [TRANSACTION_PATTERNS.md](TRANSACTION_PATTERNS.md#testing-transaction-patterns)

---

## When to Ask for Clarification

Before implementing, ask the user if:

1. **Business logic is ambiguous:** "Should dividends increase cash balance or be auto-reinvested?"
2. **Multiple valid approaches:** "Should we use optimistic updates or wait for server confirmation?"
3. **Data migration needed:** "Changing the schema will require migrating existing data. Proceed?"
4. **External dependencies:** "This requires a paid API. Should we use a free alternative?"
5. **Unclear requirements:** "What should happen if market data is unavailable for a past date?"

---

## Security Considerations

Even though this is a local app:

- **No hardcoded secrets:** Use `.env` for API keys
- **Input validation:** Sanitize all user inputs (SQL injection prevention via ORM)
- **Amount privacy:** Implement UI toggle to hide values
- **Backup reminders:** Prompt user to backup `.db` file periodically

---

## Git Commit Guidelines

Use conventional commits format:

```
feat: add exchange transaction type
fix: correct average price calculation for sells
docs: update API endpoint documentation
test: add unit tests for transfer logic
refactor: extract market data fetching to service
```

---

## Final Reminders

**When in doubt:**
1. **Data integrity > Feature completeness** → A correct calculation that's slow is better than a fast one that's wrong
2. **Read the docs first** → The information you need is likely already documented
3. **Follow the patterns** → All transactions must follow one of the 4 patterns
4. **Test with real data** → Create sample transactions to verify calculations
5. **Think like an accountant** → Every transaction should balance

**Never skip:**
- Reading [RULES.md](RULES.md) before modifying transaction logic
- Triggering recalculation when inserting past transactions
- Using `Decimal` for monetary calculations
- Validating linked transaction references are bidirectional
- Checking that `Holding` is always derivable from `Transaction` history

**Remember:** `Transaction` is the source of truth. `Holding` is always a computed view.

---

## Quick Access Links

- **Philosophy:** [CONTEXT.md](CONTEXT.md)
- **Rules:** [RULES.md](RULES.md)
- **Tasks:** [TODO.md](TODO.md)
- **API:** [API_SPEC.md](API_SPEC.md)
- **Database:** [DATABASE.md](DATABASE.md)
- **Transactions:** [TRANSACTION_PATTERNS.md](TRANSACTION_PATTERNS.md)
- **Frontend:** [FRONTEND_COMPONENTS.md](FRONTEND_COMPONENTS.md)
- **Setup:** [SETUP.md](SETUP.md)
