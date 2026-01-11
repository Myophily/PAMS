import { z } from 'zod';
import { isCurrencyTicker, validateTickerForAccountType, getTickerConstraints } from '@/lib/utils/currency';

// Initial holding item schema
const initialHoldingItemSchema = z.object({
  ticker: z.string()
    .min(1, 'Ticker is required')
    .transform(val => val.toUpperCase()),
  quantity: z.number()
    .positive('Quantity must be greater than 0'),
  price: z.number()
    .positive('Price must be greater than 0')
    .optional(),
  price_currency: z.enum(['KRW', 'USD', 'JPY', 'EUR', 'GBP', 'HKD']).optional()
}).refine(
  (data) => {
    // If price is provided, price_currency must also be provided
    if (data.price !== undefined && data.price !== null) {
      return data.price_currency !== undefined;
    }
    return true;
  },
  {
    message: 'price_currency is required when price is provided',
    path: ['price_currency'],
  }
);

// Account creation schema
export const createAccountSchema = z.object({
  name: z.string().min(1, 'Account name is required'),
  type: z.enum(['Deposit', 'Securities', 'ForeignCurrency', 'MoneyMarket', 'Savings']),
  initial_balance: z.number().min(0, 'Balance cannot be negative').optional(),
  initial_balance_date: z.string().regex(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/, 'Invalid datetime format'),
  initial_holdings: z.array(initialHoldingItemSchema).optional(),
})
.refine(data => {
  // Cannot use both initial_balance and initial_holdings
  if (data.initial_holdings?.length && data.initial_balance && data.initial_balance > 0) {
    return false;
  }
  return true;
}, {
  message: 'Cannot use both initial_balance and initial_holdings',
  path: ['initial_holdings']
})
.refine(data => {
  // Validate tickers for account type
  if (data.initial_holdings) {
    for (const holding of data.initial_holdings) {
      const validation = validateTickerForAccountType(holding.ticker, data.type);
      if (!validation.valid) {
        return false;
      }
    }
  }
  return true;
}, {
  message: 'Invalid ticker for account type',
  path: ['initial_holdings']
})
.refine(data => {
  // Price requirement based on ticker type
  if (data.initial_holdings) {
    const constraints = getTickerConstraints(data.type);
    for (const holding of data.initial_holdings) {
      const needsPrice = constraints.requirePrice(holding.ticker);
      if (needsPrice && !holding.price) {
        return false;
      }
      if (!needsPrice && holding.price) {
        return false;
      }
    }
  }
  return true;
}, {
  message: 'Price mismatch for ticker type',
  path: ['initial_holdings']
})
.refine(data => {
  // No duplicate tickers
  if (data.initial_holdings) {
    const tickers = data.initial_holdings.map(h => h.ticker);
    return tickers.length === new Set(tickers).size;
  }
  return true;
}, {
  message: 'Duplicate tickers not allowed',
  path: ['initial_holdings']
});

export type CreateAccountFormData = z.infer<typeof createAccountSchema>;

// Transaction creation schema
export const createTransactionSchema = z.object({
  account_id: z.number().positive('Please select an account'),
  type: z.string().min(1, 'Transaction type is required'),
  amount: z.number().optional(),
  ticker: z.string().optional(),
  quantity: z.number().positive().optional(),
  price: z.number().positive().optional(),
  date: z.string().regex(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/, 'Invalid datetime format'),
  description: z.string().optional(),
});

export type CreateTransactionFormData = z.infer<typeof createTransactionSchema>;

// Transfer schema (supports -1 for External accounts)
export const createTransferSchema = z.object({
  from_account_id: z.number().int(),
  to_account_id: z.number().int(),
  amount: z.number().positive('Amount must be greater than 0'),
  date: z.string().regex(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/, 'Invalid datetime format'),
  description: z.string().optional(),
})
.refine(data => {
  // Prevent External → External
  if (data.from_account_id === -1 && data.to_account_id === -1) {
    return false;
  }
  return true;
}, {
  message: 'Cannot transfer from External to External',
  path: ['to_account_id'],
})
.refine(data => {
  // When both are internal accounts (positive), they must be different
  if (data.from_account_id > 0 && data.to_account_id > 0) {
    return data.from_account_id !== data.to_account_id;
  }
  return true;
}, {
  message: 'Source and destination accounts must be different',
  path: ['to_account_id'],
})
.refine(data => {
  // At least one must be a valid internal account
  return data.from_account_id > 0 || data.to_account_id > 0;
}, {
  message: 'At least one account must be selected',
  path: ['to_account_id'],
});

export type CreateTransferFormData = z.infer<typeof createTransferSchema>;

// Exchange schema (cross-account only)
export const createExchangeSchema = z.object({
  account_id: z.number().positive('Please select an account'),
  from_ticker: z.string().min(1, 'From currency is required'),
  to_ticker: z.string().min(1, 'To currency is required'),
  from_amount: z.number().positive('Amount must be greater than 0'),
  to_amount: z.number().positive('Amount must be greater than 0'),
  exchange_rate: z.number().positive().optional(),
  date: z.string().regex(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/, 'Invalid datetime format'),
  description: z.string().optional(),
  to_account_id: z.number().positive('Please select a target account'),  // Required for cross-account exchange
}).refine(data => data.from_ticker !== data.to_ticker, {
  message: 'Source and destination currencies must be different',
  path: ['to_ticker'],
}).refine(data => data.to_account_id !== data.account_id, {
  message: 'Target account must be different from source account',
  path: ['to_account_id'],
});

export type CreateExchangeFormData = z.infer<typeof createExchangeSchema>;

// Buy/Sell schema
export const createBuySellSchema = z.object({
  account_id: z.number().positive('Please select an account'),
  type: z.enum(['Buy', 'Sell']),
  ticker: z.string().min(1, 'Ticker is required'),
  quantity: z.number().positive('Quantity must be greater than 0'),
  price: z.number().positive('Price must be greater than 0'),
  price_currency: z.enum(['USD', 'KRW', 'JPY', 'EUR', 'GBP', 'HKD']),
  date: z.string().regex(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/, 'Invalid datetime format'),
  description: z.string().optional(),
});

export type CreateBuySellFormData = z.infer<typeof createBuySellSchema>;

// Recurring transfer schema
export const createRecurringTransferSchema = z.object({
  from_account_id: z.number().positive('Please select a source account'),
  to_account_id: z.number().positive('Please select a target account'),
  amount: z.number().positive('Amount must be greater than 0'),
  day_of_month: z.number().int().min(1, 'Day must be between 1 and 31').max(31, 'Day must be between 1 and 31'),
  description: z.string().optional(),
}).refine(data => data.from_account_id !== data.to_account_id, {
  message: 'Source and target accounts must be different',
  path: ['to_account_id'],
});

export type CreateRecurringTransferFormData = z.infer<typeof createRecurringTransferSchema>;
