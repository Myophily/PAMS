'use client';

import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { toast } from 'sonner';
import { Modal } from '@/components/ui/Modal';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Button } from '@/components/ui/Button';
import { useAccounts } from '@/lib/hooks/useAccounts';
import { useStockPrice } from '@/lib/hooks/useMarketData';
import { useCreateTransaction } from '@/lib/hooks/useTransactions';
import { formatDecimal, parseDecimal } from '@/lib/utils/decimal';
import {
  createBuySellSchema,
  type CreateBuySellFormData,
} from '@/lib/validation/schemas';

interface BuySellModalProps {
  isOpen: boolean;
  onClose: () => void;
  defaultAccountId?: number;
  defaultType?: 'Buy' | 'Sell';
}

export function BuySellModal({
  isOpen,
  onClose,
  defaultAccountId,
  defaultType = 'Buy',
}: BuySellModalProps) {
  const { data: accountsData } = useAccounts();
  const createTransaction = useCreateTransaction();

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    watch,
    setValue,
  } = useForm<CreateBuySellFormData>({
    resolver: zodResolver(createBuySellSchema),
    defaultValues: {
      account_id: defaultAccountId || 0,
      type: defaultType,
      ticker: '',
      quantity: 0,
      price: 0,
      date: new Date().toISOString().split('T')[0],
    },
  });

  const accountId = watch('account_id');
  const type = watch('type');
  const ticker = watch('ticker');
  const quantity = watch('quantity');
  const price = watch('price');
  const date = watch('date');

  const accounts = accountsData?.accounts || [];
  const brokerageAccounts = accounts.filter((acc) => acc.type === 'Securities');
  const selectedAccount = accounts.find((acc) => acc.id === accountId);

  // Fetch stock price suggestion
  const { data: priceData } = useStockPrice(ticker, date);

  // Auto-fill price when stock price is fetched
  useEffect(() => {
    if (priceData?.closing_price && price === 0) {
      setValue('price', priceData.closing_price);
    }
  }, [priceData, price, setValue]);

  const totalValue = quantity * price;

  const onSubmit = async (data: CreateBuySellFormData) => {
    try {
      // Validate Buy: sufficient cash
      if (data.type === 'Buy' && selectedAccount) {
        const cost = data.quantity * data.price;
        if (cost > parseDecimal(selectedAccount.balance)) {
          toast.error('Insufficient cash balance');
          return;
        }
      }

      // TODO: For Sell, validate holding quantity (need to fetch holdings)

      await createTransaction.mutateAsync(data);
      toast.success(
        `${data.type} order for ${data.ticker} completed successfully!`
      );
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
    onClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title={`${type} Stocks`}
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div className="flex gap-4 mb-4">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              value="Buy"
              {...register('type')}
              className="w-4 h-4"
            />
            <span className="font-medium">Buy</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              value="Sell"
              {...register('type')}
              className="w-4 h-4"
            />
            <span className="font-medium">Sell</span>
          </label>
        </div>

        <Select
          label="Brokerage Account"
          {...register('account_id', { valueAsNumber: true })}
          error={errors.account_id?.message}
        >
          <option value={0}>Select a brokerage account</option>
          {brokerageAccounts.map((account) => (
            <option key={account.id} value={account.id}>
              {account.name} (Cash: {formatDecimal(account.balance)}{' '}
              {account.currency})
            </option>
          ))}
        </Select>

        <Input
          label="Ticker Symbol"
          {...register('ticker')}
          error={errors.ticker?.message}
          placeholder="e.g., AAPL, 005930.KS"
        />

        {priceData && (
          <div className="bg-blue-50 border border-blue-200 rounded p-3 text-sm">
            <span className="font-medium">Current Price:</span>{' '}
            {priceData.closing_price.toLocaleString()} {priceData.currency}
            {priceData.cached && ' (cached)'}
          </div>
        )}

        <div className="grid grid-cols-2 gap-4">
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
        </div>

        {totalValue > 0 && (
          <div className="bg-gray-50 border border-gray-200 rounded p-3">
            <span className="font-medium">Total Value:</span>{' '}
            <span className="text-lg font-bold">
              {totalValue.toLocaleString()} {selectedAccount?.currency || ''}
            </span>
          </div>
        )}

        <Input
          label="Date"
          type="date"
          {...register('date')}
          error={errors.date?.message}
        />

        <Input
          label="Description (Optional)"
          {...register('description')}
          placeholder="Notes about this trade"
        />

        <div className="flex gap-2 justify-end">
          <Button type="button" variant="secondary" onClick={handleClose}>
            Cancel
          </Button>
          <Button
            type="submit"
            loading={createTransaction.isPending}
            variant={type === 'Buy' ? 'primary' : 'danger'}
          >
            {type} Stocks
          </Button>
        </div>
      </form>
    </Modal>
  );
}
