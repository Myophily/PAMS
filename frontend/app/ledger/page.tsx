'use client';

import { useState, useMemo } from 'react';
import { useAccounts } from '@/lib/hooks/useAccounts';
import { useTransactions } from '@/lib/hooks/useTransactions';
import { LedgerTable } from '@/components/LedgerTable';
import { transactionsToLedgerRows } from '@/lib/utils/ledger';
import { Spinner } from '@/components/ui/Spinner';
import { LedgerRow } from '@/lib/types';

/**
 * Consolidated Ledger Page
 *
 * Shows transactions from all deposit accounts in a unified ledger view.
 * Features:
 * - Filter by specific accounts (multi-select)
 * - Date range filtering
 * - Running balance across all selected accounts
 * - Traditional accounting format
 */
export default function ConsolidatedLedgerPage() {
  const [filters, setFilters] = useState({
    start_date: '',
    end_date: '',
    selectedAccountIds: [] as number[],
  });

  // Fetch all accounts
  const { data: accountsData, isLoading: accountsLoading } = useAccounts();

  // Filter for Deposit, MoneyMarket, and Savings accounts (cash-based accounts)
  const cashAccounts = useMemo(() => {
    if (!accountsData?.accounts) return [];
    return accountsData.accounts.filter(acc =>
      ['Deposit', 'MoneyMarket', 'Savings'].includes(acc.type)
    );
  }, [accountsData]);

  // Fetch ALL transactions (no account_id filter to avoid Rules of Hooks violation)
  // We'll filter client-side
  const { data: transactionsData, isLoading: transactionsLoading } = useTransactions({
    start_date: filters.start_date || undefined,
    end_date: filters.end_date || undefined,
    limit: 10000,  // Fetch more for consolidated view
  });

  const isLoading = accountsLoading || transactionsLoading;

  // Determine which accounts to show
  const selectedAccountIds = useMemo(() => {
    return filters.selectedAccountIds.length > 0
      ? filters.selectedAccountIds
      : cashAccounts.map(acc => acc.id);
  }, [filters.selectedAccountIds, cashAccounts]);

  // Filter transactions to only show selected cash accounts
  const filteredTransactions = useMemo(() => {
    if (!transactionsData?.transactions) return [];

    const cashAccountIds = new Set(cashAccounts.map(acc => acc.id));

    return transactionsData.transactions
      .filter(tx => {
        // Only include transactions from cash accounts
        if (!cashAccountIds.has(tx.account_id)) return false;

        // Only include selected accounts
        if (!selectedAccountIds.includes(tx.account_id)) return false;

        return true;
      })
      .map(tx => ({
        ...tx,
        // Ensure account_name is populated from the accounts list
        account_name: tx.account_name || cashAccounts.find(acc => acc.id === tx.account_id)?.name || 'Unknown'
      }))
      .sort((a, b) => {
        // Sort chronologically (oldest first)
        const dateDiff = new Date(a.date).getTime() - new Date(b.date).getTime();
        if (dateDiff !== 0) return dateDiff;
        return a.id - b.id;
      });
  }, [transactionsData, cashAccounts, selectedAccountIds]);

  // Transform to ledger rows with running balance
  const ledgerRows: LedgerRow[] = useMemo(() => {
    return transactionsToLedgerRows(filteredTransactions, '0.00');
  }, [filteredTransactions]);

  const handleAccountToggle = (accountId: number) => {
    setFilters(prev => {
      const currentSelection = prev.selectedAccountIds;
      const isSelected = currentSelection.includes(accountId);

      return {
        ...prev,
        selectedAccountIds: isSelected
          ? currentSelection.filter(id => id !== accountId)
          : [...currentSelection, accountId]
      };
    });
  };

  const handleSelectAll = () => {
    setFilters(prev => ({
      ...prev,
      selectedAccountIds: cashAccounts.map(acc => acc.id)
    }));
  };

  const handleClearSelection = () => {
    setFilters(prev => ({
      ...prev,
      selectedAccountIds: []
    }));
  };

  if (accountsLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="bg-white rounded-lg shadow p-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          Consolidated Ledger
        </h1>
        <p className="text-gray-600">
          View all transactions across your deposit accounts in traditional ledger format
        </p>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Filters</h2>

        <div className="space-y-4">
          {/* Account Selection */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="block text-sm font-medium text-gray-700">
                Accounts
              </label>
              <div className="flex gap-2">
                <button
                  onClick={handleSelectAll}
                  className="text-sm text-blue-600 hover:text-blue-800 underline"
                >
                  Select All
                </button>
                <button
                  onClick={handleClearSelection}
                  className="text-sm text-blue-600 hover:text-blue-800 underline"
                >
                  Clear
                </button>
              </div>
            </div>

            {cashAccounts.length === 0 ? (
              <p className="text-sm text-gray-500 italic">
                No cash-based accounts found. Create a Deposit, MoneyMarket, or Savings account to use the ledger.
              </p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {cashAccounts.map(acc => (
                  <label
                    key={acc.id}
                    className="flex items-center gap-2 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer"
                  >
                    <input
                      type="checkbox"
                      checked={
                        filters.selectedAccountIds.length === 0 ||
                        filters.selectedAccountIds.includes(acc.id)
                      }
                      onChange={() => handleAccountToggle(acc.id)}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <div className="flex-1">
                      <div className="text-sm font-medium text-gray-900">
                        {acc.name}
                      </div>
                      <div className="text-xs text-gray-500">
                        {acc.type}
                      </div>
                    </div>
                  </label>
                ))}
              </div>
            )}

            {filters.selectedAccountIds.length === 0 && cashAccounts.length > 0 && (
              <p className="text-xs text-gray-500 mt-2">
                No selection means all accounts are included
              </p>
            )}
          </div>

          {/* Date Range */}
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

          {/* Clear Filters */}
          {(filters.start_date || filters.end_date || filters.selectedAccountIds.length > 0) && (
            <div>
              <button
                onClick={() => setFilters({ start_date: '', end_date: '', selectedAccountIds: [] })}
                className="text-sm text-blue-600 hover:text-blue-800 underline"
              >
                Clear all filters
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Ledger Table */}
      {cashAccounts.length > 0 ? (
        <>
          <LedgerTable
            rows={ledgerRows}
            currency="KRW"
            showAccount={true}
            isLoading={isLoading}
          />

          {/* Info notes */}
          {filteredTransactions.length >= 10000 && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <p className="text-sm text-yellow-800">
                <strong>Note:</strong> Showing up to 10,000 transactions.
                Use date filters to narrow down the results.
              </p>
            </div>
          )}

          {ledgerRows.length === 0 && !isLoading && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-sm text-blue-800">
                No transactions found for the selected filters. Try adjusting your date range or account selection.
              </p>
            </div>
          )}
        </>
      ) : (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
          <p className="text-gray-600 mb-2">
            No cash-based accounts available
          </p>
          <p className="text-sm text-gray-500">
            Create a Deposit, MoneyMarket, or Savings account to start using the consolidated ledger.
          </p>
        </div>
      )}
    </div>
  );
}
