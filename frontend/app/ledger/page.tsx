'use client';

import { useState, useMemo } from 'react';
import { useAccounts } from '@/lib/hooks/useAccounts';
import { useTransactions } from '@/lib/hooks/useTransactions';
import { LedgerTable } from '@/components/LedgerTable';
import { MonthNavigation } from '@/components/MonthNavigation';
import { MonthlyCashFlowSummary } from '@/components/MonthlyCashFlowSummary';
import {
  transactionsToLedgerRows,
} from '@/lib/utils/ledger';
import { filterLedgerMoneyFlowTransactions } from '@/lib/utils/ledgerFilters';
import {
  getMonthsFromTransactions,
  filterTransactionsByMonth,
  calculateMonthlyCashFlow
} from '@/lib/utils/month';
import { Spinner } from '@/components/ui/Spinner';
import { LedgerRow } from '@/lib/types';

/**
 * Consolidated Ledger Page
 *
 * Shows external money in/out transactions from all accounts.
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

  const [selectedMonth, setSelectedMonth] = useState<string | null>(null);
  const viewMode = filters.start_date || filters.end_date
    ? 'date-range'
    : 'monthly';

  // Fetch all accounts
  const { data: accountsData, isLoading: accountsLoading } = useAccounts();

  const accounts = useMemo(() => {
    if (!accountsData?.accounts) return [];
    return accountsData.accounts;
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
      : accounts.map(acc => acc.id);
  }, [filters.selectedAccountIds, accounts]);

  // Filter transactions to external money in/out across selected accounts.
  const filteredTransactions = useMemo(() => {
    if (!transactionsData?.transactions) return [];

    return filterLedgerMoneyFlowTransactions(
      transactionsData.transactions,
      accounts,
      filters.selectedAccountIds
    );
  }, [transactionsData, accounts, filters.selectedAccountIds]);

  // Extract available months from transactions
  const availableMonths = useMemo(() => {
    return getMonthsFromTransactions(filteredTransactions);
  }, [filteredTransactions]);

  const currentMonth = useMemo(() => {
    if (viewMode !== 'monthly') return null;
    if (
      selectedMonth &&
      availableMonths.some(month => month.value === selectedMonth)
    ) {
      return selectedMonth;
    }
    return availableMonths[0]?.value || null;
  }, [availableMonths, selectedMonth, viewMode]);

  // Filter transactions by month or show all (depending on view mode)
  const displayedTransactions = useMemo(() => {
    if (viewMode === 'date-range') return filteredTransactions;
    if (!currentMonth) return [];
    return filterTransactionsByMonth(filteredTransactions, currentMonth);
  }, [viewMode, currentMonth, filteredTransactions]);

  // Transform to ledger rows with running balance
  const ledgerRows: LedgerRow[] = useMemo(() => {
    return transactionsToLedgerRows(displayedTransactions, '0.00');
  }, [displayedTransactions]);

  // Calculate monthly summary
  const monthlySummary = useMemo(() => {
    return calculateMonthlyCashFlow(ledgerRows);
  }, [ledgerRows]);

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
      selectedAccountIds: accounts.map(acc => acc.id)
    }));
  };

  const handleClearSelection = () => {
    setFilters(prev => ({
      ...prev,
      selectedAccountIds: []
    }));
  };

  const handleClearDateRange = () => {
    setFilters(prev => ({
      ...prev,
      start_date: '',
      end_date: ''
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
    <div className="space-y-8">
      <div className="rounded-xl border border-[var(--hairline-strong)] bg-[var(--surface-card)] p-6">
        <p className="resend-caption mb-3 uppercase tracking-[0]">
          Money flow
        </p>
        <h1 className="resend-display mb-3 text-5xl tracking-[0] sm:text-6xl">
          Consolidated Ledger
        </h1>
        <p className="max-w-3xl text-[var(--charcoal)]">
          View money entering and leaving your current assets across all
          accounts. Internal transfers, exchanges, buys, and sells are hidden.
        </p>
      </div>

      <div className="rounded-xl border border-[var(--hairline-strong)] bg-[var(--surface-card)] p-6">
        <h2 className="mb-4 text-lg font-medium tracking-[0] text-[var(--ink)]">
          Filters
        </h2>

        <div className="space-y-4">
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="block text-sm font-medium tracking-[0] text-[var(--body)]">
                Accounts
              </label>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={handleSelectAll}
                  className="text-sm font-medium text-[var(--link)] hover:text-[var(--ink)]"
                >
                  Select All
                </button>
                <button
                  type="button"
                  onClick={handleClearSelection}
                  className="text-sm font-medium text-[var(--link)] hover:text-[var(--ink)]"
                >
                  Clear
                </button>
              </div>
            </div>

            {accounts.length === 0 ? (
              <p className="text-sm italic text-[var(--mute)]">
                No accounts found. Create an account to use the ledger.
              </p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {accounts.map(acc => (
                  <label
                    key={acc.id}
                    className="flex cursor-pointer items-center gap-2 rounded-lg border border-[var(--hairline-strong)] bg-[var(--surface-elevated)] p-3 transition hover:bg-[var(--surface-card)]"
                  >
                    <input
                      type="checkbox"
                      checked={
                        filters.selectedAccountIds.length === 0 ||
                        filters.selectedAccountIds.includes(acc.id)
                      }
                      onChange={() => handleAccountToggle(acc.id)}
                      className="rounded border-[var(--hairline-strong)] bg-[var(--surface-card)] text-[var(--primary)] focus:ring-[var(--ink)]"
                    />
                    <div className="flex-1">
                      <div className="text-sm font-medium text-[var(--ink)]">
                        {acc.name}
                      </div>
                      <div className="text-xs text-[var(--mute)]">
                        {acc.type}
                      </div>
                    </div>
                  </label>
                ))}
              </div>
            )}

            {filters.selectedAccountIds.length === 0 && accounts.length > 0 && (
              <p className="mt-2 text-xs text-[var(--mute)]">
                No selection means all accounts are included
              </p>
            )}
          </div>

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

          {(filters.start_date || filters.end_date || filters.selectedAccountIds.length > 0) && (
            <div>
              <button
                type="button"
                onClick={() => setFilters({ start_date: '', end_date: '', selectedAccountIds: [] })}
                className="text-sm font-medium text-[var(--link)] hover:text-[var(--ink)]"
              >
                Clear all filters
              </button>
            </div>
          )}
        </div>
      </div>

      {viewMode === 'monthly' && availableMonths.length > 0 && (
        <MonthNavigation
          availableMonths={availableMonths}
          currentMonth={currentMonth || ''}
          onMonthChange={setSelectedMonth}
          disabled={false}
        />
      )}

      {viewMode === 'date-range' && (
        <div className="rounded-xl border border-[rgba(59,158,255,0.34)] bg-[rgba(59,158,255,0.1)] p-4">
          <p className="text-sm text-[var(--link)]">
            Custom date range active - monthly view disabled.
            <button
              type="button"
              onClick={handleClearDateRange}
              className="ml-2 font-medium text-[var(--ink)] hover:text-[var(--primary)]"
            >
              Return to monthly view
            </button>
          </p>
        </div>
      )}

      {viewMode === 'monthly' && availableMonths.length > 0 && currentMonth && ledgerRows.length > 0 && (
        <MonthlyCashFlowSummary
          monthLabel={availableMonths.find(m => m.value === currentMonth)?.label || ''}
          {...monthlySummary}
          currency="KRW"
          accountCount={selectedAccountIds.length}
        />
      )}

      {accounts.length > 0 ? (
        <>
          <LedgerTable
            rows={ledgerRows}
            currency="KRW"
            showAccount={true}
            isLoading={isLoading}
          />

          {filteredTransactions.length >= 10000 && (
            <div className="rounded-xl border border-[rgba(255,197,61,0.38)] bg-[rgba(255,197,61,0.1)] p-4">
              <p className="text-sm text-[var(--accent-yellow)]">
                <strong>Note:</strong> Showing up to 10,000 transactions.
                Use date filters to narrow down the results.
              </p>
            </div>
          )}

          {ledgerRows.length === 0 && !isLoading && (
            <div className="rounded-xl border border-[rgba(59,158,255,0.34)] bg-[rgba(59,158,255,0.1)] p-4">
              <p className="text-sm text-[var(--link)]">
                {viewMode === 'monthly'
                  ? 'No money in/out transactions found in the selected month. Internal transfers, exchanges, buys, and sells are hidden from this view.'
                  : 'No money in/out transactions found for the selected filters. Internal transfers, exchanges, buys, and sells are hidden from this view.'}
              </p>
            </div>
          )}
        </>
      ) : (
        <div className="rounded-xl border border-[var(--hairline-strong)] bg-[var(--surface-card)] p-8 text-center">
          <p className="mb-2 text-[var(--charcoal)]">
            No accounts available
          </p>
          <p className="text-sm text-[var(--mute)]">
            Create an account to start using the consolidated ledger.
          </p>
        </div>
      )}
    </div>
  );
}
