import { useQuery } from '@tanstack/react-query';
import type { DashboardSummary, AssetChartData } from '../types';

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
    staleTime: 60000, // Consider data fresh for 1 minute
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
