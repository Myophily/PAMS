'use client';

import { formatPercent } from '@/lib/utils/format';
import { formatDecimal, isPositive } from '@/lib/utils/decimal';
import type { DecimalString } from '@/lib/types';

interface AssetChangeStatsProps {
  changes: {
    day: { amount_krw: DecimalString; amount_usd: DecimalString; percent: DecimalString };
    month: { amount_krw: DecimalString; amount_usd: DecimalString; percent: DecimalString };
    year: { amount_krw: DecimalString; amount_usd: DecimalString; percent: DecimalString };
  };
}

export function AssetChangeStats({ changes }: AssetChangeStatsProps) {
  const periods = [
    { label: 'Day', key: 'day', data: changes.day },
    { label: 'Month', key: 'month', data: changes.month },
    { label: 'Year', key: 'year', data: changes.year },
  ];

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
      {periods.map(({ label, key, data }) => {
        const isAmountPositive = isPositive(data.amount_krw);
        return (
          <div
            key={key}
            className="rounded-xl border border-[var(--hairline-strong)] bg-[var(--surface-card)] p-4"
          >
            <div className="mb-1 text-sm font-medium tracking-[0] text-[var(--charcoal)]">
              {label}
            </div>
            <div
              className={`font-mono text-2xl font-semibold ${
                isAmountPositive
                  ? 'text-[var(--accent-green)]'
                  : 'text-[var(--accent-red)]'
              }`}
            >
              {formatPercent(data.percent)}
            </div>
            <div className="mt-1 text-sm text-[var(--mute)]">
              {isAmountPositive ? '+' : ''}
              {formatDecimal(data.amount_krw)} KRW
            </div>
          </div>
        );
      })}
    </div>
  );
}
