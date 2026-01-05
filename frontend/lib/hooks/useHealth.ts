import { useQuery } from '@tanstack/react-query';
import { HealthStatus } from '@/lib/types';

export function useHealth() {
  return useQuery<HealthStatus>({
    queryKey: ['health'],
    queryFn: async () => {
      const res = await fetch('/api/health');
      if (!res.ok) {
        throw new Error('Failed to fetch health status');
      }
      return res.json();
    },
  });
}
