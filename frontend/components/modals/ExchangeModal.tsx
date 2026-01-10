'use client';

import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { toast } from 'sonner';
import { Modal } from '@/components/ui/Modal';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Button } from '@/components/ui/Button';
import { useAccounts } from '@/lib/hooks/useAccounts';
import { useExchangeRate } from '@/lib/hooks/useMarketData';
import { useCreateExchange } from '@/lib/hooks/useTransactions';
import {
  createExchangeSchema,
  type CreateExchangeFormData,
} from '@/lib/validation/schemas';
import { getCurrentDateTimeLocal } from '@/lib/utils/datetime';
import { extractErrorMessage } from '@/lib/utils/error';

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
  const createExchange = useCreateExchange();

  // Get accounts list early
  const accounts = accountsData?.accounts || [];

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
      date: getCurrentDateTimeLocal(),
      to_account_id: 0,
    },
  });

  const fromTicker = watch('from_ticker');
  const toTicker = watch('to_ticker');
  const fromAmount = watch('from_amount');
  const date = watch('date');
  const accountId = watch('account_id');
  const toAccountId = watch('to_account_id');

  // Determine if cross-account transfer
  const isCrossAccount = toAccountId && toAccountId > 0 && toAccountId !== accountId;

  // Get source and target accounts
  const sourceAccount = accounts.find((acc) => acc.id === accountId);
  const targetAccount = accounts.find((acc) => acc.id === toAccountId);

  // Fetch exchange rate
  const { data: rateData } = useExchangeRate(fromTicker, toTicker, date);

  // Auto-set currency constraints for cross-account transfers
  useEffect(() => {
    if (isCrossAccount && sourceAccount && targetAccount) {
      if (
        sourceAccount.type === 'ForeignCurrency' &&
        targetAccount.type !== 'ForeignCurrency'
      ) {
        // Foreign → Non-Foreign: Must convert to KRW
        setValue('to_ticker', 'KRW');
      } else if (
        sourceAccount.type !== 'ForeignCurrency' &&
        targetAccount.type === 'ForeignCurrency'
      ) {
        // Non-Foreign → Foreign: Must start with KRW
        setValue('from_ticker', 'KRW');
      }
    }
  }, [isCrossAccount, sourceAccount, targetAccount, setValue]);

  // Prevent Foreign → Foreign transfers
  useEffect(() => {
    if (
      sourceAccount?.type === 'ForeignCurrency' &&
      targetAccount?.type === 'ForeignCurrency'
    ) {
      toast.error('Cannot transfer between two Foreign Currency accounts');
      setValue('to_account_id', 0);
    }
  }, [sourceAccount, targetAccount, setValue]);

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
      await createExchange.mutateAsync({
        account_id: data.account_id,
        from_ticker: data.from_ticker,
        to_ticker: data.to_ticker,
        from_amount: data.from_amount,
        to_amount: data.to_amount,
        date: data.date,
        description: data.description,
        to_account_id: data.to_account_id,
      });
      const message = isCrossAccount
        ? 'Exchange and transfer completed successfully!'
        : 'Exchange completed successfully!';
      toast.success(message);
      reset();
      onClose();
    } catch (error) {
      let message: string;
      if (error instanceof Error) {
        message = error.message;
      } else {
        message = extractErrorMessage(error, 'Failed to create exchange');
      }

      // Parse backend validation errors for better UX
      if (message.includes('Cross-account exchange required')) {
        message = 'Please select a different target account. Same-account exchanges are not supported.';
      } else if (message.includes('Foreign Currency accounts not supported')) {
        message = 'Cannot exchange between two Foreign Currency accounts. Please select a Deposit or Securities account as target.';
      } else if (message.includes('Must convert to KRW')) {
        message = 'When transferring from Foreign Currency account, you must convert to KRW first.';
      } else if (message.includes('Must transfer KRW')) {
        message = 'When transferring to Foreign Currency account, you must transfer KRW first.';
      }

      toast.error(message);
    }
  };

  const handleClose = () => {
    reset();
    onClose();
  };

  // Allow both Foreign Currency and Deposit accounts as source
  const eligibleSourceAccounts = accounts.filter((acc) =>
    acc.type === 'ForeignCurrency' || acc.type === 'Deposit'
  );

  // Filter available target accounts (exclude source, disallow Foreign->Foreign)
  const availableTargetAccounts = accounts.filter((acc) => {
    if (acc.id === accountId) return false; // Can't select same account

    // Disallow Foreign → Foreign
    if (sourceAccount?.type === 'ForeignCurrency' && acc.type === 'ForeignCurrency') {
      return false;
    }

    // Disallow Deposit → Deposit (no exchange needed)
    if (sourceAccount?.type === 'Deposit' && acc.type === 'Deposit') {
      return false;
    }

    // For Deposit source, only allow Foreign Currency targets
    if (sourceAccount?.type === 'Deposit' && acc.type !== 'ForeignCurrency') {
      return false;
    }

    return true;
  });

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
          label="Source Account"
          {...register('account_id', { valueAsNumber: true })}
          error={errors.account_id?.message}
        >
          <option value={0}>Select an account</option>
          {eligibleSourceAccounts.map((account) => (
            <option key={account.id} value={account.id}>
              {account.name} ({account.type})
            </option>
          ))}
        </Select>

        <Select
          label="Target Account (Required)"
          {...register('to_account_id', { valueAsNumber: true })}
          error={errors.to_account_id?.message}
        >
          <option value={0}>Select a target account</option>
          {availableTargetAccounts.map((account) => (
            <option key={account.id} value={account.id}>
              {account.name} ({account.type})
            </option>
          ))}
        </Select>

        {toAccountId && toAccountId !== accountId && (
          <div className="bg-blue-50 border border-blue-200 rounded p-3 text-sm text-gray-900">
            <span className="font-medium text-blue-900">
              {sourceAccount?.type === 'ForeignCurrency' && targetAccount?.type !== 'ForeignCurrency'
                ? 'Foreign → Deposit Exchange:'
                : sourceAccount?.type === 'Deposit' && targetAccount?.type === 'ForeignCurrency'
                ? 'Deposit → Foreign Exchange:'
                : 'Cross-Account Exchange:'}
            </span>{' '}
            <span className="text-gray-900">
              {sourceAccount?.type === 'ForeignCurrency' && targetAccount?.type !== 'ForeignCurrency'
                ? 'Foreign currency will be exchanged to KRW, then transferred.'
                : sourceAccount?.type === 'Deposit' && targetAccount?.type === 'ForeignCurrency'
                ? 'KRW will be transferred first, then exchanged to foreign currency.'
                : 'This will create 4 transactions (Exchange + Transfer).'}
            </span>
          </div>
        )}

        <div className="grid grid-cols-2 gap-4">
          <Select
            label="From Currency"
            {...register('from_ticker')}
            error={errors.from_ticker?.message}
            disabled={
              sourceAccount?.type === 'Deposit' && targetAccount?.type === 'ForeignCurrency'
            }
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
            disabled={
              sourceAccount?.type === 'ForeignCurrency' && targetAccount?.type !== 'ForeignCurrency'
            }
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
          <div className="bg-blue-50 border border-blue-200 rounded p-3 text-sm text-gray-900">
            <span className="font-medium text-blue-900">Exchange Rate:</span>{' '}
            <span className="text-gray-900">
              1 {fromTicker} = {parseFloat(rateData.rate).toFixed(4)} {toTicker}
            </span>
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
          type="datetime-local"
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
          <Button type="submit" loading={createExchange.isPending}>
            Complete Exchange
          </Button>
        </div>
      </form>
    </Modal>
  );
}
