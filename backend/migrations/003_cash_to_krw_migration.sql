-- Migration: Convert CASH ticker to KRW
-- Date: 2026-01-08
-- Description: Replace all "CASH" ticker occurrences with "KRW" or "USD" based on account type
-- Status: READY TO APPLY

-- This migration converts legacy CASH ticker to explicit currency codes:
-- - Deposit/Savings/MoneyMarket accounts: CASH → KRW
-- - Securities/ForeignCurrency accounts: CASH → USD (unless account has other holdings)

PRAGMA foreign_keys=off;

BEGIN TRANSACTION;

-- Step 1: Update Holdings table
-- For Deposit/Savings/MoneyMarket: CASH → KRW
UPDATE holding
SET ticker = 'KRW'
WHERE ticker = 'CASH'
  AND account_id IN (
    SELECT id FROM account
    WHERE type IN ('Deposit', 'Savings', 'MoneyMarket')
  );

-- For Securities/ForeignCurrency: CASH → USD
UPDATE holding
SET ticker = 'USD'
WHERE ticker = 'CASH'
  AND account_id IN (
    SELECT id FROM account
    WHERE type IN ('Securities', 'ForeignCurrency')
  );

-- Step 2: Update Transaction table (same logic)
-- For Deposit/Savings/MoneyMarket accounts
UPDATE `transaction`
SET ticker = 'KRW'
WHERE ticker = 'CASH'
  AND account_id IN (
    SELECT id FROM account
    WHERE type IN ('Deposit', 'Savings', 'MoneyMarket')
  );

-- For Securities/ForeignCurrency accounts
UPDATE `transaction`
SET ticker = 'USD'
WHERE ticker = 'CASH'
  AND account_id IN (
    SELECT id FROM account
    WHERE type IN ('Securities', 'ForeignCurrency')
  );

-- Step 3: Verify no CASH tickers remain
-- This query should return 0 rows
SELECT 'HOLDINGS_CHECK' as check_type, COUNT(*) as cash_count
FROM holding
WHERE ticker = 'CASH'
UNION ALL
SELECT 'TRANSACTIONS_CHECK', COUNT(*)
FROM `transaction`
WHERE ticker = 'CASH';

COMMIT;

PRAGMA foreign_keys=on;

-- VERIFICATION QUERIES (run after migration):
-- 1. Count by ticker:
--    SELECT ticker, COUNT(*) FROM holding GROUP BY ticker;
-- 2. Count by account type and ticker:
--    SELECT a.type, h.ticker, COUNT(*)
--    FROM holding h JOIN account a ON h.account_id = a.id
--    GROUP BY a.type, h.ticker;

-- ROLLBACK SCRIPT (if needed):
-- UPDATE holding SET ticker = 'CASH' WHERE ticker = 'KRW' AND account_id IN (SELECT id FROM account WHERE type IN ('Deposit', 'Savings', 'MoneyMarket'));
-- UPDATE holding SET ticker = 'CASH' WHERE ticker = 'USD' AND account_id IN (SELECT id FROM account WHERE type IN ('Securities', 'ForeignCurrency'));
-- UPDATE `transaction` SET ticker = 'CASH' WHERE ticker = 'KRW' AND account_id IN (SELECT id FROM account WHERE type IN ('Deposit', 'Savings', 'MoneyMarket'));
-- UPDATE `transaction` SET ticker = 'CASH' WHERE ticker = 'USD' AND account_id IN (SELECT id FROM account WHERE type IN ('Securities', 'ForeignCurrency'));
