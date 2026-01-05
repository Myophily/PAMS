'use client';

import { AssetVolatilityChart } from '@/components/charts/AssetVolatilityChart';
import { DividendCalendar } from '@/components/charts/DividendCalendar';

interface AccountAnalysisChartsProps {
  accountId: number;
}

export function AccountAnalysisCharts({ accountId }: AccountAnalysisChartsProps) {
  // TODO: Fetch account-specific chart data and dividends
  // For now, showing placeholder

  return (
    <div className="space-y-6">
      <AssetVolatilityChart data={[]} />

      <DividendCalendar dividends={[]} />

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <p className="text-gray-700">
          Account-specific analysis charts coming soon in Phase 4.
        </p>
      </div>
    </div>
  );
}
