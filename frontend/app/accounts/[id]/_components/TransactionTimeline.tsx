'use client';

import { useState } from 'react';
import { useTransactions } from '@/lib/hooks/useTransactions';
import { Spinner } from '@/components/ui/Spinner';
import { Badge } from '@/components/ui/Badge';
import { formatDateTime } from '@/lib/utils/datetime';
import { formatDecimal } from '@/lib/utils/decimal';

interface TransactionTimelineProps {
  accountId: number;
}

const getCurrencySymbol = (currency?: string): string => {
  if (!currency) return '$';
  switch (currency) {
    case 'KRW': return '₩';
    case 'JPY': return '¥';
    case 'EUR': return '€';
    case 'GBP': return '£';
    case 'HKD': return 'HK$';
    default: return '$';
  }
};

export function TransactionTimeline({ accountId }: TransactionTimelineProps) {
  const [filters, setFilters] = useState({
    type: '',
    start_date: '',
    end_date: '',
  });

  const { data, isLoading } = useTransactions({
    account_id: accountId,
    ...filters,
    limit: 50,
  });

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Spinner size="md" />
      </div>
    );
  }

  const transactions = data?.transactions || [];

  const getBadgeVariant = (type: string): 'success' | 'danger' | 'default' => {
    if (type === 'Buy' || type === 'Deposit' || type === 'Transfer_In') {
      return 'success';
    }
    if (type === 'Sell' || type === 'Withdrawal' || type === 'Transfer_Out') {
      return 'danger';
    }
    return 'default';
  };

  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-[var(--hairline-strong)] bg-[var(--surface-card)] p-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="mb-1 block text-sm font-medium tracking-[0] text-[var(--body)]">
              Type
            </label>
            <select
              value={filters.type}
              onChange={(e) => setFilters({ ...filters, type: e.target.value })}
              className="h-10 w-full rounded-lg border border-[var(--hairline-strong)] bg-[var(--surface-card)] px-3 py-2 text-sm text-[var(--ink)] focus:border-[var(--ink)] focus:outline-none"
            >
              <option value="">All Types</option>
              <option value="Buy">Buy</option>
              <option value="Sell">Sell</option>
              <option value="Deposit">Deposit</option>
              <option value="Withdrawal">Withdrawal</option>
              <option value="Transfer_In">Transfer In</option>
              <option value="Transfer_Out">Transfer Out</option>
              <option value="Dividend">Dividend</option>
              <option value="Exchange">Exchange</option>
            </select>
          </div>

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
      </div>

      {transactions.length === 0 ? (
        <div className="rounded-xl border border-[var(--hairline-strong)] bg-[var(--surface-card)] p-6 text-center text-[var(--mute)]">
          No transactions found
        </div>
      ) : (
        <div className="space-y-3">
          {transactions.map((tx) => (
            <div
              key={tx.id}
              className="rounded-xl border border-[var(--hairline-strong)] bg-[var(--surface-card)] p-4 transition hover:border-[rgba(252,253,255,0.28)]"
            >
              <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <Badge variant={getBadgeVariant(tx.type)}>{tx.type}</Badge>
                    <span className="text-sm text-[var(--charcoal)]">
                      {formatDateTime(tx.date)}
                    </span>
                    {(() => {
                      const txDate = new Date(tx.date);
                      const now = new Date();
                      const daysDiff = (now.getTime() - txDate.getTime()) / (1000 * 60 * 60 * 24);
                      return daysDiff > 7 && (
                        <Badge variant="warning" className="text-xs">
                          Past transaction
                        </Badge>
                      );
                    })()}
                  </div>

                  <div className="font-mono text-lg font-semibold text-[var(--ink)]">
                    {tx.ticker && `${tx.ticker} `}
                    {tx.quantity && tx.price && (
                      <>
                        {formatDecimal(tx.quantity)} shares @ {getCurrencySymbol(tx.price_currency)}
                        {formatDecimal(tx.price)}
                      </>
                    )}
                    {tx.amount && `${parseFloat(tx.amount).toLocaleString()}`}
                  </div>

                  {tx.description && (
                    <div className="mt-1 text-sm text-[var(--charcoal)]">
                      {tx.description}
                    </div>
                  )}
                </div>

                <div className="flex gap-2">
                  <button
                    type="button"
                    className="text-sm font-medium text-[var(--link)] hover:text-[var(--ink)]"
                  >
                    Edit
                  </button>
                  <button
                    type="button"
                    className="text-sm font-medium text-[var(--accent-red)] hover:text-[var(--ink)]"
                  >
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
