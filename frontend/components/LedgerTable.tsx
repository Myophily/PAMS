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
      <div className="flex justify-center items-center h-64 bg-white rounded-lg shadow">
        <div className="text-gray-500">Loading ledger...</div>
      </div>
    );
  }

  if (rows.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-8 text-center">
        <p className="text-gray-500">No transactions to display</p>
        <p className="text-sm text-gray-400 mt-2">
          Transactions will appear here once you add them to this account.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <thead className="bg-gray-50 border-b-2 border-gray-200">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                Date
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                Description
              </th>
              {showAccount && (
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                  Account
                </th>
              )}
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-700 uppercase tracking-wider">
                Debit
              </th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-700 uppercase tracking-wider">
                Credit
              </th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-700 uppercase tracking-wider">
                Balance
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {rows.map((row, index) => (
              <tr
                key={`${row.id}-${index}`}
                className="hover:bg-gray-50 transition-colors"
              >
                <td className="px-4 py-3 text-sm text-gray-900 whitespace-nowrap">
                  {formatDate(row.date)}
                </td>
                <td className="px-4 py-3">
                  <div className="text-sm text-gray-900">{row.description}</div>
                  {row.counterpartyAccount && (
                    <div className="text-xs text-gray-500 mt-0.5">
                      {row.counterpartyAccount}
                    </div>
                  )}
                </td>
                {showAccount && (
                  <td className="px-4 py-3 text-sm text-gray-700 whitespace-nowrap">
                    {row.accountName || '-'}
                  </td>
                )}
                <td className="px-4 py-3 text-right text-sm font-mono whitespace-nowrap">
                  {row.debit !== '0.00' ? (
                    <span className="text-red-600">
                      {getCurrencySymbol(currency)}
                      {formatDecimal(row.debit)}
                    </span>
                  ) : (
                    <span className="text-gray-300">-</span>
                  )}
                </td>
                <td className="px-4 py-3 text-right text-sm font-mono whitespace-nowrap">
                  {row.credit !== '0.00' ? (
                    <span className="text-green-600">
                      {getCurrencySymbol(currency)}
                      {formatDecimal(row.credit)}
                    </span>
                  ) : (
                    <span className="text-gray-300">-</span>
                  )}
                </td>
                <td className="px-4 py-3 text-right text-sm font-mono font-semibold text-gray-900 whitespace-nowrap">
                  {getCurrencySymbol(currency)}
                  {formatDecimal(row.balance)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Summary footer */}
      <div className="bg-gray-50 px-4 py-3 border-t border-gray-200">
        <div className="flex justify-between items-center text-sm">
          <span className="text-gray-600">
            {rows.length} transaction{rows.length !== 1 ? 's' : ''}
          </span>
          <div className="flex items-center gap-4">
            <span className="text-gray-600">
              Final Balance:
            </span>
            <span className="font-semibold text-gray-900">
              {getCurrencySymbol(currency)}
              {rows.length > 0 ? formatDecimal(rows[rows.length - 1].balance) : '0.00'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
