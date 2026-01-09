'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { toast } from 'sonner';
import { Modal } from '@/components/ui/Modal';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Button } from '@/components/ui/Button';
import { useAccounts } from '@/lib/hooks/useAccounts';
import { useCreateTransfer } from '@/lib/hooks/useTransactions';
import { formatDecimal, parseDecimal } from '@/lib/utils/decimal';
import {
  createTransferSchema,
  type CreateTransferFormData,
} from '@/lib/validation/schemas';
import { getCurrentDateTimeLocal } from '@/lib/utils/datetime';
import { extractErrorMessage } from '@/lib/utils/error';

interface TransferModalProps {
  isOpen: boolean;
  onClose: () => void;
  defaultFromAccountId?: number;
}

export function TransferModal({
  isOpen,
  onClose,
  defaultFromAccountId,
}: TransferModalProps) {
  const { data: accountsData } = useAccounts();
  const createTransfer = useCreateTransfer();

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    watch,
  } = useForm<CreateTransferFormData>({
    resolver: zodResolver(createTransferSchema),
    defaultValues: {
      from_account_id: defaultFromAccountId || 0,
      to_account_id: 0,
      amount: 0,
      date: getCurrentDateTimeLocal(),
    },
  });

  const fromAccountId = watch('from_account_id');
  const accounts = accountsData?.accounts || [];

  // Get selected from account for balance display
  const fromAccount = accounts.find((acc) => acc.id === fromAccountId);

  const onSubmit = async (data: CreateTransferFormData) => {
    try {
      // Validate sufficient balance
      if (fromAccount && data.amount > parseDecimal(fromAccount.balance)) {
        toast.error('Insufficient balance in source account');
        return;
      }

      await createTransfer.mutateAsync(data);
      toast.success('Transfer completed successfully!');
      reset();
      onClose();
    } catch (error) {
      const message = error instanceof Error
        ? error.message
        : extractErrorMessage(error, 'Failed to create transfer');
      toast.error(message);
    }
  };

  const handleClose = () => {
    reset();
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Transfer Funds">
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <Select
          label="From Account"
          {...register('from_account_id', { valueAsNumber: true })}
          error={errors.from_account_id?.message}
        >
          <option value={0}>Select source account</option>
          {accounts.map((account) => (
            <option key={account.id} value={account.id}>
              {account.name} ({formatDecimal(account.balance)} {['Securities', 'ForeignCurrency'].includes(account.type) ? 'USD' : 'KRW'})
            </option>
          ))}
        </Select>

        {fromAccount && (
          <div className="bg-blue-50 border border-blue-200 rounded p-3 text-sm text-gray-900">
            <span className="font-medium text-blue-900">Available Balance:</span>{' '}
            <span className="text-gray-900">
              {formatDecimal(fromAccount.balance)} {['Securities', 'ForeignCurrency'].includes(fromAccount.type) ? 'USD' : 'KRW'}
            </span>
          </div>
        )}

        <Select
          label="To Account"
          {...register('to_account_id', { valueAsNumber: true })}
          error={errors.to_account_id?.message}
        >
          <option value={0}>Select destination account</option>
          {accounts
            .filter((account) => account.id !== fromAccountId)
            .map((account) => (
              <option key={account.id} value={account.id}>
                {account.name} ({account.type})
              </option>
            ))}
        </Select>

        <Input
          label="Amount"
          type="number"
          step="0.01"
          {...register('amount', { valueAsNumber: true })}
          error={errors.amount?.message}
          placeholder="0.00"
        />

        <Input
          label="Date"
          type="datetime-local"
          {...register('date')}
          error={errors.date?.message}
        />

        <Input
          label="Description (Optional)"
          {...register('description')}
          placeholder="Notes about this transfer"
        />

        <div className="flex gap-2 justify-end">
          <Button type="button" variant="secondary" onClick={handleClose}>
            Cancel
          </Button>
          <Button type="submit" loading={createTransfer.isPending}>
            Transfer Funds
          </Button>
        </div>
      </form>
    </Modal>
  );
}
