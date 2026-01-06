'use client';

import { useState } from 'react';
import { useTransactions } from '@/lib/hooks/useTransactions';
import { Spinner } from '@/components/ui/Spinner';
import { Badge } from '@/components/ui/Badge';
import { formatShortDate } from '@/lib/utils/format';

interface TransactionTimelineProps {
  accountId: number;
}

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
      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Type
            </label>
            <select
              value={filters.type}
              onChange={(e) => setFilters({ ...filters, type: e.target.value })}
              className="w-full border rounded px-3 py-2"
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
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Start Date
            </label>
            <input
              type="date"
              value={filters.start_date}
              onChange={(e) =>
                setFilters({ ...filters, start_date: e.target.value })
              }
              className="w-full border rounded px-3 py-2"
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
              className="w-full border rounded px-3 py-2"
            />
          </div>
        </div>
      </div>

      {/* Timeline */}
      {transactions.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-6 text-center text-gray-500">
          No transactions found
        </div>
      ) : (
        <div className="space-y-3">
          {transactions.map((tx) => (
            <div
              key={tx.id}
              className="bg-white rounded-lg shadow p-4 hover:shadow-md transition"
            >
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <Badge variant={getBadgeVariant(tx.type)}>{tx.type}</Badge>
                    <span className="text-sm text-gray-600">
                      {formatShortDate(tx.date)}
                    </span>
                    {/* Show badge for past transactions (older than a week) */}
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

                  <div className="text-lg font-semibold text-gray-900">
                    {tx.ticker && `${tx.ticker} `}
                    {tx.quantity && `${tx.quantity} shares @ ${tx.price}`}
                    {tx.amount && `${parseFloat(tx.amount).toLocaleString()}`}
                  </div>

                  {tx.description && (
                    <div className="text-sm text-gray-600 mt-1">
                      {tx.description}
                    </div>
                  )}
                </div>

                <div className="flex gap-2">
                  <button className="text-sm text-blue-600 hover:text-blue-800">
                    Edit
                  </button>
                  <button className="text-sm text-red-600 hover:text-red-800">
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
