"use client";

import { useState } from 'react';
import { useDashboardSummary, useCandlestickChart } from "@/lib/hooks/useDashboard";
import { useCurrency } from "@/lib/context/currency-context";
import { Spinner } from "@/components/ui/Spinner";
import { TotalAssetCard } from "./_components/TotalAssetCard";
import { ExchangeRateDisplay } from "./_components/ExchangeRateDisplay";
import { AssetChangeStats } from "./_components/AssetChangeStats";
import { AssetAllocationChart } from "@/components/charts/AssetAllocationChart";
import { TopAssetsBarChart } from "@/components/charts/TopAssetsBarChart";
import { AssetCandlestickChart } from "@/components/charts/AssetCandlestickChart";
import type { CandlestickPeriod } from "@/lib/types";

export default function HomePage() {
  const { currency } = useCurrency();
  const [chartPeriod, setChartPeriod] = useState<CandlestickPeriod>('daily');

  const { data: summary, isLoading, error } = useDashboardSummary();
  const { data: candlestickData } = useCandlestickChart(chartPeriod, currency);

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Spinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-xl border border-[rgba(255,32,71,0.38)] bg-[rgba(255,32,71,0.1)] px-4 py-3 text-[var(--accent-red)]">
        <strong>Error:</strong> {error.message}
      </div>
    );
  }

  if (!summary) {
    return (
      <div className="rounded-xl border border-[rgba(255,197,61,0.38)] bg-[rgba(255,197,61,0.1)] p-6">
        <h3 className="mb-2 text-lg font-medium tracking-[0] text-[var(--ink)]">
          No Data Available
        </h3>
        <p className="text-[var(--body)]">
          Create your first account to start tracking your assets.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <p className="resend-caption mb-3 uppercase tracking-[0]">
          Local-first asset desk
        </p>
        <h1 className="resend-display text-5xl tracking-[0] sm:text-6xl">
          Dashboard
        </h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <TotalAssetCard
            totalKRW={summary.total_assets.krw}
            totalUSD={summary.total_assets.usd}
          />
        </div>
        <ExchangeRateDisplay
          rate={parseFloat(summary.current_exchange_rate.usd_to_krw)}
          updatedAt={summary.current_exchange_rate.updated_at}
        />
      </div>

      <AssetChangeStats changes={summary.changes} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <AssetAllocationChart data={summary.allocation} riskSummary={summary.risk_summary} />
        <TopAssetsBarChart assets={summary.top_assets} />
      </div>

      <AssetCandlestickChart
        data={candlestickData?.candles || []}
        period={chartPeriod}
        onPeriodChange={setChartPeriod}
      />
    </div>
  );
}
