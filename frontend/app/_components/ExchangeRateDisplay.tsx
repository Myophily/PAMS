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
    <div className="rounded-xl border border-[var(--hairline-strong)] bg-[var(--surface-card)] p-4">
      <div className="mb-1 text-sm font-medium tracking-[0] text-[var(--charcoal)]">
        Exchange Rate (USD/KRW)
      </div>
      <div className="font-mono text-2xl font-semibold text-[var(--ink)]">
        ₩{formatNumber(rate, 2)}
      </div>
      <div className="mt-1 text-xs text-[var(--mute)]">Updated: {updateTime}</div>
    </div>
  );
}
