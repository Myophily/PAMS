/**
 * Decimal value from backend, serialized as string.
 * Example: "1234.56", "0.0000", "-99.99"
 *
 * Backend uses Python's Decimal type for precision, which Pydantic
 * serializes to JSON as strings to prevent floating-point errors.
 *
 * Use parseDecimal() to convert to number for calculations.
 * Use formatDecimal() for display with locale formatting.
 */
export type DecimalString = string;

// Base types
export interface Account {
  id: number;
  name: string;
  type: 'Deposit' | 'Securities' | 'ForeignCurrency' | 'MoneyMarket' | 'Savings';
  created_at: string;
}

export interface AccountWithBalance extends Account {
  balance: DecimalString;  // Cash only (backward compat)
  total_value: DecimalString;  // NEW: Total portfolio value (cash + stocks)
  total_value_krw: DecimalString;  // NEW: Total value in KRW
  stock_value: DecimalString;  // NEW: Stock holdings value
  balance_usd: DecimalString;  // Now represents total portfolio USD value
  currency: string;  // Inferred primary currency from holdings (e.g., "KRW", "USD")
  holdings_count: number;
}

export interface Transaction {
  id: number;
  account_id: number;
  type: string;
  amount: string; // String because Decimal comes as string from JSON
  date: string;
  description?: string;
  created_at: string;
}

export interface TransactionDetail extends Transaction {
  account_name: string;
  ticker?: string;
  ticker_name?: string;
  quantity?: DecimalString;  // Decimal as string from backend
  price?: DecimalString;  // Decimal as string from backend
  price_currency?: string;  // Currency for stock prices (KRW, USD, JPY, etc.)
  linked_tx_id?: number;
}

export interface Holding {
  id: number;
  account_id: number;
  ticker: string;
  ticker_name?: string;
  quantity: DecimalString;  // Decimal as string from backend
  avg_price: DecimalString;  // Decimal as string from backend
  price_currency?: string;  // Currency for stock prices (KRW, USD, JPY, etc.)
  current_price: DecimalString;  // Decimal as string from backend
  current_value: DecimalString;  // Decimal as string from backend
  cost_basis: DecimalString;  // Decimal as string from backend
  unrealized_pl: DecimalString;  // Decimal as string from backend
  unrealized_pl_percent: DecimalString;  // Decimal as string from backend
}

export interface AccountDetails {
  account: Account;
  summary: {
    total_value: DecimalString;  // Decimal as string from backend
    total_value_krw: DecimalString;  // Total value converted to KRW
    cash_balance: DecimalString;  // Decimal as string from backend
    cash_balance_krw: DecimalString;  // Cash balance converted to KRW
    invested_amount: DecimalString;  // Decimal as string from backend
    unrealized_pl: DecimalString;  // Decimal as string from backend
    unrealized_pl_krw: DecimalString;  // Unrealized P/L converted to KRW
    unrealized_pl_percent: DecimalString;  // Decimal as string from backend
    currency: string;  // Inferred primary currency from holdings (e.g., "KRW", "USD")
  };
  holdings: Holding[];
}

// Dashboard types
export interface DashboardSummary {
  total_assets: {
    krw: DecimalString;  // Decimal as string from backend
    usd: DecimalString;  // Decimal as string from backend
  };
  current_exchange_rate: {
    usd_to_krw: string;  // Decimal as string from backend (e.g., "1300.0000")
    updated_at: string;
  };
  changes: {
    day: { amount_krw: DecimalString; amount_usd: DecimalString; percent: DecimalString };
    month: { amount_krw: DecimalString; amount_usd: DecimalString; percent: DecimalString };
    year: { amount_krw: DecimalString; amount_usd: DecimalString; percent: DecimalString };
  };
  allocation: {
    by_type: Array<{ type: string; value_krw: DecimalString; percent: DecimalString }>;
    by_risk: Array<{ type: string; value_krw: DecimalString; percent: DecimalString }>;
  };
  top_assets: Array<{
    ticker: string;
    name: string;
    value_krw: DecimalString;
    percent: DecimalString;
  }>;
}

export interface AssetChartData {
  date: string;
  total_assets: DecimalString;  // Decimal as string from backend
  principal: DecimalString;  // Decimal as string from backend
  gain_loss: DecimalString;  // Decimal as string from backend
}

// Form input types
export interface InitialHoldingItem {
  ticker: string;      // "KRW", "USD", "AAPL", "TSLA", "GOLD" (currency or asset ticker)
  quantity: number;
  price?: number;      // Required for non-currency tickers
  price_currency?: string;  // Currency for stock prices (KRW or USD)
}

export interface CreateAccountInput {
  name: string;
  type: 'Deposit' | 'Securities' | 'ForeignCurrency' | 'MoneyMarket' | 'Savings';
  initial_balance?: number;  // DEPRECATED: Use initial_holdings instead
  initial_balance_date: string;
  initial_holdings?: InitialHoldingItem[];  // Now for ALL account types
}

export interface CreateTransactionInput {
  account_id: number;
  type: string;
  amount?: number;
  ticker?: string;
  quantity?: number;
  price?: number;
  price_currency?: string;
  date: string;
  description?: string;
}

export interface CreateTransferInput {
  from_account_id: number;
  to_account_id: number;
  amount: number;
  date: string;
  description?: string;
}

export interface CreateExchangeInput {
  account_id: number;
  from_ticker: string;
  to_ticker: string;
  from_amount: number;
  to_amount: number;
  exchange_rate?: number;
  date: string;
  description?: string;
}

// Market data types
export interface StockPrice {
  price: string;        // Decimal as string from backend
  currency: string;
  source: string;
  is_cached: boolean;   // Changed from cached
  date: string;
}

export interface ExchangeRate {
  from: string;
  to: string;
  rate: string;  // Decimal as string from backend (e.g., "1300.0000")
  date: string;
  source: string;
}

// Health check (existing)
export interface HealthStatus {
  status: 'healthy' | 'unhealthy';
  database: string;
  accounts_count: number;
  error?: string;
}