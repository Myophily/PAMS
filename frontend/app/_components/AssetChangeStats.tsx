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
    <div className="grid grid-cols-3 gap-4">
      {periods.map(({ label, key, data }) => {
        const isAmountPositive = isPositive(data.amount_krw);
        return (
          <div key={key} className="bg-white rounded-lg shadow p-4">
            <div className="text-sm text-gray-600 mb-1">{label}</div>
            <div
              className={`text-2xl font-bold ${
                isAmountPositive ? 'text-green-600' : 'text-red-600'
              }`}
            >
              {formatPercent(data.percent)}
            </div>
            <div className="text-sm text-gray-500 mt-1">
              {isAmountPositive ? '+' : ''}
              {formatDecimal(data.amount_krw)} KRW
            </div>
          </div>
        );
      })}
    </div>
  );
}
