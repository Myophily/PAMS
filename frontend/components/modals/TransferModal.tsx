'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { toast } from 'sonner';
import { Modal } from '@/components/ui/Modal';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Button } from '@/components/ui/Button';
import { useAccounts } from '@/lib/hooks/useAccounts';
import {
  useCreateTransfer,
  useCreateDeposit,
  useCreateWithdrawal,
} from '@/lib/hooks/useTransactions';
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
  const createDeposit = useCreateDeposit();
  const createWithdrawal = useCreateWithdrawal();

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
  const toAccountId = watch('to_account_id');
  const accounts = accountsData?.accounts || [];

  // Get selected from account for balance display
  const fromAccount = accounts.find((acc) => acc.id === fromAccountId);

  const onSubmit = async (data: CreateTransferFormData) => {
    try {
      const isFromExternal = data.from_account_id === -1;
      const isToExternal = data.to_account_id === -1;

      if (isFromExternal && !isToExternal) {
        // External → Internal = Deposit
        await createDeposit.mutateAsync({
          account_id: data.to_account_id,
          amount: data.amount,
          date: data.date,
          description: data.description,
        });
        toast.success('Deposit completed successfully!');
      } else if (!isFromExternal && isToExternal) {
        // Internal → External = Withdrawal
        // Validate sufficient balance
        if (fromAccount && data.amount > parseDecimal(fromAccount.balance)) {
          toast.error('Insufficient balance in source account');
          return;
        }
        await createWithdrawal.mutateAsync({
          account_id: data.from_account_id,
          amount: data.amount,
          date: data.date,
          description: data.description,
        });
        toast.success('Withdrawal completed successfully!');
      } else {
        // Internal → Internal = Transfer (existing logic)
        if (fromAccount && data.amount > parseDecimal(fromAccount.balance)) {
          toast.error('Insufficient balance in source account');
          return;
        }
        await createTransfer.mutateAsync(data);
        toast.success('Transfer completed successfully!');
      }

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
          <option value={-1}>External (Outside PAMS)</option>
          <option disabled>──────────────</option>
          {accounts.map((account) => (
            <option key={account.id} value={account.id}>
              {account.name} ({formatDecimal(account.balance)} {['Securities', 'ForeignCurrency'].includes(account.type) ? 'USD' : 'KRW'})
            </option>
          ))}
        </Select>

        {fromAccount && fromAccountId > 0 && (
          <div className="bg-blue-50 border border-blue-200 rounded p-3 text-sm text-gray-900">
            <span className="font-medium text-blue-900">Available Balance:</span>{' '}
            <span className="text-gray-900">
              {formatDecimal(fromAccount.balance)} KRW
            </span>
          </div>
        )}

        {/* Context-aware helper text */}
        {(fromAccountId === -1 || toAccountId === -1) && (
          <div className="bg-amber-50 border border-amber-200 rounded p-3 text-sm text-gray-700">
            {fromAccountId === -1 && toAccountId > 0 && (
              <span><strong>Deposit:</strong> Adding money from external source (total assets increase)</span>
            )}
            {fromAccountId > 0 && toAccountId === -1 && (
              <span><strong>Withdrawal:</strong> Sending money to external account (total assets decrease)</span>
            )}
          </div>
        )}

        <Select
          label="To Account"
          {...register('to_account_id', { valueAsNumber: true })}
          error={errors.to_account_id?.message}
        >
          <option value={0}>Select destination account</option>
          <option value={-1}>External (Outside PAMS)</option>
          <option disabled>──────────────</option>
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
          <Button
            type="submit"
            loading={createTransfer.isPending || createDeposit.isPending || createWithdrawal.isPending}
          >
            Transfer Funds
          </Button>
        </div>
      </form>
    </Modal>
  );
}
