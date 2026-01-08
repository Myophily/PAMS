'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { toast } from 'sonner';
import { useEffect } from 'react';
import { Modal } from '@/components/ui/Modal';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Button } from '@/components/ui/Button';
import { InitialHoldingsInput } from '@/components/forms/InitialHoldingsInput';
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
    watch,
    control,
    setValue,
  } = useForm<CreateAccountFormData>({
    resolver: zodResolver(createAccountSchema),
    defaultValues: {
      name: '',
      type: 'Deposit',
      initial_balance: undefined,
      initial_balance_date: getCurrentDateTimeLocal(),
      initial_holdings: [],
    },
  });

  const accountType = watch('type');

  // Initialize initial_holdings based on account type
  useEffect(() => {
    if (['Deposit', 'Savings', 'MoneyMarket'].includes(accountType)) {
      // Pre-populate with single KRW holding
      reset({
        ...watch(),
        initial_holdings: [{ ticker: 'KRW', quantity: 0, price: undefined }],
      });
    } else {
      // Clear holdings for other types
      reset({
        ...watch(),
        initial_holdings: [],
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [accountType]);

  const onSubmit = async (data: CreateAccountFormData) => {
    try {
      // Clean up payload
      const payload = {
        ...data,
        // Remove initial_balance (deprecated)
        initial_balance: undefined,
        // Filter out empty holdings
        initial_holdings: data.initial_holdings?.filter(
          h => h.ticker && h.quantity > 0
        ),
      };

      await createAccount.mutateAsync(payload);
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

        <Input
          label="Initial Balance Date & Time"
          type="datetime-local"
          {...register('initial_balance_date')}
          error={errors.initial_balance_date?.message}
        />

        {/* Single reusable component for all account types */}
        <InitialHoldingsInput
          accountType={accountType}
          control={control}
          register={register}
          errors={errors}
          watch={watch}
          setValue={setValue}
        />

        <div className="flex gap-2 justify-end pt-4 border-t">
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
