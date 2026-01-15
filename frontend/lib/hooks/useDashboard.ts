import { useQuery } from '@tanstack/react-query';
import type { DashboardSummary, AssetChartData, CandlestickChartData, CandlestickPeriod } from '../types';

// Get dashboard summary
export function useDashboardSummary() {
  return useQuery<DashboardSummary>({
    queryKey: ['dashboard', 'summary'],
    queryFn: async () => {
      const res = await fetch('/api/dashboard/summary');
      if (!res.ok) throw new Error('Failed to fetch dashboard summary');
      const data = await res.json();
      return data.data || data;
    },
    staleTime: 0, // Always refetch on mount for real-time exchange rate
  });
}

// Get asset chart data
export function useAssetChart(period: string = '1M', currency: string = 'KRW') {
  return useQuery<{ chart_data: AssetChartData[] }>({
    queryKey: ['dashboard', 'chart', period, currency],
    queryFn: async () => {
      const res = await fetch(`/api/dashboard/chart?period=${period}&currency=${currency}`);
      if (!res.ok) throw new Error('Failed to fetch chart data');
      const data = await res.json();
      return data.data || data;
    },
  });
}

// Get candlestick chart data
export function useCandlestickChart(
  period: CandlestickPeriod = 'daily',
  currency: string = 'KRW'
) {
  return useQuery<CandlestickChartData>({
    queryKey: ['dashboard', 'candlestick-chart', period, currency],
    queryFn: async () => {
      const res = await fetch(
        `/api/dashboard/candlestick-chart?period=${period}&currency=${currency}`
      );
      if (!res.ok) throw new Error('Failed to fetch candlestick chart data');
      const data = await res.json();
      return data.data || data;
    },
    staleTime: 60000, // 1 minute
  });
}
