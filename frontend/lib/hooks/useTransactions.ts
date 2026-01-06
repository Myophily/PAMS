import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { TransactionDetail, CreateTransactionInput, CreateTransferInput } from '../types';

interface TransactionFilters {
  account_id?: number;
  type?: string;
  start_date?: string;
  end_date?: string;
  ticker?: string;
  limit?: number;
  offset?: number;
}

// List transactions with filters
export function useTransactions(filters: TransactionFilters = {}) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined) params.append(key, value.toString());
  });

  return useQuery<{ transactions: TransactionDetail[]; total: number }>({
    queryKey: ['transactions', filters],
    queryFn: async () => {
      const res = await fetch(`/api/transactions?${params}`);
      if (!res.ok) throw new Error('Failed to fetch transactions');
      const data = await res.json();
      return data.data || data;
    },
  });
}

// Get transaction details
export function useTransactionDetails(id: number) {
  return useQuery<{ transaction: TransactionDetail }>({
    queryKey: ['transactions', id],
    queryFn: async () => {
      const res = await fetch(`/api/transactions/${id}`);
      if (!res.ok) throw new Error('Failed to fetch transaction');
      const data = await res.json();
      return data.data || data;
    },
    enabled: !!id,
  });
}

// Create transaction
export function useCreateTransaction() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: CreateTransactionInput) => {
      const res = await fetch('/api/transactions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.message || 'Failed to create transaction');
      }
      return res.json();
    },
    onSuccess: (_, variables) => {
      // Invalidate all affected queries
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
      queryClient.invalidateQueries({ queryKey: ['accounts'] });
      queryClient.invalidateQueries({ queryKey: ['accounts', variables.account_id] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['snapshots'] });
    },
  });
}

// Create transfer (special case - creates 2 linked transactions)
export function useCreateTransfer() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: CreateTransferInput) => {
      const res = await fetch('/api/transactions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...data, type: 'Transfer' }),
      });
      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.message || 'Failed to create transfer');
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
      queryClient.invalidateQueries({ queryKey: ['accounts'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['snapshots'] });
    },
  });
}

// Update transaction
export function useUpdateTransaction(id: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: Partial<CreateTransactionInput>) => {
      const res = await fetch(`/api/transactions/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!res.ok) throw new Error('Failed to update transaction');
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
      queryClient.invalidateQueries({ queryKey: ['accounts'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['snapshots'] });
    },
  });
}

// Delete transaction
export function useDeleteTransaction() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: number) => {
      const res = await fetch(`/api/transactions/${id}`, {
        method: 'DELETE',
      });
      if (!res.ok) throw new Error('Failed to delete transaction');
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
      queryClient.invalidateQueries({ queryKey: ['accounts'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['snapshots'] });
    },
  });
}
