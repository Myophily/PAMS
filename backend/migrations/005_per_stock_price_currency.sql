-- Migration: Change price_currency from account-level to per-stock (transaction/holding level)
-- Date: 2026-01-08
-- Purpose: Allow different stocks to have different price currencies in the same account

-- Remove price_currency from account table
ALTER TABLE account DROP COLUMN price_currency;

-- Add price_currency to transaction table (for Buy/Sell transactions)
ALTER TABLE "transaction" ADD COLUMN price_currency VARCHAR(3);

-- Add price_currency to holding table
ALTER TABLE holding ADD COLUMN price_currency VARCHAR(3);

-- Set default USD for existing holdings (backward compatibility)
UPDATE holding SET price_currency = 'USD' WHERE ticker NOT IN ('KRW', 'USD', 'EUR', 'JPY', 'GBP', 'CNY', 'AUD', 'CAD', 'CHF', 'HKD', 'SGD');
