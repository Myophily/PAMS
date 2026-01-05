'use client';

import type { Holding } from '@/lib/types';
import { formatPercent } from '@/lib/utils/format';

interface HoldingsTableProps {
  holdings: Holding[];
  currency: string;
}

export function HoldingsTable({ holdings, currency }: HoldingsTableProps) {
  if (holdings.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6 text-center text-gray-500">
        No holdings in this account
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Asset
            </th>
            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
              Quantity
            </th>
            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
              Avg Price
            </th>
            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
              Current Price
            </th>
            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
              Value
            </th>
            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
              Return
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {holdings.map((holding) => (
            <tr key={holding.id} className="hover:bg-gray-50">
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="text-sm font-medium text-gray-900">
                  {holding.ticker}
                </div>
                {holding.ticker_name && (
                  <div className="text-sm text-gray-500">
                    {holding.ticker_name}
                  </div>
                )}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900">
                {holding.quantity.toLocaleString()}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900">
                {holding.avg_price.toLocaleString()}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900">
                {holding.current_price.toLocaleString()}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900">
                {holding.current_value.toLocaleString()} {currency}
              </td>
              <td
                className={`px-6 py-4 whitespace-nowrap text-right text-sm font-medium ${
                  holding.unrealized_pl >= 0 ? 'text-green-600' : 'text-red-600'
                }`}
              >
                {formatPercent(holding.unrealized_pl_percent)}
                <div className="text-xs">
                  ({holding.unrealized_pl >= 0 ? '+' : ''}
                  {holding.unrealized_pl.toLocaleString()})
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
