-- Migration: Make currency column nullable
-- Date: 2026-01-08
-- Description: Prepare for currency removal by making the column optional

-- Make currency nullable (SQLite doesn't support ALTER COLUMN, so we need to recreate)
-- This is a safe migration that doesn't lose data

PRAGMA foreign_keys=off;

BEGIN TRANSACTION;

-- Create new table with nullable currency
CREATE TABLE account_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,
    type VARCHAR(20) NOT NULL,
    currency VARCHAR(3),  -- Changed from NOT NULL to nullable
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_account_type CHECK (type IN ('Deposit', 'Securities', 'ForeignCurrency', 'MoneyMarket', 'Savings'))
);

-- Copy data from old table
INSERT INTO account_new (id, name, type, currency, created_at)
SELECT id, name, type, currency, created_at FROM account;

-- Drop old table
DROP TABLE account;

-- Rename new table
ALTER TABLE account_new RENAME TO account;

-- Recreate indexes
CREATE INDEX idx_account_type ON account(type);
CREATE INDEX idx_account_currency ON account(currency);

COMMIT;

PRAGMA foreign_keys=on;
