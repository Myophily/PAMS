'use client';

import { DecimalString, MonthlyCashFlowSummary as MonthlySummaryType } from '@/lib/types';
import { formatDecimal, parseDecimal } from '@/lib/utils/decimal';
import { CURRENCY_SYMBOLS } from '@/lib/utils/currency';

interface MonthlyCashFlowSummaryProps extends MonthlySummaryType {
  monthLabel: string;
  currency: string;
  accountCount?: number;
}

export function MonthlyCashFlowSummary({
  monthLabel,
  totalDebit,
  totalCredit,
  netCashFlow,
  openingBalance,
  closingBalance,
  transactionCount,
  currency,
  accountCount
}: MonthlyCashFlowSummaryProps) {
  const netFlow = parseDecimal(netCashFlow);
  const isPositive = netFlow > 0;
  const isZero = netFlow === 0;

  const bgColor = isZero
    ? 'bg-gray-50 border-gray-200'
    : isPositive
      ? 'bg-green-50 border-green-200'
      : 'bg-red-50 border-red-200';

  const netFlowColor = isZero
    ? 'text-gray-900'
    : isPositive
      ? 'text-green-700'
      : 'text-red-700';

  const symbol = CURRENCY_SYMBOLS[currency] || currency + ' ';

  return (
    <div className={`rounded-lg border-2 ${bgColor} p-6`}>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-gray-900">
          {monthLabel} Cash Flow Summary
        </h2>
        <div className="text-sm text-gray-600">
          {transactionCount} transaction{transactionCount !== 1 ? 's' : ''}
          {accountCount !== undefined && ` • ${accountCount} account${accountCount !== 1 ? 's' : ''}`}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Total Debit */}
        <div>
          <div className="text-sm text-gray-600 mb-1 flex items-center gap-1">
            <span className="text-red-600">↓</span>
            Total Debit (Money Out)
          </div>
          <div className="text-2xl font-bold text-red-600 font-mono">
            {symbol}{formatDecimal(totalDebit)}
          </div>
        </div>

        {/* Total Credit */}
        <div>
          <div className="text-sm text-gray-600 mb-1 flex items-center gap-1">
            <span className="text-green-600">↑</span>
            Total Credit (Money In)
          </div>
          <div className="text-2xl font-bold text-green-600 font-mono">
            {symbol}{formatDecimal(totalCredit)}
          </div>
        </div>

        {/* Net Cash Flow */}
        <div>
          <div className="text-sm text-gray-600 mb-1">
            Net Cash Flow
          </div>
          <div className={`text-3xl font-bold font-mono ${netFlowColor}`}>
            {netFlow >= 0 ? '+' : ''}{symbol}{formatDecimal(netCashFlow)}
          </div>
        </div>
      </div>

      {/* Opening/Closing Balance */}
      <div className="mt-4 pt-4 border-t border-gray-300 grid grid-cols-2 gap-4">
        <div>
          <span className="text-sm text-gray-600">Opening Balance: </span>
          <span className="font-semibold text-gray-900 font-mono">
            {symbol}{formatDecimal(openingBalance)}
          </span>
        </div>
        <div>
          <span className="text-sm text-gray-600">Closing Balance: </span>
          <span className="font-semibold text-gray-900 font-mono">
            {symbol}{formatDecimal(closingBalance)}
          </span>
        </div>
      </div>
    </div>
  );
}
