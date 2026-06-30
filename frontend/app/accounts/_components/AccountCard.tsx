'use client';

import type { ReactNode } from 'react';

import {
  ArrowDown,
  ArrowLeftRight,
  ArrowUp,
  Banknote,
  CircleDollarSign,
  Coins,
  Trash2,
  TrendingDown,
  TrendingUp,
} from 'lucide-react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

import type { AccountWithBalance } from '@/lib/types';
import { Badge } from '@/components/ui/Badge';
import { formatCurrency } from '@/lib/utils/format';
import { getAccountTypeConfig } from '@/lib/config/accountTypeConfig';

interface AccountCardProps {
  account: AccountWithBalance;
}

// Action labels for buttons
const ACTION_LABELS: Record<string, string> = {
  transfer: 'Transfer',
  deposit: 'Deposit',
  withdrawal: 'Withdraw',
  buy: 'Buy',
  sell: 'Sell',
  dividend: 'Dividend',
  exchange: 'Exchange',
  interest: 'Interest',
  delete: 'Delete',
};

const ACTION_ICONS: Record<string, ReactNode> = {
  transfer: <ArrowLeftRight size={14} />,
  deposit: <ArrowDown size={14} />,
  withdrawal: <ArrowUp size={14} />,
  buy: <TrendingUp size={14} />,
  sell: <TrendingDown size={14} />,
  dividend: <Banknote size={14} />,
  exchange: <CircleDollarSign size={14} />,
  interest: <Coins size={14} />,
  delete: <Trash2 size={14} />,
};

// Map actions to modal names
const ACTION_TO_MODAL: Record<string, string> = {
  transfer: 'transfer',
  deposit: 'add-transaction',
  withdrawal: 'add-transaction',
  buy: 'buy',
  sell: 'sell',
  dividend: 'add-transaction',
  exchange: 'exchange',
  interest: 'add-transaction',
  delete: 'delete-account',
};

export function AccountCard({ account }: AccountCardProps) {
  const router = useRouter();
  const accountConfig = getAccountTypeConfig(account.type);
  const actions = accountConfig.primaryActions;

  // Use inferred currency from backend
  const currency = account.currency;

  const handleAction = (action: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();

    const modalName = ACTION_TO_MODAL[action];
    if (modalName) {
      router.push(`/accounts?modal=${modalName}&accountId=${account.id}`);
    }
  };

  return (
    <Link href={`/accounts/${account.id}`}>
      <div className="group rounded-xl border border-[var(--hairline-strong)] bg-[var(--surface-card)] p-6 transition hover:border-[rgba(252,253,255,0.28)]">
        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-xl font-medium tracking-[0] text-[var(--ink)]">
              {account.name}
            </h3>
            <Badge variant="default">{accountConfig.displayName}</Badge>
          </div>
          <span className="text-sm text-[var(--mute)]">{currency}</span>
        </div>

        <div className="mb-4">
          <div className="font-mono text-2xl font-semibold text-[var(--ink)]">
            {formatCurrency(
              account.total_value_krw || account.total_value || account.balance,
              'KRW'
            )}
          </div>
          <div className="mt-1 text-sm text-[var(--charcoal)]">
            ≈ {formatCurrency(account.balance_usd, 'USD')}
            <span className="ml-1 text-xs text-[var(--ash)]">
              ({account.currency})
            </span>
          </div>
        </div>

        <div className="mb-4 text-sm text-[var(--mute)]">
          {account.holdings_count} {account.holdings_count === 1 ? 'holding' : 'holdings'}
        </div>

        <div className="flex flex-wrap gap-2">
          {actions.map((action) => (
            <button
              key={action}
              type="button"
              className={`inline-flex h-8 items-center gap-1.5 rounded-lg border px-3 text-sm font-medium tracking-[0] transition ${
                action === 'delete'
                  ? 'border-[rgba(255,32,71,0.38)] bg-[rgba(255,32,71,0.1)] text-[var(--accent-red)] hover:bg-[rgba(255,32,71,0.16)]'
                  : 'border-[var(--hairline-strong)] bg-[var(--surface-elevated)] text-[var(--body)] hover:text-[var(--ink)]'
              }`}
              onClick={(e) => handleAction(action, e)}
            >
              {ACTION_ICONS[action]}
              {ACTION_LABELS[action] || action}
            </button>
          ))}
        </div>
      </div>
    </Link>
  );
}
