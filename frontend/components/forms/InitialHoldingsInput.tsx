'use client';

import { useEffect } from 'react';
import { useFieldArray, Control, Controller, UseFormRegister, FieldErrors, UseFormWatch, UseFormSetValue } from 'react-hook-form';
import { Plus, Trash2, Info } from 'lucide-react';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Button } from '@/components/ui/Button';
import { CURRENCY_TICKERS, isCurrencyTicker, KOREAN_BOND_TICKERS } from '@/lib/utils/currency';
import { CreateAccountFormData } from '@/lib/validation/schemas';

function inferCurrencyFromTicker(ticker: string): 'USD' | 'KRW' | 'JPY' | 'EUR' | 'GBP' | 'HKD' {
  const upper = ticker.toUpperCase();
  if (/^\d{6}$/.test(upper) || upper.endsWith('.KS') || upper.endsWith('.KQ')) {
    return 'KRW';
  }
  if ((KOREAN_BOND_TICKERS as readonly string[]).includes(upper)) {
    return 'KRW';
  }
  if (upper.endsWith('.T')) {
    return 'JPY';
  }
  if (upper.endsWith('.HK')) {
    return 'HKD';
  }
  return 'USD';
}

interface InitialHoldingsInputProps {
  accountType: string;
  control: Control<CreateAccountFormData>;
  register: UseFormRegister<CreateAccountFormData>;
  errors: FieldErrors<CreateAccountFormData>;
  watch: UseFormWatch<CreateAccountFormData>;
  setValue: UseFormSetValue<CreateAccountFormData>;
}

