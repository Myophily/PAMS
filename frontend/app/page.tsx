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
      <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
        <strong>Error:</strong> {error.message}
      </div>
    );
  }

  if (!summary) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          No Data Available
        </h3>
        <p className="text-gray-700">
          Create your first account to start tracking your assets.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Dashboard</h1>

      {/* Top section: Total Assets + Exchange Rate */}
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

      {/* Asset change stats */}
      <AssetChangeStats changes={summary.changes} />

      {/* Charts section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <AssetAllocationChart data={summary.allocation} riskSummary={summary.risk_summary} />
        <TopAssetsBarChart assets={summary.top_assets} />
      </div>

      {/* Full width candlestick chart */}
      <AssetCandlestickChart
        data={candlestickData?.candles || []}
        period={chartPeriod}
        onPeriodChange={setChartPeriod}
      />
    </div>
  );
}
