'use client';

import { LedgerRow } from '@/lib/types';
import { formatDate } from '@/lib/utils/datetime';
import { formatDecimal } from '@/lib/utils/decimal';
import { CURRENCY_SYMBOLS } from '@/lib/utils/currency';

interface LedgerTableProps {
  rows: LedgerRow[];
  currency?: string;
  showAccount?: boolean;  // For consolidated view
  isLoading?: boolean;
}

/**
 * Traditional accounting ledger table component.
 *
 * Displays transactions in ledger format with:
 * - Date column
 * - Description with counterparty info
 * - Debit column (money out, in red)
 * - Credit column (money in, in green)
 * - Running balance column (bold)
 * - Optional account name column for consolidated view
 *
 * @example
 * <LedgerTable
 *   rows={ledgerRows}
 *   currency="KRW"
 *   showAccount={false}
 * />
 */
export function LedgerTable({
  rows,
  currency = 'KRW',
  showAccount = false,
  isLoading = false
}: LedgerTableProps) {
  const getCurrencySymbol = (curr: string): string => {
    return CURRENCY_SYMBOLS[curr] || curr + ' ';
  };

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center rounded-xl border border-[var(--hairline-strong)] bg-[var(--surface-card)]">
        <div className="text-[var(--mute)]">Loading ledger...</div>
      </div>
    );
  }

  if (rows.length === 0) {
    return (
      <div className="rounded-xl border border-[var(--hairline-strong)] bg-[var(--surface-card)] p-8 text-center">
        <p className="text-[var(--mute)]">No transactions to display</p>
        <p className="mt-2 text-sm text-[var(--ash)]">
          Transactions will appear here once you add them to this account.
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-xl border border-[var(--hairline-strong)] bg-[var(--surface-card)]">
      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <thead className="border-b border-[var(--hairline)] bg-[rgba(255,255,255,0.03)]">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-[0] text-[var(--mute)]">
                Date
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-[0] text-[var(--mute)]">
                Description
              </th>
              {showAccount && (
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-[0] text-[var(--mute)]">
                  Account
                </th>
              )}
              <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-[0] text-[var(--mute)]">
                Debit
              </th>
              <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-[0] text-[var(--mute)]">
                Credit
              </th>
              <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-[0] text-[var(--mute)]">
                Balance
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--hairline)]">
            {rows.map((row, index) => (
              <tr
                key={`${row.id}-${index}`}
                className="transition-colors hover:bg-[rgba(255,255,255,0.03)]"
              >
                <td className="whitespace-nowrap px-4 py-3 text-sm text-[var(--body)]">
                  {formatDate(row.date)}
                </td>
                <td className="px-4 py-3">
                  <div className="text-sm text-[var(--ink)]">{row.description}</div>
                  {row.counterpartyAccount && (
                    <div className="mt-0.5 text-xs text-[var(--mute)]">
                      {row.counterpartyAccount}
                    </div>
                  )}
                </td>
                {showAccount && (
                  <td className="whitespace-nowrap px-4 py-3 text-sm text-[var(--body)]">
                    {row.accountName || '-'}
                  </td>
                )}
                <td className="whitespace-nowrap px-4 py-3 text-right font-mono text-sm">
                  {row.debit !== '0.00' ? (
                    <span className="text-[var(--accent-red)]">
                      {getCurrencySymbol(currency)}
                      {formatDecimal(row.debit)}
                    </span>
                  ) : (
                    <span className="text-[var(--stone)]">-</span>
                  )}
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-right font-mono text-sm">
                  {row.credit !== '0.00' ? (
                    <span className="text-[var(--accent-green)]">
                      {getCurrencySymbol(currency)}
                      {formatDecimal(row.credit)}
                    </span>
                  ) : (
                    <span className="text-[var(--stone)]">-</span>
                  )}
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-right font-mono text-sm font-semibold text-[var(--ink)]">
                  {getCurrencySymbol(currency)}
                  {formatDecimal(row.balance)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="border-t border-[var(--hairline)] bg-[rgba(255,255,255,0.03)] px-4 py-3">
        <div className="flex justify-between items-center text-sm">
          <span className="text-[var(--charcoal)]">
            {rows.length} transaction{rows.length !== 1 ? 's' : ''}
          </span>
          <div className="flex items-center gap-4">
            <span className="text-[var(--charcoal)]">
              Final Balance:
            </span>
            <span className="font-mono font-semibold text-[var(--ink)]">
              {getCurrencySymbol(currency)}
              {rows.length > 0 ? formatDecimal(rows[rows.length - 1].balance) : '0.00'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
