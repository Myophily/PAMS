'use client';

import { useState } from 'react';
import { useTransactions } from '@/lib/hooks/useTransactions';
import { LedgerTable } from '@/components/LedgerTable';
import { transactionsToLedgerRows } from '@/lib/utils/ledger';

interface AccountLedgerProps {
  accountId: number;
  currency?: string;
  initialBalance?: string;
}

/**
 * Account ledger tab component.
 *
 * Displays traditional accounting ledger view for an individual account:
 * - Date range filters
 * - Transactions in chronological order (oldest first)
 * - Debit/Credit columns
 * - Running balance calculation
 *
 * @example
 * <AccountLedger accountId={123} currency="KRW" />
 */
export function AccountLedger({
  accountId,
  currency = 'KRW',
  initialBalance = '0.00'
}: AccountLedgerProps) {
  const [filters, setFilters] = useState({
    start_date: '',
    end_date: '',
  });

  // Fetch transactions for this account
  const { data, isLoading } = useTransactions({
    account_id: accountId,
    start_date: filters.start_date || undefined,
    end_date: filters.end_date || undefined,
    limit: 1000,  // Fetch all for ledger view (up to 1000)
  });

  const transactions = data?.transactions || [];

  // Transform transactions to ledger rows with running balance
  const ledgerRows = transactionsToLedgerRows(transactions, initialBalance);

  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-[var(--hairline-strong)] bg-[var(--surface-card)] p-4">
        <h3 className="mb-3 text-sm font-medium tracking-[0] text-[var(--body)]">
          Filters
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="mb-1 block text-sm font-medium tracking-[0] text-[var(--body)]">
              Start Date
            </label>
            <input
              type="date"
              value={filters.start_date}
              onChange={(e) =>
                setFilters({ ...filters, start_date: e.target.value })
              }
              className="h-10 w-full rounded-lg border border-[var(--hairline-strong)] bg-[var(--surface-card)] px-3 py-2 text-sm text-[var(--ink)] focus:border-[var(--ink)] focus:outline-none"
            />
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium tracking-[0] text-[var(--body)]">
              End Date
            </label>
            <input
              type="date"
              value={filters.end_date}
              onChange={(e) =>
                setFilters({ ...filters, end_date: e.target.value })
              }
              className="h-10 w-full rounded-lg border border-[var(--hairline-strong)] bg-[var(--surface-card)] px-3 py-2 text-sm text-[var(--ink)] focus:border-[var(--ink)] focus:outline-none"
            />
          </div>
        </div>

        {(filters.start_date || filters.end_date) && (
          <div className="mt-3">
            <button
              type="button"
              onClick={() => setFilters({ start_date: '', end_date: '' })}
              className="text-sm font-medium text-[var(--link)] hover:text-[var(--ink)]"
            >
              Clear filters
            </button>
          </div>
        )}
      </div>

      <LedgerTable
        rows={ledgerRows}
        currency={currency}
        showAccount={false}
        isLoading={isLoading}
      />

      {transactions.length >= 1000 && (
        <div className="rounded-xl border border-[rgba(255,197,61,0.38)] bg-[rgba(255,197,61,0.1)] p-4">
          <p className="text-sm text-[var(--accent-yellow)]">
            <strong>Note:</strong> Showing the most recent 1,000 transactions.
            Use date filters to narrow down the results.
          </p>
        </div>
      )}
    </div>
  );
}
