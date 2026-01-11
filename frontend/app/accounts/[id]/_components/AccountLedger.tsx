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
      {/* Filter Section */}
      <div className="bg-gray-50 rounded-lg border border-gray-200 p-4">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Filters</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Start Date
            </label>
            <input
              type="date"
              value={filters.start_date}
              onChange={(e) =>
                setFilters({ ...filters, start_date: e.target.value })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              End Date
            </label>
            <input
              type="date"
              value={filters.end_date}
              onChange={(e) =>
                setFilters({ ...filters, end_date: e.target.value })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>

        {(filters.start_date || filters.end_date) && (
          <div className="mt-3">
            <button
              onClick={() => setFilters({ start_date: '', end_date: '' })}
              className="text-sm text-blue-600 hover:text-blue-800 underline"
            >
              Clear filters
            </button>
          </div>
        )}
      </div>

      {/* Ledger Table */}
      <LedgerTable
        rows={ledgerRows}
        currency={currency}
        showAccount={false}
        isLoading={isLoading}
      />

      {/* Info note */}
      {transactions.length >= 1000 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <p className="text-sm text-yellow-800">
            <strong>Note:</strong> Showing the most recent 1,000 transactions.
            Use date filters to narrow down the results.
          </p>
        </div>
      )}
    </div>
  );
}
