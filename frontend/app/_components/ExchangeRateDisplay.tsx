'use client';

import { formatNumber } from '@/lib/utils/format';

interface ExchangeRateDisplayProps {
  rate: number;
  updatedAt: string;
}

export function ExchangeRateDisplay({
  rate,
  updatedAt,
}: ExchangeRateDisplayProps) {
  const updateTime = new Date(updatedAt).toLocaleString('ko-KR', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="text-sm text-gray-600 mb-1">Exchange Rate (USD/KRW)</div>
      <div className="text-2xl font-bold text-gray-900">
        ₩{formatNumber(rate, 2)}
      </div>
      <div className="text-xs text-gray-500 mt-1">Updated: {updateTime}</div>
    </div>
  );
}
