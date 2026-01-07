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
import { useExchangeRate } from '@/lib/hooks/useMarketData';
import { useCreateTransaction } from '@/lib/hooks/useTransactions';
import {
  createExchangeSchema,
  type CreateExchangeFormData,
} from '@/lib/validation/schemas';

interface ExchangeModalProps {
  isOpen: boolean;
  onClose: () => void;
  defaultAccountId?: number;
}

export function ExchangeModal({
  isOpen,
  onClose,
  defaultAccountId,
}: ExchangeModalProps) {
  const { data: accountsData } = useAccounts();
  const createTransaction = useCreateTransaction();

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    watch,
    setValue,
  } = useForm<CreateExchangeFormData>({
    resolver: zodResolver(createExchangeSchema),
    defaultValues: {
      account_id: defaultAccountId || 0,
      from_ticker: 'KRW',
      to_ticker: 'USD',
      from_amount: 0,
      to_amount: 0,
      date: new Date().toISOString().split('T')[0],
    },
  });

  const fromTicker = watch('from_ticker');
  const toTicker = watch('to_ticker');
  const fromAmount = watch('from_amount');
  const toAmount = watch('to_amount');
  const date = watch('date');

  // Fetch exchange rate
  const { data: rateData } = useExchangeRate(fromTicker, toTicker, date);

  // Auto-calculate amounts when rate or amount changes
  useEffect(() => {
    if (rateData?.rate && fromAmount > 0) {
      const rateNumber = parseFloat(rateData.rate);
      const calculated = fromAmount / rateNumber;
      setValue('to_amount', parseFloat(calculated.toFixed(2)));
      setValue('exchange_rate', rateNumber);
    }
  }, [rateData, fromAmount, setValue]);

  const onSubmit = async (data: CreateExchangeFormData) => {
    try {
      await createTransaction.mutateAsync({
        account_id: data.account_id,
        type: 'Exchange',
        ticker: `${data.from_ticker}/${data.to_ticker}`,
        amount: data.from_amount,
        price: data.exchange_rate,
        date: data.date,
        description: data.description,
      });
      toast.success('Exchange completed successfully!');
      reset();
      onClose();
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : 'Failed to create exchange'
      );
    }
  };

  const handleClose = () => {
    reset();
    onClose();
  };

  const accounts = accountsData?.accounts || [];
  const foreignAccounts = accounts.filter((acc) => acc.type === 'ForeignCurrency');

  const currencies = [
    { value: 'KRW', label: 'KRW (₩)' },
    { value: 'USD', label: 'USD ($)' },
    { value: 'EUR', label: 'EUR (€)' },
    { value: 'JPY', label: 'JPY (¥)' },
    { value: 'CNY', label: 'CNY (¥)' },
  ];

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Currency Exchange">
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <Select
          label="Account"
          {...register('account_id', { valueAsNumber: true })}
          error={errors.account_id?.message}
        >
          <option value={0}>Select a foreign currency account</option>
          {foreignAccounts.map((account) => (
            <option key={account.id} value={account.id}>
              {account.name} ({account.currency})
            </option>
          ))}
        </Select>

        <div className="grid grid-cols-2 gap-4">
          <Select
            label="From Currency"
            {...register('from_ticker')}
            error={errors.from_ticker?.message}
          >
            {currencies.map((curr) => (
              <option key={curr.value} value={curr.value}>
                {curr.label}
              </option>
            ))}
          </Select>

          <Select
            label="To Currency"
            {...register('to_ticker')}
            error={errors.to_ticker?.message}
          >
            {currencies
              .filter((curr) => curr.value !== fromTicker)
              .map((curr) => (
                <option key={curr.value} value={curr.value}>
                  {curr.label}
                </option>
              ))}
          </Select>
        </div>

        {rateData?.rate && (
          <div className="bg-blue-50 border border-blue-200 rounded p-3 text-sm">
            <span className="font-medium">Exchange Rate:</span> 1 {fromTicker} ={' '}
            {parseFloat(rateData.rate).toFixed(4)} {toTicker}
          </div>
        )}

        <div className="grid grid-cols-2 gap-4">
          <Input
            label={`Amount (${fromTicker})`}
            type="number"
            step="0.01"
            {...register('from_amount', { valueAsNumber: true })}
            error={errors.from_amount?.message}
            placeholder="0.00"
          />

          <Input
            label={`Receive (${toTicker})`}
            type="number"
            step="0.01"
            {...register('to_amount', { valueAsNumber: true })}
            error={errors.to_amount?.message}
            placeholder="0.00"
          />
        </div>

        <Input
          label="Date"
          type="date"
          {...register('date')}
          error={errors.date?.message}
        />

        <Input
          label="Description (Optional)"
          {...register('description')}
          placeholder="Notes about this exchange"
        />

        <div className="flex gap-2 justify-end">
          <Button type="button" variant="secondary" onClick={handleClose}>
            Cancel
          </Button>
          <Button type="submit" loading={createTransaction.isPending}>
            Complete Exchange
          </Button>
        </div>
      </form>
    </Modal>
  );
}