export function InitialHoldingsInput({
  accountType,
  control,
  register,
  errors,
  watch,
  setValue,
}: InitialHoldingsInputProps) {
  const { fields, append, remove } = useFieldArray({
    control,
    name: 'initial_holdings',
  });

  // Auto-clear price field when currency ticker is detected (Securities accounts only)
  useEffect(() => {
    if (accountType !== 'Securities') return;

    fields.forEach((_, index) => {
      const ticker = watch(`initial_holdings.${index}.ticker`);
      const currentPrice = watch(`initial_holdings.${index}.price`);

      // If ticker is a currency AND price has a value, clear it
      if (ticker && isCurrencyTicker(ticker) && currentPrice !== undefined && currentPrice !== 0) {
        setValue(`initial_holdings.${index}.price`, undefined, {
          shouldValidate: true,
          shouldDirty: true,
        });
      }
    });
  }, [
    accountType,
    fields.map((_, i) => watch(`initial_holdings.${i}.ticker`)).join(','),
    fields.length,
    setValue,
    watch,
  ]);

  // Auto-detect price_currency from ticker (Securities accounts only)
  useEffect(() => {
    if (accountType !== 'Securities') return;

    fields.forEach((_, index) => {
      const ticker = watch(`initial_holdings.${index}.ticker`);
      const isCurrency = ticker ? isCurrencyTicker(ticker) : false;

      // Auto-set price_currency for stocks based on ticker
      if (!isCurrency && ticker) {
        const inferredCurrency = inferCurrencyFromTicker(ticker);
        const currentPriceCurrency = watch(`initial_holdings.${index}.price_currency`);

        if (currentPriceCurrency !== inferredCurrency) {
          setValue(`initial_holdings.${index}.price_currency`, inferredCurrency, {
            shouldValidate: true,
            shouldDirty: false,
          });
        }
      } else if (isCurrency) {
        // Clear price_currency for currency tickers (USD, KRW, etc.)
        const currentPriceCurrency = watch(`initial_holdings.${index}.price_currency`);
        if (currentPriceCurrency !== undefined) {
          setValue(`initial_holdings.${index}.price_currency`, undefined, {
            shouldValidate: true,
            shouldDirty: false,
          });
        }
      }
    });
  }, [
    accountType,
    fields.map((_, i) => watch(`initial_holdings.${i}.ticker`)).join(','),
    fields.length,
    setValue,
    watch,
  ]);

  // Render for Deposit/Savings/MoneyMarket accounts (simple KRW balance)
  const renderSimpleKRWBalance = () => {
    return (
      <div>
        <label className="block text-sm font-medium text-gray-900 mb-2">
          Initial Balance (KRW)
        </label>
        <div className="relative">
          <Input
            type="number"
            step="1"
            placeholder="1000000"
            {...register('initial_holdings.0.quantity', { valueAsNumber: true })}
            error={errors.initial_holdings?.[0]?.quantity?.message}
            className="pr-12"
          />
          <span className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 font-medium pointer-events-none">
            ₩
          </span>
        </div>
        <p className="text-xs text-gray-500 mt-1">
          Enter initial balance in Korean Won
        </p>
        {/* Hidden ticker field */}
        <input type="hidden" {...register('initial_holdings.0.ticker')} value="KRW" />
      </div>
    );
  };

  // Render for ForeignCurrency accounts (currency dropdown, no price)
  const renderForeignCurrency = () => {
    const currencyOptions = CURRENCY_TICKERS.filter(c => c !== 'KRW');

    return (
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <label className="text-sm font-medium text-gray-900">
            Initial Foreign Currency Holdings
          </label>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => append({ ticker: 'USD', quantity: 0, price: undefined })}
          >
            <Plus className="w-4 h-4 mr-1" />
            Add Currency
          </Button>
        </div>

        {fields.length === 0 && (
          <div className="text-center py-6 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
            <Info className="w-8 h-8 mx-auto text-gray-400 mb-2" />
            <p className="text-sm text-gray-500">
              No currencies added yet. Click &quot;Add Currency&quot; to start.
            </p>
          </div>
        )}

        {fields.map((field, index) => (
          <div key={field.id} className="flex items-start gap-2 p-3 bg-gray-50 rounded-lg">
            <div className="flex-1 grid grid-cols-2 gap-2">
              <div>
                {index === 0 && (
                  <label className="block text-sm font-medium text-gray-900 mb-1">
                    Currency
                  </label>
                )}
                <select
                  {...register(`initial_holdings.${index}.ticker`)}
                  className={`w-full border rounded px-3 py-2 text-gray-900 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    errors.initial_holdings?.[index]?.ticker ? 'border-red-500' : 'border-gray-300'
                  }`}
                >
                  <option value="">Select currency</option>
                  {currencyOptions.map(currency => (
                    <option key={currency} value={currency}>
                      {currency}
                    </option>
                  ))}
                </select>
                {errors.initial_holdings?.[index]?.ticker && (
                  <p className="text-red-500 text-sm mt-1">
                    {errors.initial_holdings[index]?.ticker?.message}
                  </p>
                )}
              </div>
              <Input
                label={index === 0 ? 'Amount' : undefined}
                type="number"
                step="0.01"
                {...register(`initial_holdings.${index}.quantity`, { valueAsNumber: true })}
                error={errors.initial_holdings?.[index]?.quantity?.message}
                placeholder="5000"
              />
            </div>
            {fields.length > 1 && (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => remove(index)}
                className={index === 0 ? 'mt-6' : ''}
              >
                <Trash2 className="w-4 h-4 text-red-500" />
              </Button>
            )}
          </div>
        ))}

        {errors.initial_holdings?.root?.message && (
          <p className="text-sm text-red-600">
            {errors.initial_holdings.root.message}
          </p>
        )}
      </div>
    );
  };

  // Render for Securities accounts (any ticker, conditional price)
  const renderSecurities = () => {
    return (
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <label className="text-sm font-medium text-gray-900">
            Initial Holdings
          </label>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => append({ ticker: '', quantity: 0, price: undefined, price_currency: undefined })}
          >
            <Plus className="w-4 h-4 mr-1" />
            Add Holding
          </Button>
        </div>

        {fields.length === 0 && (
          <div className="text-center py-6 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
            <Info className="w-8 h-8 mx-auto text-gray-400 mb-2" />
            <p className="text-sm text-gray-500">
              No holdings added yet. You can add cash (KRW, USD) or securities (AAPL, TSLA).
            </p>
          </div>
        )}

        {fields.map((field, index) => {
          const ticker = watch(`initial_holdings.${index}.ticker`);
          const isCurrency = ticker ? isCurrencyTicker(ticker) : false;
          const selectedCurrency = watch(`initial_holdings.${index}.price_currency`) || 'USD';

          return (
            <div key={field.id} className="p-3 bg-gray-50 rounded-lg">
              <div className="flex items-start gap-2">
                <div className={`flex-1 grid ${isCurrency ? 'grid-cols-2' : 'grid-cols-4'} gap-2`}>
                  <Input
                    label={index === 0 ? 'Ticker' : undefined}
                    {...register(`initial_holdings.${index}.ticker`)}
                    error={errors.initial_holdings?.[index]?.ticker?.message}
                    placeholder="AAPL or KRW"
                  />
                  <Input
                    label={index === 0 ? 'Quantity' : undefined}
                    type="number"
                    step="0.00000001"
                    {...register(`initial_holdings.${index}.quantity`, { valueAsNumber: true })}
                    error={errors.initial_holdings?.[index]?.quantity?.message}
                    placeholder="100"
                  />
                  {!isCurrency && (
                    <>
                      <Input
                        label={index === 0 ? 'Price' : undefined}
                        type="number"
                        step="0.0001"
                        {...register(`initial_holdings.${index}.price`, { valueAsNumber: true })}
                        error={errors.initial_holdings?.[index]?.price?.message}
                        placeholder={selectedCurrency === 'KRW' ? '65000' : '150.50'}
                      />
                      <Controller
                        name={`initial_holdings.${index}.price_currency`}
                        control={control}
                        defaultValue="USD"
                        render={({ field }) => (
                          <Select
                            label={index === 0 ? 'Currency' : undefined}
                            {...field}
                          >
                            <option value="USD">USD</option>
                            <option value="KRW">KRW</option>
                          </Select>
                        )}
                      />
                    </>
                  )}
                </div>
                {fields.length > 0 && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => remove(index)}
                    className={index === 0 ? 'mt-6' : ''}
                  >
                    <Trash2 className="w-4 h-4 text-red-500" />
                  </Button>
                )}
              </div>
              {isCurrency && ticker && (
                <p className="text-xs text-blue-600 mt-1">
                  Currency detected - price not required
                </p>
              )}
              {!isCurrency && ticker && (
                <p className="text-xs text-gray-500 mt-1">
                  Price currency: {selectedCurrency === 'KRW' ? '₩ Korean Won' : '$ US Dollar'}
                </p>
              )}
            </div>
          );
        })}

        {errors.initial_holdings?.root?.message && (
          <p className="text-sm text-red-600">
            {errors.initial_holdings.root.message}
          </p>
        )}
      </div>
    );
  };

  // Route to appropriate renderer based on account type
  if (['Deposit', 'Savings', 'MoneyMarket'].includes(accountType)) {
    return renderSimpleKRWBalance();
  } else if (accountType === 'ForeignCurrency') {
    return renderForeignCurrency();
  } else if (accountType === 'Securities') {
    return renderSecurities();
  }

  return null;
}
