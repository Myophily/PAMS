import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { TransactionDetail, CreateTransactionInput, CreateTransferInput } from '../types';
import { extractErrorMessage } from '../utils/error';

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
    if (value !== undefined && value !== '' && value !== null) params.append(key, value.toString());
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

// Pattern ① - Income/Expense transactions
export function useCreateDeposit() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: { account_id: number; amount: number; date: string; description?: string }) => {
      const res = await fetch('/api/transactions/deposit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const error = await res.json();
        const message = extractErrorMessage(error, 'Failed to create deposit');
        throw new Error(message);
      }
      return res.json();
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
      queryClient.invalidateQueries({ queryKey: ['accounts', variables.account_id] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['snapshots'] });
    },
  });
}

export function useCreateWithdrawal() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: { account_id: number; amount: number; date: string; description?: string }) => {
      const res = await fetch('/api/transactions/withdrawal', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const error = await res.json();
        const message = extractErrorMessage(error, 'Failed to create withdrawal');
        throw new Error(message);
      }
      return res.json();
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
      queryClient.invalidateQueries({ queryKey: ['accounts', variables.account_id] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['snapshots'] });
    },
  });
}

export function useCreateDividend() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: { account_id: number; ticker: string; amount: number; date: string; description?: string }) => {
      const res = await fetch('/api/transactions/dividend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const error = await res.json();
        const message = extractErrorMessage(error, 'Failed to create dividend');
        throw new Error(message);
      }
      return res.json();
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
      queryClient.invalidateQueries({ queryKey: ['accounts', variables.account_id] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['snapshots'] });
    },
  });
}

export function useCreateInterest() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: { account_id: number; amount: number; date: string; description?: string }) => {
      const res = await fetch('/api/transactions/interest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const error = await res.json();
        const message = extractErrorMessage(error, 'Failed to create interest');
        throw new Error(message);
      }
      return res.json();
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
      queryClient.invalidateQueries({ queryKey: ['accounts', variables.account_id] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['snapshots'] });
    },
  });
}

// Pattern ② - Transfer (creates 2 linked transactions)
export function useCreateTransfer() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: { from_account_id: number; to_account_id: number; amount: number; date: string; description?: string }) => {
      const res = await fetch('/api/transactions/transfer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const error = await res.json();
        const message = extractErrorMessage(error, 'Failed to create transfer');
        throw new Error(message);
      }
      return res.json();
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
      queryClient.invalidateQueries({ queryKey: ['accounts', variables.from_account_id] });
      queryClient.invalidateQueries({ queryKey: ['accounts', variables.to_account_id] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['snapshots'] });
    },
  });
}

// Pattern ③ - Buy/Sell (converts cash ↔ stock)
export function useCreateBuy() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: { account_id: number; ticker: string; quantity: number; price: number; price_currency?: string; date: string; description?: string }) => {
      const res = await fetch('/api/transactions/buy', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const error = await res.json();
        const message = extractErrorMessage(error, 'Failed to create buy transaction');
        throw new Error(message);
      }
      return res.json();
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
      queryClient.invalidateQueries({ queryKey: ['accounts', variables.account_id] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['snapshots'] });
    },
  });
}

export function useCreateSell() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: { account_id: number; ticker: string; quantity: number; price: number; price_currency?: string; date: string; description?: string }) => {
      const res = await fetch('/api/transactions/sell', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const error = await res.json();
        const message = extractErrorMessage(error, 'Failed to create sell transaction');
        throw new Error(message);
      }
      return res.json();
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
      queryClient.invalidateQueries({ queryKey: ['accounts', variables.account_id] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['snapshots'] });
    },
  });
}

// Pattern ④ - Exchange (converts currencies)
export function useCreateExchange() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: { account_id: number; from_ticker: string; to_ticker: string; from_amount: number; to_amount: number; date: string; description?: string }) => {
      const res = await fetch('/api/transactions/exchange', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const error = await res.json();
        const message = extractErrorMessage(error, 'Failed to create exchange');
        throw new Error(message);
      }
      return res.json();
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
      queryClient.invalidateQueries({ queryKey: ['accounts', variables.account_id] });
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
      if (!res.ok) {
        const error = await res.json();
        const message = extractErrorMessage(error, 'Failed to update transaction');
        throw new Error(message);
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

// Delete transaction
export function useDeleteTransaction() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: number) => {
      const res = await fetch(`/api/transactions/${id}`, {
        method: 'DELETE',
      });
      if (!res.ok) {
        const error = await res.json();
        const message = extractErrorMessage(error, 'Failed to delete transaction');
        throw new Error(message);
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
