-- Migration: Add price_currency field to account table
-- Date: 2026-01-08
-- Purpose: Allow Securities accounts to specify price currency (KRW or USD)

-- Add price_currency column to account table
ALTER TABLE account ADD COLUMN price_currency VARCHAR(3);

-- Set default to 'USD' for existing Securities accounts (backward compatibility)
UPDATE account SET price_currency = 'USD' WHERE type = 'Securities';
