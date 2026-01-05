'use client';

import { formatPercent } from '@/lib/utils/format';

interface AssetChangeStatsProps {
  changes: {
    day: { amount_krw: number; amount_usd: number; percent: number };
    month: { amount_krw: number; amount_usd: number; percent: number };
    year: { amount_krw: number; amount_usd: number; percent: number };
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
        const isPositive = data.amount_krw >= 0;
        return (
          <div key={key} className="bg-white rounded-lg shadow p-4">
            <div className="text-sm text-gray-600 mb-1">{label}</div>
            <div
              className={`text-2xl font-bold ${
                isPositive ? 'text-green-600' : 'text-red-600'
              }`}
            >
              {formatPercent(data.percent)}
            </div>
            <div className="text-sm text-gray-500 mt-1">
              {isPositive ? '+' : ''}
              {data.amount_krw.toLocaleString()} KRW
            </div>
          </div>
        );
      })}
    </div>
  );
}
