'use client';

import { useEffect, useRef } from 'react';

import {
  CandlestickSeries,
  createChart,
  type CandlestickData as LWCCandlestickData,
  type IChartApi,
} from 'lightweight-charts';

import { parseDecimal } from '@/lib/utils/decimal';
import type { CandlestickData, CandlestickPeriod } from '@/lib/types';

interface AssetCandlestickChartProps {
  data: CandlestickData[];
  period: CandlestickPeriod;
  onPeriodChange: (period: CandlestickPeriod) => void;
}

export function AssetCandlestickChart({
  data,
  period,
  onPeriodChange
}: AssetCandlestickChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    // Clean up previous chart instance
    if (chartRef.current) {
      chartRef.current.remove();
      chartRef.current = null;
    }

    // Create chart
    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 400,
      layout: {
        background: { color: '#0a0a0c' },
        textColor: 'rgba(252,253,255,0.7)',
      },
      grid: {
        vertLines: { color: 'rgba(255,255,255,0.06)' },
        horzLines: { color: 'rgba(255,255,255,0.06)' },
      },
      timeScale: {
        borderColor: 'rgba(255,255,255,0.14)',
        timeVisible: true,
        secondsVisible: false,
      },
      rightPriceScale: {
        borderColor: 'rgba(255,255,255,0.14)',
      },
    });

    chartRef.current = chart;

    // Add candlestick series (v5 API)
    const candlestickSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#11ff99',
      downColor: '#ff2047',
      borderVisible: false,
      wickUpColor: '#11ff99',
      wickDownColor: '#ff2047',
    });

    // Transform data for lightweight-charts
    const chartData: LWCCandlestickData[] = data.map((candle) => ({
      time: candle.time,
      open: parseDecimal(candle.open),
      high: parseDecimal(candle.high),
      low: parseDecimal(candle.low),
      close: parseDecimal(candle.close),
    }));

    candlestickSeries.setData(chartData);

    // Fit content
    chart.timeScale().fitContent();

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
        });
      }
    };

    window.addEventListener('resize', handleResize);

    // Cleanup
    return () => {
      window.removeEventListener('resize', handleResize);
      if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
      }
    };
  }, [data]);

  if (!data || data.length === 0) {
    return (
      <div className="rounded-xl border border-[var(--hairline-strong)] bg-[var(--surface-card)] p-6">
        <h3 className="mb-4 text-lg font-medium tracking-[0] text-[var(--ink)]">
          Asset Growth
        </h3>
        <div className="flex h-[400px] items-center justify-center text-[var(--mute)]">
          No data available
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-[var(--hairline-strong)] bg-[var(--surface-card)] p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium tracking-[0] text-[var(--ink)]">
          Asset Growth
        </h3>

        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => onPeriodChange('daily')}
            className={`h-8 rounded-lg border px-3 text-sm font-medium tracking-[0] transition-colors ${
              period === 'daily'
                ? 'border-[var(--primary)] bg-[var(--primary)] text-[var(--primary-on)]'
                : 'border-[var(--hairline-strong)] bg-[var(--surface-elevated)] text-[var(--body)] hover:text-[var(--ink)]'
            }`}
          >
            Daily
          </button>
          <button
            type="button"
            onClick={() => onPeriodChange('monthly')}
            className={`h-8 rounded-lg border px-3 text-sm font-medium tracking-[0] transition-colors ${
              period === 'monthly'
                ? 'border-[var(--primary)] bg-[var(--primary)] text-[var(--primary-on)]'
                : 'border-[var(--hairline-strong)] bg-[var(--surface-elevated)] text-[var(--body)] hover:text-[var(--ink)]'
            }`}
          >
            Monthly
          </button>
          <button
            type="button"
            onClick={() => onPeriodChange('annual')}
            className={`h-8 rounded-lg border px-3 text-sm font-medium tracking-[0] transition-colors ${
              period === 'annual'
                ? 'border-[var(--primary)] bg-[var(--primary)] text-[var(--primary-on)]'
                : 'border-[var(--hairline-strong)] bg-[var(--surface-elevated)] text-[var(--body)] hover:text-[var(--ink)]'
            }`}
          >
            Annual
          </button>
        </div>
      </div>

      <div ref={chartContainerRef} className="w-full" />
    </div>
  );
}
