'use client';

import type { Holding } from '@/lib/types';
import { formatPercent } from '@/lib/utils/format';
import { formatDecimal, isPositive } from '@/lib/utils/decimal';
import { isCurrencyTicker } from '@/lib/utils/currency';

interface HoldingsTableProps {
  holdings: Holding[];
  currency: string;
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

export function HoldingsTable({ holdings, currency }: HoldingsTableProps) {
  if (holdings.length === 0) {
    return (
      <div className="rounded-xl border border-[var(--hairline-strong)] bg-[var(--surface-card)] p-6 text-center text-[var(--mute)]">
        No holdings in this account
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-xl border border-[var(--hairline-strong)] bg-[var(--surface-card)]">
      <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-[var(--hairline)]">
        <thead className="bg-[rgba(255,255,255,0.03)]">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-[0] text-[var(--mute)]">
              Asset
            </th>
            <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-[0] text-[var(--mute)]">
              Quantity
            </th>
            <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-[0] text-[var(--mute)]">
              Avg Price
            </th>
            <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-[0] text-[var(--mute)]">
              Current Price
            </th>
            <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-[0] text-[var(--mute)]">
              Value
            </th>
            <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-[0] text-[var(--mute)]">
              Return
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-[var(--hairline)] bg-[var(--surface-card)]">
          {holdings.map((holding) => {
            const isStock = !isCurrencyTicker(holding.ticker);
            const priceSymbol = getCurrencySymbol(holding.price_currency);

            return (
              <tr key={holding.id} className="transition hover:bg-[rgba(255,255,255,0.03)]">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-medium text-[var(--ink)]">
                    {holding.ticker}
                  </div>
                  {holding.ticker_name && (
                    <div className="text-sm text-[var(--mute)]">
                      {holding.ticker_name}
                    </div>
                  )}
                </td>
                <td className="whitespace-nowrap px-6 py-4 text-right font-mono text-sm text-[var(--body)]">
                  {formatDecimal(holding.quantity)}
                </td>
                <td className="whitespace-nowrap px-6 py-4 text-right font-mono text-sm text-[var(--body)]">
                  {isStock && holding.price_currency ? priceSymbol : ''}
                  {formatDecimal(holding.avg_price)}
                </td>
                <td className="whitespace-nowrap px-6 py-4 text-right font-mono text-sm text-[var(--body)]">
                  {isStock && holding.price_currency ? priceSymbol : ''}
                  {formatDecimal(holding.current_price)}
                </td>
                <td className="whitespace-nowrap px-6 py-4 text-right font-mono text-sm text-[var(--ink)]">
                  {formatDecimal(holding.current_value)} {isCurrencyTicker(holding.ticker) ? holding.ticker : (isStock && holding.price_currency ? holding.price_currency : currency)}
                </td>
                <td
                  className={`whitespace-nowrap px-6 py-4 text-right font-mono text-sm font-medium ${
                    isPositive(holding.unrealized_pl)
                      ? 'text-[var(--accent-green)]'
                      : 'text-[var(--accent-red)]'
                  }`}
                >
                  {formatPercent(holding.unrealized_pl_percent)}
                  <div className="text-xs">
                    ({isPositive(holding.unrealized_pl) ? '+' : ''}
                    {formatDecimal(holding.unrealized_pl)})
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      </div>
    </div>
  );
}
