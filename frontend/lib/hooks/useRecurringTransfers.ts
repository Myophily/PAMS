import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  CreateRecurringTransferInput,
  UpdateRecurringTransferInput,
  RecurringTransfer
} from '../types';

const API_BASE = '/api';

/**
 * Fetch all recurring transfers, optionally filtered by account ID.
 *
 * @param accountId - Optional account ID to filter transfers
 * @returns Query result with list of recurring transfers
 */
export function useRecurringTransfers(accountId?: number) {
  return useQuery({
    queryKey: accountId ? ['recurring-transfers', accountId] : ['recurring-transfers'],
    queryFn: async () => {
      const url = accountId
        ? `${API_BASE}/recurring-transfers?account_id=${accountId}`
        : `${API_BASE}/recurring-transfers`;
      const response = await fetch(url);
      if (!response.ok) throw new Error('Failed to fetch recurring transfers');
      return response.json() as Promise<RecurringTransfer[]>;
    },
  });
}

/**
 * Fetch a single recurring transfer by ID.
 *
 * @param recurringId - Recurring transfer ID
 * @returns Query result with recurring transfer details
 */
export function useRecurringTransfer(recurringId: number) {
  return useQuery({
    queryKey: ['recurring-transfer', recurringId],
    queryFn: async () => {
      const response = await fetch(`${API_BASE}/recurring-transfers/${recurringId}`);
      if (!response.ok) throw new Error('Failed to fetch recurring transfer');
      return response.json() as Promise<RecurringTransfer>;
    },
    enabled: !!recurringId,
  });
}

/**
 * Create a new recurring transfer.
 * Invalidates recurring-transfers and accounts cache on success.
 */
export function useCreateRecurringTransfer() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: CreateRecurringTransferInput) => {
      const response = await fetch(`${API_BASE}/recurring-transfers`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create recurring transfer');
      }
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recurring-transfers'] });
      queryClient.invalidateQueries({ queryKey: ['accounts'] });
    },
  });
}

/**
 * Update an existing recurring transfer.
 * Invalidates recurring-transfers cache on success.
 */
export function useUpdateRecurringTransfer() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, data }: { id: number; data: UpdateRecurringTransferInput }) => {
      const response = await fetch(`${API_BASE}/recurring-transfers/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to update recurring transfer');
      }
      return response.json();
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['recurring-transfers'] });
      queryClient.invalidateQueries({ queryKey: ['recurring-transfer', variables.id] });
    },
  });
}

/**
 * Delete a recurring transfer (soft delete).
 * Historical transactions created by this recurring transfer are preserved.
 * Invalidates recurring-transfers cache on success.
 */
export function useDeleteRecurringTransfer() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: number) => {
      const response = await fetch(`${API_BASE}/recurring-transfers/${id}`, {
        method: 'DELETE',
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to delete recurring transfer');
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recurring-transfers'] });
    },
  });
}
