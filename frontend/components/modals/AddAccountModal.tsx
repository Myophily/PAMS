'use client';

import { useForm, useFieldArray } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { toast } from 'sonner';
import { useState, useEffect } from 'react';
import { Plus, Trash2 } from 'lucide-react';
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
  const [useMultipleHoldings, setUseMultipleHoldings] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    watch,
    control,
  } = useForm<CreateAccountFormData>({
    resolver: zodResolver(createAccountSchema),
    defaultValues: {
      name: '',
      type: 'Deposit',
      initial_balance: 0,
      initial_balance_date: getCurrentDateTimeLocal(),
      initial_holdings: [],
    },
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: 'initial_holdings',
  });

  const accountType = watch('type');
  const isSecuritiesAccount = accountType === 'Securities';

  // Reset holdings mode when switching away from Securities
  useEffect(() => {
    if (accountType !== 'Securities') {
      setUseMultipleHoldings(false);
    }
  }, [accountType]);

  const onSubmit = async (data: CreateAccountFormData) => {
    try {
      // Clean up payload based on mode
      const payload = {
        ...data,
        initial_balance: useMultipleHoldings ? undefined : data.initial_balance,
        initial_holdings: useMultipleHoldings ? data.initial_holdings : undefined,
      };

      await createAccount.mutateAsync(payload);
      toast.success('Account created successfully!');
      reset();
      setUseMultipleHoldings(false);
      onClose();
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : 'Failed to create account'
      );
    }
  };

  const handleClose = () => {
    reset();
    setUseMultipleHoldings(false);
    onClose();
  };

  const handleAddHolding = () => {
    append({ ticker: '', quantity: 0, price: undefined });
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

        {/* Conditional: Securities account with mode toggle */}
        {isSecuritiesAccount && (
          <div className="border-t pt-4">
            <div className="flex items-center justify-between mb-3">
              <label className="text-sm font-medium text-gray-700">
                Initial Holdings
              </label>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => setUseMultipleHoldings(!useMultipleHoldings)}
              >
                {useMultipleHoldings ? 'Use Simple Balance' : 'Add Multiple Holdings'}
              </Button>
            </div>

            {!useMultipleHoldings ? (
              <Input
                label="Cash Balance"
                type="number"
                step="0.01"
                {...register('initial_balance', { valueAsNumber: true })}
                error={errors.initial_balance?.message}
              />
            ) : (
              <div className="space-y-3">
                {fields.length === 0 && (
                  <p className="text-sm text-gray-500 text-center py-4">
                    No holdings added yet. Click "Add Holding" to start.
                  </p>
                )}

                {fields.map((field, index) => (
                  <div key={field.id} className="border rounded-lg p-3 bg-gray-50">
                    <div className="flex items-start gap-2">
                      <div className="flex-1 grid grid-cols-3 gap-2">
                        <Input
                          label={index === 0 ? 'Ticker' : ''}
                          {...register(`initial_holdings.${index}.ticker`)}
                          error={errors.initial_holdings?.[index]?.ticker?.message}
                          placeholder="AAPL or CASH"
                        />
                        <Input
                          label={index === 0 ? 'Quantity' : ''}
                          type="number"
                          step="0.00000001"
                          {...register(`initial_holdings.${index}.quantity`, {
                            valueAsNumber: true,
                          })}
                          error={errors.initial_holdings?.[index]?.quantity?.message}
                          placeholder="100"
                        />
                        <Input
                          label={index === 0 ? 'Price' : ''}
                          type="number"
                          step="0.0001"
                          {...register(`initial_holdings.${index}.price`, {
                            valueAsNumber: true,
                          })}
                          error={errors.initial_holdings?.[index]?.price?.message}
                          placeholder="150.50"
                          disabled={watch(`initial_holdings.${index}.ticker`) === 'CASH'}
                        />
                      </div>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => remove(index)}
                        className="mt-6"
                      >
                        <Trash2 className="w-4 h-4 text-red-500" />
                      </Button>
                    </div>
                  </div>
                ))}

                {errors.initial_holdings?.root?.message && (
                  <p className="text-sm text-red-600">
                    {errors.initial_holdings.root.message}
                  </p>
                )}

                <Button
                  type="button"
                  variant="secondary"
                  onClick={handleAddHolding}
                  className="w-full"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Add Holding
                </Button>
              </div>
            )}
          </div>
        )}

        {/* Non-Securities accounts: simple balance */}
        {!isSecuritiesAccount && (
          <Input
            label="Initial Balance"
            type="number"
            step="0.01"
            {...register('initial_balance', { valueAsNumber: true })}
            error={errors.initial_balance?.message}
          />
        )}

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
