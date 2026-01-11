'use client';

import { useState } from 'react';
import {
  useRecurringTransfers,
  useDeleteRecurringTransfer,
  useUpdateRecurringTransfer,
} from '@/lib/hooks/useRecurringTransfers';
import { Button } from '@/components/ui/Button';
import { RecurringTransferModal } from '@/components/modals/RecurringTransferModal';
import { formatDecimal } from '@/lib/utils/decimal';
import { toast } from 'sonner';

export default function RecurringTransfersPage() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const { data: transfers, isLoading } = useRecurringTransfers();
  const deleteTransfer = useDeleteRecurringTransfer();
  const updateTransfer = useUpdateRecurringTransfer();

  const handleToggleActive = async (id: number, currentStatus: boolean) => {
    try {
      await updateTransfer.mutateAsync({
        id,
        data: { is_active: !currentStatus },
      });
      toast.success(currentStatus ? 'Recurring transfer paused' : 'Recurring transfer resumed');
    } catch (error) {
      toast.error('Failed to update transfer status');
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this recurring transfer? This will not affect historical transactions.')) {
      return;
    }

    try {
      await deleteTransfer.mutateAsync(id);
      toast.success('Recurring transfer deleted');
    } catch (error) {
      toast.error('Failed to delete recurring transfer');
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-gray-600">Loading recurring transfers...</div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Recurring Transfers</h1>
          <p className="text-gray-600 mt-1">Manage automatic monthly transfers between accounts</p>
        </div>
        <Button onClick={() => setIsModalOpen(true)}>
          Create New
        </Button>
      </div>

      {!transfers || transfers.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-8 text-center">
          <div className="text-gray-400 mb-4">
            <svg
              className="mx-auto h-12 w-12"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"
              />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No recurring transfers</h3>
          <p className="text-gray-600 mb-4">
            Create your first recurring transfer to automatically move money between accounts each month.
          </p>
          <Button onClick={() => setIsModalOpen(true)}>
            Create Recurring Transfer
          </Button>
        </div>
      ) : (
        <div className="space-y-4">
          {transfers.map((transfer) => (
            <div
              key={transfer.id}
              className="bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow"
            >
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-3">
                    <h3 className="font-semibold text-lg text-gray-900">
                      {transfer.from_account_name} → {transfer.to_account_name}
                    </h3>
                    <span
                      className={`px-2 py-1 text-xs font-medium rounded-full ${
                        transfer.is_active
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {transfer.is_active ? 'Active' : 'Paused'}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-4 text-sm text-gray-600">
                    <div>
                      <span className="font-medium text-gray-700">Amount:</span>{' '}
                      <span className="text-gray-900 font-semibold">
                        {formatDecimal(transfer.amount)} KRW
                      </span>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">Day of Month:</span>{' '}
                      <span className="text-gray-900">{transfer.day_of_month}</span>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">Last Executed:</span>{' '}
                      <span className="text-gray-900">{formatDate(transfer.last_executed_date)}</span>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">Next Execution:</span>{' '}
                      <span className="text-gray-900">{formatDate(transfer.next_execution_date)}</span>
                    </div>
                  </div>

                  {transfer.description && (
                    <p className="mt-3 text-sm text-gray-600">
                      <span className="font-medium text-gray-700">Note:</span> {transfer.description}
                    </p>
                  )}
                </div>

                <div className="flex flex-col gap-2 ml-6">
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => handleToggleActive(transfer.id, transfer.is_active)}
                    disabled={updateTransfer.isPending}
                  >
                    {transfer.is_active ? 'Pause' : 'Resume'}
                  </Button>
                  <Button
                    size="sm"
                    variant="danger"
                    onClick={() => handleDelete(transfer.id)}
                    disabled={deleteTransfer.isPending}
                  >
                    Delete
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <RecurringTransferModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />
    </div>
  );
}
