'use client';

import { useEffect, useRef, useState } from 'react';
import { createChart, CandlestickSeries, type IChartApi, type CandlestickData as LWCCandlestickData } from 'lightweight-charts';
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
  const [isLoading, setIsLoading] = useState(true);

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
        background: { color: '#ffffff' },
        textColor: '#333',
      },
      grid: {
        vertLines: { color: '#f0f0f0' },
        horzLines: { color: '#f0f0f0' },
      },
      timeScale: {
        borderColor: '#ccc',
        timeVisible: true,
        secondsVisible: false,
      },
      rightPriceScale: {
        borderColor: '#ccc',
      },
    });

    chartRef.current = chart;

    // Add candlestick series (v5 API)
    const candlestickSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#10B981', // Green for gains
      downColor: '#EF4444', // Red for losses
      borderVisible: false,
      wickUpColor: '#10B981',
      wickDownColor: '#EF4444',
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

    setIsLoading(false);

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
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-bold text-gray-900 mb-4">Asset Growth</h3>
        <div className="flex items-center justify-center h-[400px] text-gray-500">
          No data available
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      {/* Header with period selector */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-bold text-gray-900">Asset Growth</h3>

        {/* Period selector buttons */}
        <div className="flex gap-2">
          <button
            onClick={() => onPeriodChange('daily')}
            className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
              period === 'daily'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Daily
          </button>
          <button
            onClick={() => onPeriodChange('monthly')}
            className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
              period === 'monthly'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Monthly
          </button>
          <button
            onClick={() => onPeriodChange('annual')}
            className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
              period === 'annual'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Annual
          </button>
        </div>
      </div>

      {/* Chart container */}
      <div ref={chartContainerRef} className="w-full" />

      {isLoading && (
        <div className="flex items-center justify-center h-[400px]">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
        </div>
      )}
    </div>
  );
}
