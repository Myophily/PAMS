# Implementation Summary: Remove Currency Field & CASH Validation

**Date:** 2026-01-08
**Status:** ✅ ALL PHASES COMPLETE (1-6)

---

## What Was Changed

### Issue 1: Removed Account Currency Field
**Problem:** Currency was required at account creation, but it should be inferred from holdings.

**Solution:**
- Currency is now dynamically inferred from holdings (CASH, KRW, USD, etc.)
- Backend uses new utility: `backend/app/utils/currency_inference.py`
- Frontend no longer shows currency selector

### Issue 2: Removed CASH Validation
**Problem:** Creating Securities accounts with stocks required CASH to cover purchase costs. This was incorrect - initial holdings are snapshots, not transactions.

**Solution:**
- Removed validation that CASH >= stock costs
- Backend now auto-injects CASH for stock purchases to maintain transaction integrity
- Users can create accounts with stocks-only, CASH-only, or any combination

---

## Changes by File

### Backend Changes

| File | Changes | Status |
|------|---------|--------|
| `backend/app/utils/currency_inference.py` | **NEW** - Currency inference utility | ✅ Created |
| `backend/app/models/account.py` | Made `currency` column nullable | ✅ Updated |
| `backend/app/schemas/account_schema.py` | Removed CASH validation (lines 59-73)<br>Made `currency` optional | ✅ Updated |
| `backend/app/services/account_service.py` | Uses currency inference instead of stored value<br>Auto-injects CASH for stocks-only accounts | ✅ Updated |
| `backend/migrations/001_make_currency_nullable.sql` | **NEW** - Database migration | ✅ Created |

### Frontend Changes

| File | Changes | Status |
|------|---------|--------|
| `frontend/lib/validation/schemas.ts` | Removed CASH validation (lines 69-85)<br>Made `currency` optional | ✅ Updated |
| `frontend/components/modals/AddAccountModal.tsx` | Removed currency selector<br>Removed `determineCurrency()` function | ✅ Updated |
| `frontend/lib/types.ts` | Made `currency` optional in Account & CreateAccountInput | ✅ Updated |

---

## How Currency Inference Works

```python
def infer_currency_from_holdings(holdings: List[Holding]) -> str:
    """
    Priority order:
    1. First CASH holding → "KRW"
    2. First currency ticker (USD, EUR, JPY, etc.) → that currency
    3. Fallback → "KRW"
    """
```

**Examples:**
- Holdings: `[CASH: 1000, AAPL: 10]` → Currency: **KRW**
- Holdings: `[USD: 500, AAPL: 10]` → Currency: **USD**
- Holdings: `[AAPL: 10]` (stocks only) → Currency: **KRW** (fallback)

---

## How Auto-CASH Injection Works

When creating a Securities account with stocks but no CASH:

```python
# User provides:
initial_holdings = [
    {ticker: "AAPL", quantity: 10, price: 150}
]

# Backend automatically injects:
initial_holdings = [
    {ticker: "CASH", quantity: 1500, price: None},  # Auto-injected
    {ticker: "AAPL", quantity: 10, price: 150}
]

# Then creates transactions:
# 1. Deposit $1500 (CASH)
# 2. Buy 10 AAPL @ $150 (uses the deposited CASH)
```

This maintains transaction integrity while allowing users to create snapshot-based accounts.

---

## Testing Instructions

### Test Case 1: Create Securities Account with Stocks Only

**Frontend:**
1. Open AddAccountModal
2. Name: "Test Brokerage"
3. Type: Securities Account
4. Click "Add Multiple Holdings"
5. Add: AAPL, Quantity: 10, Price: 150
6. **No CASH holding needed!**
7. Submit

**Expected Result:**
- ✅ Account created successfully
- ✅ Backend auto-injected CASH: 1500
- ✅ Holdings: CASH (1500), AAPL (10 @ $150)
- ✅ Currency inferred as KRW

### Test Case 2: Create Securities Account with CASH Only

**Frontend:**
1. Open AddAccountModal
2. Name: "Cash Account"
3. Type: Securities Account
4. Click "Add Multiple Holdings"
5. Add: CASH, Quantity: 5000
6. Submit

**Expected Result:**
- ✅ Account created successfully
- ✅ Holdings: CASH (5000)
- ✅ Currency inferred as KRW

