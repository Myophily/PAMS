import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { Account, AccountWithBalance, AccountDetails, CreateAccountInput } from '../types';
import { extractErrorMessage } from '../utils/error';

// List all accounts
export function useAccounts() {
  return useQuery<{ accounts: AccountWithBalance[] }>({
    queryKey: ['accounts'],
    queryFn: async () => {
      const res = await fetch('/api/accounts');
      if (!res.ok) throw new Error('Failed to fetch accounts');
      const data = await res.json();
      return { accounts: data };
    },
  });
}

// Get account details
export function useAccountDetails(id: number) {
  return useQuery<AccountDetails>({
    queryKey: ['accounts', id],
    queryFn: async () => {
      const res = await fetch(`/api/accounts/${id}`);
      if (!res.ok) throw new Error('Failed to fetch account details');
      const data = await res.json();
      return data.data || data;
    },
    enabled: !!id,
  });
}

// Create account
export function useCreateAccount() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: CreateAccountInput) => {
      const res = await fetch('/api/accounts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const error = await res.json();
        const message = extractErrorMessage(error, 'Failed to create account');
        throw new Error(message);
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });
}

// Update account
export function useUpdateAccount(id: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: Partial<Account>) => {
      const res = await fetch(`/api/accounts/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const error = await res.json();
        const message = extractErrorMessage(error, 'Failed to update account');
        throw new Error(message);
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] });
      queryClient.invalidateQueries({ queryKey: ['accounts', id] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });
}

// Delete account
export function useDeleteAccount() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: number) => {
      const res = await fetch(`/api/accounts/${id}`, {
        method: 'DELETE',
      });
      if (!res.ok) {
        const error = await res.json();
        const message = extractErrorMessage(error, 'Failed to delete account');
        throw new Error(message);
      }
      // Backend now returns 200 with stats, not 204
      return res.json();
    },
    onSuccess: (data) => {
      // Invalidate all potentially affected queries
      queryClient.invalidateQueries({ queryKey: ['accounts'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
      queryClient.invalidateQueries({ queryKey: ['snapshots'] });

      // Log deletion stats (optional)
      if (data.stats) {
        console.log('Account deleted:', data.stats);
      }
    },
  });
}
