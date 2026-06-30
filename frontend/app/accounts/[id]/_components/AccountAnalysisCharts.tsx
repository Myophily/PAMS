'use client';

import { AssetVolatilityChart } from '@/components/charts/AssetVolatilityChart';
import { DividendCalendar } from '@/components/charts/DividendCalendar';

interface AccountAnalysisChartsProps {
  accountId: number;
}

export function AccountAnalysisCharts({ accountId }: AccountAnalysisChartsProps) {
  void accountId;

  // TODO: Fetch account-specific chart data and dividends
  // For now, showing placeholder

  return (
    <div className="space-y-6">
      <AssetVolatilityChart data={[]} />

      <DividendCalendar dividends={[]} />

      <div className="rounded-xl border border-[var(--hairline-strong)] bg-[rgba(59,158,255,0.1)] p-6">
        <p className="text-[var(--body)]">
          Account-specific analysis charts coming soon in Phase 4.
        </p>
      </div>
    </div>
  );
}