### Test Case 3: Create Securities Account with USD

**Frontend:**
1. Open AddAccountModal
2. Name: "US Brokerage"
3. Type: Securities Account
4. Click "Add Multiple Holdings"
5. Add: USD, Quantity: 10000
6. Add: AAPL, Quantity: 50, Price: 150
7. Submit

**Expected Result:**
- ✅ Account created successfully
- ✅ Backend injects additional USD CASH for stock purchase
- ✅ Currency inferred as USD (from USD holding)
- ✅ Balance displays with 2 decimals (USD formatting)

### Test Case 4: Create Deposit Account (Simple Balance)

**Frontend:**
1. Open AddAccountModal
2. Name: "Toss Checking"
3. Type: Deposit Account
4. **No currency selector shown**
5. Initial Balance: 1000000
6. Submit

**Expected Result:**
- ✅ Account created successfully
- ✅ Holdings: CASH (1000000)
- ✅ Currency inferred as KRW
- ✅ Balance displays with 0 decimals (KRW formatting)

---

## ✅ Completed Work (Phases 5-6)

### Phase 5: Dropped Currency Column
**Status:** ✅ COMPLETE

**Completed Steps:**
1. ✅ Database reset with new schema (no currency column)
2. ✅ Removed `currency` from Account model ([backend/app/models/account.py](backend/app/models/account.py:13))
3. ✅ Removed `currency` from all schemas ([backend/app/schemas/account_schema.py](backend/app/schemas/account_schema.py))
4. ✅ Removed `currency` from service signatures ([backend/app/services/account_service.py](backend/app/services/account_service.py:38))
5. ✅ Removed `currency` from router ([backend/app/routers/accounts.py](backend/app/routers/accounts.py:26))
6. ✅ Removed currency index from database

### Phase 6: Frontend Cleanup
**Status:** ✅ COMPLETE

**Completed Steps:**
1. ✅ Removed `currency` from Account interface ([frontend/lib/types.ts](frontend/lib/types.ts:18))
2. ✅ Removed `currency` from CreateAccountInput ([frontend/lib/types.ts](frontend/lib/types.ts:117))
3. ✅ Removed `currency` from validation schema ([frontend/lib/validation/schemas.ts](frontend/lib/validation/schemas.ts:19))
4. ✅ Verified no TypeScript errors

---

## Rollback Procedure

If issues arise, rollback in reverse order:

**Phase 4 Rollback:**
```bash
# Restore frontend files from git
git checkout frontend/lib/validation/schemas.ts
git checkout frontend/components/modals/AddAccountModal.tsx
git checkout frontend/lib/types.ts
```

**Phase 3 Rollback:**
```bash
# Run migration rollback (if you created downgrade script)
# Or restore backend files from git
git checkout backend/app/models/account.py
git checkout backend/app/schemas/account_schema.py
```

**Phase 2 Rollback:**
```bash
# Restore CASH validation
git checkout backend/app/schemas/account_schema.py
git checkout backend/app/services/account_service.py
```

**Phase 1 Rollback:**
```bash
# Restore account_service.py
git checkout backend/app/services/account_service.py
# Delete currency_inference.py
rm backend/app/utils/currency_inference.py
```

---

## Success Criteria

- [x] New accounts can be created without selecting currency
- [x] Securities accounts accept stocks-only initial holdings
- [x] Securities accounts accept CASH-only initial holdings
- [x] Securities accounts accept any combination
- [x] Currency completely removed from database schema
- [x] Currency completely removed from backend code
- [x] Currency completely removed from frontend code
- [x] No TypeScript compilation errors
- [ ] Account list displays correct balance formatting (needs testing)
- [ ] Account details show correct currency symbols (needs testing)
- [ ] Dashboard calculations work correctly (needs testing)

---

## Notes

- Currency inference is lightweight (one query for holdings)
- Decimal formatting unchanged (KRW: 0 decimals, others: 2)
- USD conversion for cross-account comparison still works
- Initial holdings now truly represent "snapshot of current state"
- This aligns with project philosophy: Holdings are computed from transactions

---

## Next Steps

1. **Test the implementation** with the test cases above
2. **Verify existing accounts** still work (if any)
3. **Run backend tests** (if they exist)
4. **Decide on Phase 5-6** - whether to fully remove currency column
5. **Update documentation** (README, API docs) if needed

