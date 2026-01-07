import { z } from 'zod';

// Account creation schema
export const createAccountSchema = z.object({
  name: z.string().min(1, 'Account name is required'),
  type: z.enum(['Deposit', 'Securities', 'ForeignCurrency', 'MoneyMarket']),
  currency: z.string().length(3, 'Currency must be 3 characters'),
  initial_balance: z.number().min(0, 'Balance cannot be negative'),
  initial_balance_date: z.string().regex(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/, 'Invalid datetime format'),
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

// Transfer schema
export const createTransferSchema = z.object({
  from_account_id: z.number().positive('Please select source account'),
  to_account_id: z.number().positive('Please select destination account'),
  amount: z.number().positive('Amount must be greater than 0'),
  date: z.string().regex(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/, 'Invalid datetime format'),
  description: z.string().optional(),
}).refine(data => data.from_account_id !== data.to_account_id, {
  message: 'Source and destination accounts must be different',
  path: ['to_account_id'],
});

export type CreateTransferFormData = z.infer<typeof createTransferSchema>;

// Exchange schema
export const createExchangeSchema = z.object({
  account_id: z.number().positive('Please select an account'),
  from_ticker: z.string().min(1, 'From currency is required'),
  to_ticker: z.string().min(1, 'To currency is required'),
  from_amount: z.number().positive('Amount must be greater than 0'),
  to_amount: z.number().positive('Amount must be greater than 0'),
  exchange_rate: z.number().positive().optional(),
  date: z.string().regex(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/, 'Invalid datetime format'),
  description: z.string().optional(),
}).refine(data => data.from_ticker !== data.to_ticker, {
  message: 'Source and destination currencies must be different',
  path: ['to_ticker'],
});

export type CreateExchangeFormData = z.infer<typeof createExchangeSchema>;

// Buy/Sell schema
export const createBuySellSchema = z.object({
  account_id: z.number().positive('Please select an account'),
  type: z.enum(['Buy', 'Sell']),
  ticker: z.string().min(1, 'Ticker is required'),
  quantity: z.number().positive('Quantity must be greater than 0'),
  price: z.number().positive('Price must be greater than 0'),
  date: z.string().regex(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/, 'Invalid datetime format'),
  description: z.string().optional(),
});

export type CreateBuySellFormData = z.infer<typeof createBuySellSchema>;
