'use client';

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
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex justify-between items-center mb-2">
        <h2 className="text-gray-600 text-sm font-medium">Total Assets</h2>
        <div className="flex gap-2">
          <button
            onClick={togglePrivacy}
            className="text-gray-400 hover:text-gray-600 transition"
            title={isHidden ? 'Show amounts' : 'Hide amounts'}
          >
            {isHidden ? '👁️' : '👁️‍🗨️'}
          </button>
          <button
            onClick={toggleCurrency}
            className="text-sm px-2 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition font-medium"
          >
            {currency === 'KRW' ? 'USD' : 'KRW'}
          </button>
        </div>
      </div>

      <div className="text-4xl font-bold text-gray-900">
        {formatCurrency(displayAmount, currency, isHidden)}
      </div>

      {!isHidden && (
        <div className="text-sm text-gray-500 mt-2">
          {currency === 'KRW'
            ? `≈ ${formatCurrency(totalUSD, 'USD')}`
            : `≈ ${formatCurrency(totalKRW, 'KRW')}`}
        </div>
      )}
    </div>
  );
}
