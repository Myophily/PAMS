import { useQuery } from '@tanstack/react-query';
import type { StockPrice, ExchangeRate } from '../types';

// Fetch stock price
export function useStockPrice(ticker: string, date?: string) {
  return useQuery<StockPrice>({
    queryKey: ['market-data', 'price', ticker, date],
    queryFn: async () => {
      const params = new URLSearchParams({ ticker });
      if (date) params.append('date', date);

      const res = await fetch(`/api/market-data/price?${params}`);
      if (!res.ok) throw new Error('Failed to fetch price');
      const data = await res.json();
      return data.data || data;
    },
    enabled: !!ticker,
    staleTime: 300000, // 5 minutes
  });
}

// Fetch exchange rate
export function useExchangeRate(from: string, to: string, date?: string) {
  return useQuery<ExchangeRate>({
    queryKey: ['market-data', 'exchange-rate', from, to, date],
    queryFn: async () => {
      const params = new URLSearchParams({ from, to });
      if (date) params.append('date', date);

      const res = await fetch(`/api/market-data/exchange-rate?${params}`);
      if (!res.ok) throw new Error('Failed to fetch exchange rate');
      const data = await res.json();
      return data.data || data;
    },
    enabled: !!from && !!to,
    staleTime: 300000, // 5 minutes
  });
}
