'use client';

import { Trash2 } from 'lucide-react';
import { useRouter } from 'next/navigation';

import { formatCurrency, formatPercent } from '@/lib/utils/format';
import { formatDecimal, isPositive } from '@/lib/utils/decimal';
import type { DecimalString } from '@/lib/types';
import { Badge } from '@/components/ui/Badge';
import { Spinner } from '@/components/ui/Spinner';

interface AccountSummaryHeaderProps {
  accountId: number;
  name: string;
  type: string;
  currency: string;
  totalValue: DecimalString;
  totalValueKRW: DecimalString;
  cashBalance: DecimalString;
  cashBalanceKRW: DecimalString;
  unrealizedPL: DecimalString;
  unrealizedPLKRW: DecimalString;
  unrealizedPLPercent: DecimalString;
  isRefetching?: boolean;
}

export function AccountSummaryHeader({
  accountId,
  name,
  type,
  currency,
  totalValue,
  totalValueKRW,
  cashBalance,
  cashBalanceKRW,
  unrealizedPL,
  unrealizedPLKRW,
  unrealizedPLPercent,
  isRefetching = false,
}: AccountSummaryHeaderProps) {
  const router = useRouter();
  const isPlPositive = isPositive(unrealizedPL);
  const isKRWAccount = currency === 'KRW';

  const handleDeleteClick = () => {
    router.push(`/accounts?modal=delete-account&accountId=${accountId}`);
  };

  return (
    <div className="rounded-xl border border-[var(--hairline-strong)] bg-[var(--surface-card)] p-6">
      <div className="mb-6 flex flex-col justify-between gap-4 sm:flex-row sm:items-start">
        <div>
          <p className="resend-caption mb-3 uppercase tracking-[0]">
            {type} • {currency}
          </p>
          <h1 className="resend-display text-5xl tracking-[0] sm:text-6xl">
            {name}
          </h1>
        </div>

        <div className="flex items-center gap-3">
          {isRefetching && (
            <Badge variant="warning" className="flex items-center gap-2">
              <Spinner size="sm" />
              Updating data...
            </Badge>
          )}

          <button
            type="button"
            onClick={handleDeleteClick}
            className="inline-flex h-9 items-center gap-2 rounded-lg border border-[rgba(255,32,71,0.38)] bg-[rgba(255,32,71,0.1)] px-4 text-sm font-medium tracking-[0] text-[var(--accent-red)] transition hover:bg-[rgba(255,32,71,0.16)]"
          >
            <Trash2 size={15} />
            Delete Account
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div>
          <div className="mb-1 text-sm font-medium tracking-[0] text-[var(--charcoal)]">
            Total Value
          </div>
          <div className="font-mono text-2xl font-semibold text-[var(--ink)]">
            {formatCurrency(totalValueKRW, 'KRW')}
          </div>
          {!isKRWAccount && (
            <div className="mt-1 text-sm text-[var(--charcoal)]">
              ≈ {formatDecimal(totalValue)} {currency}
            </div>
          )}
        </div>

        <div>
          <div className="mb-1 text-sm font-medium tracking-[0] text-[var(--charcoal)]">
            Cash Balance
          </div>
          <div className="font-mono text-2xl font-semibold text-[var(--ink)]">
            {formatCurrency(cashBalanceKRW, 'KRW')}
          </div>
          {!isKRWAccount && (
            <div className="mt-1 text-sm text-[var(--charcoal)]">
              ≈ {formatDecimal(cashBalance)} {currency}
            </div>
          )}
        </div>

        <div>
          <div className="mb-1 text-sm font-medium tracking-[0] text-[var(--charcoal)]">
            Unrealized P/L
          </div>
          <div
            className={`font-mono text-2xl font-semibold ${
              isPlPositive
                ? 'text-[var(--accent-green)]'
                : 'text-[var(--accent-red)]'
            }`}
          >
            {isPlPositive ? '+' : ''}
            {formatCurrency(unrealizedPLKRW, 'KRW')}
          </div>
          <div
            className={`text-sm ${
              isPlPositive
                ? 'text-[var(--accent-green)]'
                : 'text-[var(--accent-red)]'
            }`}
          >
            {isKRWAccount ? (
              formatPercent(unrealizedPLPercent)
            ) : (
              `${formatPercent(unrealizedPLPercent)} • ≈ ${formatDecimal(unrealizedPL)} ${currency}`
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
