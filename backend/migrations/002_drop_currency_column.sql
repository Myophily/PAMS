-- Migration: Drop currency column completely
-- Date: 2026-01-08
-- Description: Remove currency field - now inferred from holdings
-- Status: ✅ APPLIED (Database reset with new schema)

-- This migration is for documentation only.
-- The database was reset with the new schema that excludes the currency column.

-- If you need to apply this to an existing database with data:
-- WARNING: This is destructive if applied to a database with existing data

PRAGMA foreign_keys=off;

BEGIN TRANSACTION;

-- Create new table without currency
CREATE TABLE account_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,
    type VARCHAR(20) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_account_type CHECK (type IN ('Deposit', 'Securities', 'ForeignCurrency', 'MoneyMarket', 'Savings'))
);

-- Copy data from old table (excluding currency)
INSERT INTO account_new (id, name, type, created_at)
SELECT id, name, type, created_at FROM account;

-- Drop old table
DROP TABLE account;

-- Rename new table
ALTER TABLE account_new RENAME TO account;

-- Recreate indexes (currency index removed)
CREATE INDEX idx_account_type ON account(type);

COMMIT;

PRAGMA foreign_keys=on;

-- NOTES:
-- - Currency is now dynamically inferred from holdings
-- - Inference logic: backend/app/utils/currency_inference.py
-- - CASH holding → KRW
-- - USD/EUR/JPY holding → respective currency
-- - No holdings → KRW (default)
