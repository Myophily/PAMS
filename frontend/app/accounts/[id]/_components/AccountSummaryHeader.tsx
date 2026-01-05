'use client';

import { formatCurrency, formatPercent } from '@/lib/utils/format';

interface AccountSummaryHeaderProps {
  name: string;
  type: string;
  currency: string;
  totalValue: number;
  cashBalance: number;
  unrealizedPL: number;
  unrealizedPLPercent: number;
}

export function AccountSummaryHeader({
  name,
  type,
  currency,
  totalValue,
  cashBalance,
  unrealizedPL,
  unrealizedPLPercent,
}: AccountSummaryHeaderProps) {
  const isPositive = unrealizedPL >= 0;

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="mb-4">
        <h1 className="text-3xl font-bold">{name}</h1>
        <span className="text-sm text-gray-500">
          {type} • {currency}
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div>
          <div className="text-sm text-gray-600 mb-1">Total Value</div>
          <div className="text-2xl font-bold text-gray-900">
            {totalValue.toLocaleString()} {currency}
          </div>
        </div>

        <div>
          <div className="text-sm text-gray-600 mb-1">Cash Balance</div>
          <div className="text-2xl font-bold text-gray-900">
            {cashBalance.toLocaleString()} {currency}
          </div>
        </div>

        <div>
          <div className="text-sm text-gray-600 mb-1">Unrealized P/L</div>
          <div
            className={`text-2xl font-bold ${
              isPositive ? 'text-green-600' : 'text-red-600'
            }`}
          >
            {isPositive ? '+' : ''}
            {unrealizedPL.toLocaleString()} {currency}
          </div>
          <div
            className={`text-sm ${
              isPositive ? 'text-green-600' : 'text-red-600'
            }`}
          >
            {formatPercent(unrealizedPLPercent)}
          </div>
        </div>
      </div>
    </div>
  );
}
