# PAM - Agent Guidelines

This document provides essential information for agentic coding assistants working in the PAM (Personal Asset Manager) repository.

## Build & Test Commands

### Backend (Python/FastAPI)
```bash
# Development server
cd backend && uvicorn app.main:app --reload

# Run all tests
cd backend && pytest

# Run single test file
cd backend && pytest tests/services/test_transaction_patterns.py

# Run single test function
cd backend && pytest tests/services/test_transaction_patterns.py::TestPattern1IncomeExpense::test_deposit_increases_cash_balance

# Run with coverage
cd backend && pytest --cov=app --cov-report=term-missing

# Install dependencies
cd backend && pip install -r requirements.txt
```

### Frontend (Next.js)
```bash
# Development server
cd frontend && npm run dev

# Build production
cd frontend && npm run build

# Lint
cd frontend && npm run lint

# Install dependencies
cd frontend && npm install
```

## Backend Code Style (Python)

### Imports & Formatting
- Import order: stdlib, third-party, local app modules (each separated by blank line)
- Use `from decimal import Decimal` for monetary values (NEVER use `float`)
- Use `from datetime import datetime, date` for dates (NEVER use string dates)
- Type hints required on all function signatures
- Max line length: 88 characters (black default)

### Type Safety
```python
from decimal import Decimal
from datetime import datetime, date
from typing import Optional, List, Tuple

def create_deposit(
    account_id: int,
    amount: Decimal,        # ALWAYS Decimal for money
    transaction_date: date, # ALWAYS date, not datetime
    description: Optional[str],
    db: Session
) -> Transaction:
    pass
```

### Naming Conventions
- Classes: PascalCase (`TransactionService`)
- Functions/Variables: snake_case (`create_deposit`)
- Constants: UPPER_SNAKE_CASE (`ALLOWED_TRANSACTIONS`)
- Private methods: `_leading_underscore`

### Error Handling in Routers
```python
@router.post("/", response_model=AccountResponse)
def create_account(request: AccountCreateRequest, db: Session = Depends(get_db)):
    try:
        account = account_service.create_account(...)
        return account
    except ValueError as e:
        # Business logic validation errors
        raise HTTPException(status_code=400, detail=str(e))
    except IntegrityError as e:
        # Database constraint violations
        db.rollback()
        raise HTTPException(status_code=409, detail="Database constraint violation")
    except SQLAlchemyError as e:
        # Database errors
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
```

### Service Layer Pattern
- All business logic in services, not routers
- Services use `Decimal` for all monetary calculations
- Use `db.flush()` before accessing generated IDs
- Use `db.commit()` at end of operations (can be skipped with `auto_commit=False`)

### Database Operations
```python
# Correct pattern for past transactions
if is_past_transaction(transaction_date):
    recalculate_from_date(transaction_date, db)
```

## Frontend Code Style (TypeScript/React)

### Imports & Formatting
- Import order: React/hooks, third-party lib imports, local imports (each separated by blank line)
- Use `import type` for type-only imports
- Max line length: 80 characters (Prettier default)

### Type Safety
```typescript
import type { Account, Transaction, DecimalString } from '@/lib/types';

// Decimal from backend is always string
const balance: DecimalString = "1234.56";

// Use parseDecimal() for calculations
const total = parseDecimal(balance) + parseDecimal(amount);

// Use formatDecimal() for display
const display = formatDecimal(balance, locale);
```

### React Query Hooks
```typescript
export function useAccounts() {
  return useQuery<{ accounts: AccountWithBalance[] }>({
    queryKey: ['accounts'],
    queryFn: async () => {
      const res = await fetch('/api/accounts');
      if (!res.ok) throw new Error('Failed to fetch accounts');
      return res.json();
    },
  });
}
```

### Component Patterns
- Use `"use client"` directive for client components
- Wrap data fetching in Suspense boundaries
- Handle loading/error states explicitly
- Use Tailwind CSS classes (no inline styles)

### Error Handling
```typescript
try {
  const res = await fetch('/api/accounts', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Failed to create account');
  }
  return res.json();
} catch (error) {
  // Handle error
}
```

## Testing Patterns

### Pytest Structure
- Test files: `test_*.py` in `tests/` directory
- Test classes: `Test*` with descriptive names
- Test functions: `test_*` with descriptive names
- Fixtures defined in `tests/conftest.py`

### Test Organization
```python
class TestPattern1IncomeExpense:
    """Test Pattern ① - Single account, total assets CHANGE."""

    def test_deposit_increases_cash_balance(self, db_session, checking_account):
        """Deposit should increase CASH holding."""
        # Arrange, Act, Assert pattern
```

### Common Fixtures
- `db_session`: Database session (auto-rollback)
- `test_client`: FastAPI TestClient
- `checking_account`, `brokerage_account`, `foreign_account`: Sample accounts
- `create_deposit`: Factory function for creating deposits

## Critical Business Rules

### Four Transaction Patterns (NEVER VIOLATE)
1. **Pattern ① (Income/Expense):** 1 transaction → 1 holding → total assets CHANGE
2. **Pattern ② (Transfer):** 2 linked transactions → 2 holdings → total assets UNCHANGED
3. **Pattern ③ (Buy/Sell):** 1 transaction → 2 holdings → total assets UNCHANGED at tx time
4. **Pattern ④ (Exchange):** 2 linked transactions (same account) → 2 holdings → total assets UNCHANGED

### Immutable Transaction History
- Use soft delete (`deleted_at`) - never hard delete
- `Holding` table is computed from `Transaction` history
- Linked transactions must reference each other bidirectionally

### Monetary Values
- **Backend:** ALWAYS use `Decimal` type, never `float`
- **Frontend:** Backend sends decimals as strings (`DecimalString`), use helpers for display

### Account Type Transaction Enforcement
- **Deposit accounts:** Only cash operations (Deposit, Withdrawal, Transfer_In/Out)
- **Securities accounts:** All transaction types including Buy, Sell, Dividend
- **ForeignCurrency accounts:** Cash operations + Exchange
- **MoneyMarket accounts:** Cash operations + Interest

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

## Before Making Changes

1. **Read project docs:** CONTEXT.md, RULES.md, TODO.md, API_SPEC.md
2. **Identify transaction pattern:** Which of the 4 patterns applies?
3. **Validate account types:** Check if transaction type is allowed for account type
4. **Use Decimal everywhere:** Never use float for monetary values
5. **Handle past transactions:** Trigger recalculation if date < today
6. **Test thoroughly:** Run pytest for backend, check console for frontend
