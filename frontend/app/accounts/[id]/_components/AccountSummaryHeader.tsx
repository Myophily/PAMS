'use client';

import { formatCurrency, formatPercent } from '@/lib/utils/format';
import { formatDecimal, isPositive } from '@/lib/utils/decimal';
import type { DecimalString } from '@/lib/types';
import { Badge } from '@/components/ui/Badge';
import { Spinner } from '@/components/ui/Spinner';

interface AccountSummaryHeaderProps {
  name: string;
  type: string;
  currency: string;
  totalValue: DecimalString;
  cashBalance: DecimalString;
  unrealizedPL: DecimalString;
  unrealizedPLPercent: DecimalString;
  isRefetching?: boolean;
}

export function AccountSummaryHeader({
  name,
  type,
  currency,
  totalValue,
  cashBalance,
  unrealizedPL,
  unrealizedPLPercent,
  isRefetching = false,
}: AccountSummaryHeaderProps) {
  const isPlPositive = isPositive(unrealizedPL);

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">{name}</h1>
          <span className="text-sm text-gray-500">
            {type} • {currency}
          </span>
        </div>

        {/* Recalculation indicator */}
        {isRefetching && (
          <Badge variant="warning" className="flex items-center gap-2">
            <Spinner size="sm" />
            Updating data...
          </Badge>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div>
          <div className="text-sm text-gray-600 mb-1">Total Value</div>
          <div className="text-2xl font-bold text-gray-900">
            {formatDecimal(totalValue)} {currency}
          </div>
        </div>

        <div>
          <div className="text-sm text-gray-600 mb-1">Cash Balance</div>
          <div className="text-2xl font-bold text-gray-900">
            {formatDecimal(cashBalance)} {currency}
          </div>
        </div>

        <div>
          <div className="text-sm text-gray-600 mb-1">Unrealized P/L</div>
          <div
            className={`text-2xl font-bold ${
              isPlPositive ? 'text-green-600' : 'text-red-600'
            }`}
          >
            {isPlPositive ? '+' : ''}
            {formatDecimal(unrealizedPL)} {currency}
          </div>
          <div
            className={`text-sm ${
              isPlPositive ? 'text-green-600' : 'text-red-600'
            }`}
          >
            {formatPercent(unrealizedPLPercent)}
          </div>
        </div>
      </div>
    </div>
  );
}
