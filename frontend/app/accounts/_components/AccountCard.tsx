'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import type { AccountWithBalance } from '@/lib/types';
import { Badge } from '@/components/ui/Badge';
import { formatDecimal } from '@/lib/utils/decimal';

interface AccountCardProps {
  account: AccountWithBalance;
}

// Configuration-driven action buttons
const ACCOUNT_ACTIONS: Record<string, string[]> = {
  Checking: ['transfer', 'deposit', 'withdrawal'],
  Brokerage: ['buy', 'sell', 'dividend', 'transfer'],
  Foreign: ['exchange', 'transfer'],
  MMF: ['interest', 'transfer'],
};

const ACTION_LABELS: Record<string, string> = {
  transfer: 'Transfer',
  deposit: 'Deposit',
  withdrawal: 'Withdraw',
  buy: 'Buy',
  sell: 'Sell',
  dividend: 'Dividend',
  exchange: 'Exchange',
  interest: 'Interest',
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
};

export function AccountCard({ account }: AccountCardProps) {
  const router = useRouter();
  const actions = ACCOUNT_ACTIONS[account.type] || [];

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
      <div className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition cursor-pointer">
        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-xl font-bold">{account.name}</h3>
            <Badge variant="default">{account.type}</Badge>
          </div>
          <span className="text-sm text-gray-500">{account.currency}</span>
        </div>

        <div className="mb-4">
          <div className="text-3xl font-bold text-gray-900">
            {formatDecimal(account.balance)} {account.currency}
          </div>
          <div className="text-sm text-gray-600 mt-1">
            ${formatDecimal(account.balance_usd)}
          </div>
        </div>

        <div className="text-sm text-gray-500 mb-4">
          {account.holdings_count} {account.holdings_count === 1 ? 'holding' : 'holdings'}
        </div>

        {/* Action buttons */}
        <div className="flex flex-wrap gap-2">
          {actions.map((action) => (
            <button
              key={action}
              className="text-sm px-3 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition"
              onClick={(e) => handleAction(action, e)}
            >
              {ACTION_LABELS[action] || action}
            </button>
          ))}
        </div>
      </div>
    </Link>
  );
}
