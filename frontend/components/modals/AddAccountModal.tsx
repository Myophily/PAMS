'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { toast } from 'sonner';
import { Modal } from '@/components/ui/Modal';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Button } from '@/components/ui/Button';
import { useCreateAccount } from '@/lib/hooks/useAccounts';
import {
  createAccountSchema,
  type CreateAccountFormData,
} from '@/lib/validation/schemas';
import { getCurrentDateTimeLocal } from '@/lib/utils/datetime';

interface AddAccountModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function AddAccountModal({ isOpen, onClose }: AddAccountModalProps) {
  const createAccount = useCreateAccount();

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<CreateAccountFormData>({
    resolver: zodResolver(createAccountSchema),
    defaultValues: {
      name: '',
      type: 'Deposit',
      currency: 'KRW',
      initial_balance: 0,
      initial_balance_date: getCurrentDateTimeLocal(),
    },
  });

  const onSubmit = async (data: CreateAccountFormData) => {
    try {
      await createAccount.mutateAsync(data);
      toast.success('Account created successfully!');
      reset();
      onClose();
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : 'Failed to create account'
      );
    }
  };

  const handleClose = () => {
    reset();
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Add New Account">
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <Input
          label="Account Name"
          {...register('name')}
          error={errors.name?.message}
          placeholder="e.g., Toss Checking"
        />

        <Select
          label="Account Type"
          {...register('type')}
          error={errors.type?.message}
        >
          <option value="Deposit">Deposit Account (입출금)</option>
          <option value="Savings">Savings Account (예적금)</option>
          <option value="Securities">Securities Account (증권)</option>
          <option value="ForeignCurrency">Foreign Currency (외화)</option>
          <option value="MoneyMarket">Money Market Fund (MMF)</option>
        </Select>

        <Select
          label="Currency"
          {...register('currency')}
          error={errors.currency?.message}
        >
          <option value="KRW">KRW (₩)</option>
          <option value="USD">USD ($)</option>
          <option value="EUR">EUR (€)</option>
          <option value="JPY">JPY (¥)</option>
        </Select>

        <Input
          label="Initial Balance"
          type="number"
          step="0.01"
          {...register('initial_balance', { valueAsNumber: true })}
          error={errors.initial_balance?.message}
        />

        <Input
          label="Initial Balance Date & Time"
          type="datetime-local"
          {...register('initial_balance_date')}
          error={errors.initial_balance_date?.message}
        />

        <div className="flex gap-2 justify-end">
          <Button type="button" variant="secondary" onClick={handleClose}>
            Cancel
          </Button>
          <Button type="submit" loading={createAccount.isPending}>
            Create Account
          </Button>
        </div>
      </form>
    </Modal>
  );
}
