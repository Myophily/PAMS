'use client';

import type { MonthlyCashFlowSummary as MonthlySummaryType } from '@/lib/types';
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
    ? 'bg-[var(--surface-card)] border-[var(--hairline-strong)]'
    : isPositive
      ? 'bg-[rgba(17,255,153,0.08)] border-[rgba(17,255,153,0.32)]'
      : 'bg-[rgba(255,32,71,0.08)] border-[rgba(255,32,71,0.32)]';

  const netFlowColor = isZero
    ? 'text-[var(--ink)]'
    : isPositive
      ? 'text-[var(--accent-green)]'
      : 'text-[var(--accent-red)]';

  const symbol = CURRENCY_SYMBOLS[currency] || currency + ' ';

  return (
    <div className={`rounded-xl border ${bgColor} p-6`}>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-medium tracking-[0] text-[var(--ink)]">
          {monthLabel} Cash Flow Summary
        </h2>
        <div className="text-sm text-[var(--charcoal)]">
          {transactionCount} transaction{transactionCount !== 1 ? 's' : ''}
          {accountCount !== undefined && ` • ${accountCount} account${accountCount !== 1 ? 's' : ''}`}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Total Debit */}
        <div>
          <div className="mb-1 flex items-center gap-1 text-sm text-[var(--charcoal)]">
            <span className="text-[var(--accent-red)]">↓</span>
            Total Debit (Money Out)
          </div>
          <div className="font-mono text-2xl font-semibold text-[var(--accent-red)]">
            {symbol}{formatDecimal(totalDebit)}
          </div>
        </div>

        {/* Total Credit */}
        <div>
          <div className="mb-1 flex items-center gap-1 text-sm text-[var(--charcoal)]">
            <span className="text-[var(--accent-green)]">↑</span>
            Total Credit (Money In)
          </div>
          <div className="font-mono text-2xl font-semibold text-[var(--accent-green)]">
            {symbol}{formatDecimal(totalCredit)}
          </div>
        </div>

        {/* Net Cash Flow */}
        <div>
          <div className="mb-1 text-sm text-[var(--charcoal)]">
            Net Cash Flow
          </div>
          <div className={`font-mono text-3xl font-semibold ${netFlowColor}`}>
            {netFlow >= 0 ? '+' : ''}{symbol}{formatDecimal(netCashFlow)}
          </div>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 border-t border-[var(--hairline)] pt-4 sm:grid-cols-2">
        <div>
          <span className="text-sm text-[var(--charcoal)]">Opening Balance: </span>
          <span className="font-mono font-semibold text-[var(--ink)]">
            {symbol}{formatDecimal(openingBalance)}
          </span>
        </div>
        <div>
          <span className="text-sm text-[var(--charcoal)]">Closing Balance: </span>
          <span className="font-mono font-semibold text-[var(--ink)]">
            {symbol}{formatDecimal(closingBalance)}
          </span>
        </div>
      </div>
    </div>
  );
}
