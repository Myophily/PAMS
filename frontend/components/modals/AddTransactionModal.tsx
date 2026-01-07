'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { toast } from 'sonner';
import { Modal } from '@/components/ui/Modal';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Button } from '@/components/ui/Button';
import { useAccounts } from '@/lib/hooks/useAccounts';
import {
  useCreateDeposit,
  useCreateWithdrawal,
  useCreateDividend,
  useCreateBuy,
  useCreateSell,
} from '@/lib/hooks/useTransactions';
import {
  createTransactionSchema,
  type CreateTransactionFormData,
} from '@/lib/validation/schemas';
import { getCurrentDateTimeLocal } from '@/lib/utils/datetime';

interface AddTransactionModalProps {
  isOpen: boolean;
  onClose: () => void;
  defaultAccountId?: number;
}

export function AddTransactionModal({
  isOpen,
  onClose,
  defaultAccountId,
}: AddTransactionModalProps) {
  const { data: accountsData } = useAccounts();
  const createDeposit = useCreateDeposit();
  const createWithdrawal = useCreateWithdrawal();
  const createDividend = useCreateDividend();
  const createBuy = useCreateBuy();
  const createSell = useCreateSell();
  const [transactionType, setTransactionType] = useState('Deposit');

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    watch,
  } = useForm<CreateTransactionFormData>({
    resolver: zodResolver(createTransactionSchema),
    defaultValues: {
      account_id: defaultAccountId || 0,
      type: 'Deposit',
      date: getCurrentDateTimeLocal(),
    },
  });

  const onSubmit = async (data: CreateTransactionFormData) => {
    try {
      // Route to the appropriate hook based on transaction type
      switch (data.type) {
        case 'Deposit':
          await createDeposit.mutateAsync({
            account_id: data.account_id,
            amount: data.amount!,
            date: data.date,
            description: data.description,
          });
          break;
        case 'Withdrawal':
          await createWithdrawal.mutateAsync({
            account_id: data.account_id,
            amount: data.amount!,
            date: data.date,
            description: data.description,
          });
          break;
        case 'Dividend':
          await createDividend.mutateAsync({
            account_id: data.account_id,
            ticker: data.ticker!,
            amount: data.amount!,
            date: data.date,
            description: data.description,
          });
          break;
        case 'Buy':
          await createBuy.mutateAsync({
            account_id: data.account_id,
            ticker: data.ticker!,
            quantity: data.quantity!,
            price: data.price!,
            date: data.date,
            description: data.description,
          });
          break;
        case 'Sell':
          await createSell.mutateAsync({
            account_id: data.account_id,
            ticker: data.ticker!,
            quantity: data.quantity!,
            price: data.price!,
            date: data.date,
            description: data.description,
          });
          break;
        default:
          throw new Error('Unknown transaction type');
      }

      toast.success('Transaction created successfully!');
      reset();
      onClose();
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : 'Failed to create transaction'
      );
    }
  };

  const handleClose = () => {
    reset();
    setTransactionType('Deposit');
    onClose();
  };

  const accounts = accountsData?.accounts || [];

  // Transaction type options
  const transactionTypes = [
    { value: 'Deposit', label: 'Deposit' },
    { value: 'Withdrawal', label: 'Withdrawal' },
    { value: 'Buy', label: 'Buy Stock' },
    { value: 'Sell', label: 'Sell Stock' },
    { value: 'Dividend', label: 'Dividend' },
  ];

  // Show different fields based on transaction type
  const showAmountField = ['Deposit', 'Withdrawal', 'Dividend'].includes(transactionType);
  const showStockFields = ['Buy', 'Sell'].includes(transactionType);

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Add Transaction">
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <Select
          label="Account"
          {...register('account_id', { valueAsNumber: true })}
          error={errors.account_id?.message}
        >
          <option value={0}>Select an account</option>
          {accounts.map((account) => (
            <option key={account.id} value={account.id}>
              {account.name} ({account.type})
            </option>
          ))}
        </Select>

        <Select
          label="Transaction Type"
          {...register('type')}
          error={errors.type?.message}
          onChange={(e) => setTransactionType(e.target.value)}
        >
          {transactionTypes.map((type) => (
            <option key={type.value} value={type.value}>
              {type.label}
            </option>
          ))}
        </Select>

        {showAmountField && (
          <Input
            label="Amount"
            type="number"
            step="0.01"
            {...register('amount', { valueAsNumber: true })}
            error={errors.amount?.message}
            placeholder="0.00"
          />
        )}

        {showStockFields && (
          <>
            <Input
              label="Ticker Symbol"
              {...register('ticker')}
              error={errors.ticker?.message}
              placeholder="e.g., AAPL, 005930.KS"
            />

            <Input
              label="Quantity"
              type="number"
              step="1"
              {...register('quantity', { valueAsNumber: true })}
              error={errors.quantity?.message}
              placeholder="Number of shares"
            />

            <Input
              label="Price per Share"
              type="number"
              step="0.01"
              {...register('price', { valueAsNumber: true })}
              error={errors.price?.message}
              placeholder="0.00"
            />
          </>
        )}

        {transactionType === 'Dividend' && (
          <Input
            label="Stock Ticker"
            {...register('ticker')}
            error={errors.ticker?.message}
            placeholder="e.g., AAPL"
          />
        )}

        <Input
          label="Date & Time"
          type="datetime-local"
          {...register('date')}
          error={errors.date?.message}
        />

        <Input
          label="Description (Optional)"
          {...register('description')}
          placeholder="Add notes about this transaction"
        />

        <div className="flex gap-2 justify-end">
          <Button type="button" variant="secondary" onClick={handleClose}>
            Cancel
          </Button>
          <Button
            type="submit"
            loading={
              createDeposit.isPending ||
              createWithdrawal.isPending ||
              createDividend.isPending ||
              createBuy.isPending ||
              createSell.isPending
            }
          >
            Create Transaction
          </Button>
        </div>
      </form>
    </Modal>
  );
}
