'use client';

import { Eye, EyeOff } from 'lucide-react';

import { useCurrency } from '@/lib/context/currency-context';
import { usePrivacyToggle } from '@/lib/hooks/usePrivacyToggle';
import { formatCurrency } from '@/lib/utils/format';
import type { DecimalString } from '@/lib/types';

interface TotalAssetCardProps {
  totalKRW: DecimalString;
  totalUSD: DecimalString;
}

export function TotalAssetCard({ totalKRW, totalUSD }: TotalAssetCardProps) {
  const { currency, toggleCurrency } = useCurrency();
  const { isHidden, toggle: togglePrivacy } = usePrivacyToggle();

  const displayAmount = currency === 'KRW' ? totalKRW : totalUSD;

  return (
    <div className="rounded-xl border border-[var(--hairline-strong)] bg-[var(--surface-card)] p-6">
      <div className="mb-4 flex items-center justify-between gap-4">
        <h2 className="text-sm font-medium tracking-[0] text-[var(--charcoal)]">
          Total Assets
        </h2>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={togglePrivacy}
            className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-[var(--hairline-strong)] bg-[var(--surface-elevated)] text-[var(--charcoal)] transition hover:text-[var(--ink)]"
            title={isHidden ? 'Show amounts' : 'Hide amounts'}
            aria-label={isHidden ? 'Show amounts' : 'Hide amounts'}
          >
            {isHidden ? <Eye size={17} /> : <EyeOff size={17} />}
          </button>
          <button
            type="button"
            onClick={toggleCurrency}
            className="h-9 rounded-lg border border-[var(--primary)] bg-[var(--primary)] px-3 text-sm font-medium tracking-[0] text-[var(--primary-on)] transition hover:bg-[var(--surface-light)]"
          >
            {currency === 'KRW' ? 'USD' : 'KRW'}
          </button>
        </div>
      </div>

      <div className="resend-display text-4xl tracking-[0] sm:text-5xl">
        {formatCurrency(displayAmount, currency, isHidden)}
      </div>

      {!isHidden && (
        <div className="mt-3 text-sm text-[var(--mute)]">
          {currency === 'KRW'
            ? `≈ ${formatCurrency(totalUSD, 'USD')}`
            : `≈ ${formatCurrency(totalKRW, 'KRW')}`}
        </div>
      )}
    </div>
  );
}
