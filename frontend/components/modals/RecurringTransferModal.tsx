'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { toast } from 'sonner';
import { Modal } from '@/components/ui/Modal';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Button } from '@/components/ui/Button';
import { useAccounts } from '@/lib/hooks/useAccounts';
import { useCreateRecurringTransfer } from '@/lib/hooks/useRecurringTransfers';
import { formatDecimal } from '@/lib/utils/decimal';
import {
  createRecurringTransferSchema,
  type CreateRecurringTransferFormData,
} from '@/lib/validation/schemas';
import { extractErrorMessage } from '@/lib/utils/error';

interface RecurringTransferModalProps {
  isOpen: boolean;
  onClose: () => void;
  defaultFromAccountId?: number;
}

export function RecurringTransferModal({
  isOpen,
  onClose,
  defaultFromAccountId,
}: RecurringTransferModalProps) {
  const { data: accountsData } = useAccounts();
  const createRecurring = useCreateRecurringTransfer();

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    watch,
  } = useForm<CreateRecurringTransferFormData>({
    resolver: zodResolver(createRecurringTransferSchema),
    defaultValues: {
      from_account_id: defaultFromAccountId || 0,
      to_account_id: 0,
      amount: 0,
      day_of_month: 1,
      description: '',
    },
  });

  const fromAccountId = watch('from_account_id');
  const accounts = accountsData?.accounts || [];

  // Get selected from account for balance display
  const fromAccount = accounts.find((acc) => acc.id === fromAccountId);

  const onSubmit = async (data: CreateRecurringTransferFormData) => {
    try {
      await createRecurring.mutateAsync(data);
      toast.success('Recurring transfer created successfully!');
      reset();
      onClose();
    } catch (error: any) {
      const errorMessage = extractErrorMessage(error);
      toast.error(errorMessage);
    }
  };

  const handleClose = () => {
    reset();
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Create Recurring Transfer">
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <Select
          label="From Account"
          {...register('from_account_id', { valueAsNumber: true })}
          error={errors.from_account_id?.message}
        >
          <option value={0}>Select account...</option>
          {accounts.map((acc) => (
            <option key={acc.id} value={acc.id}>
              {acc.name} ({formatDecimal(acc.balance)} KRW)
            </option>
          ))}
        </Select>

        <Select
          label="To Account"
          {...register('to_account_id', { valueAsNumber: true })}
          error={errors.to_account_id?.message}
        >
          <option value={0}>Select account...</option>
          {accounts
            .filter((acc) => acc.id !== fromAccountId)
            .map((acc) => (
              <option key={acc.id} value={acc.id}>
                {acc.name}
              </option>
            ))}
        </Select>

        <Input
          label="Amount (KRW)"
          type="number"
          step="0.01"
          {...register('amount', { valueAsNumber: true })}
          error={errors.amount?.message}
          helperText={
            fromAccount
              ? `Available balance: ${formatDecimal(fromAccount.balance)} KRW`
              : undefined
          }
        />

        <Input
          label="Day of Month (1-31)"
          type="number"
          min="1"
          max="31"
          {...register('day_of_month', { valueAsNumber: true })}
          error={errors.day_of_month?.message}
          helperText="For months with fewer days, transfer will occur on the last day of the month"
        />

        <Input
          label="Description (Optional)"
          {...register('description')}
          error={errors.description?.message}
          placeholder="e.g., Monthly savings transfer"
        />

        <div className="flex gap-2 justify-end pt-4">
          <Button type="button" variant="secondary" onClick={handleClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={createRecurring.isPending}>
            {createRecurring.isPending ? 'Creating...' : 'Create Recurring Transfer'}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
