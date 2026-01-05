// Base types
export interface Account {
  id: number;
  name: string;
  type: 'Checking' | 'Brokerage' | 'Foreign' | 'MMF';
  currency: string;
  created_at: string;
}

export interface AccountWithBalance extends Account {
  balance: number;
  balance_usd: number;
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
  quantity?: number;
  price?: number;
  linked_tx_id?: number;
}

export interface Holding {
  id: number;
  account_id: number;
  ticker: string;
  ticker_name?: string;
  quantity: number;
  avg_price: number;
  current_price: number;
  current_value: number;
  cost_basis: number;
  unrealized_pl: number;
  unrealized_pl_percent: number;
}

export interface AccountDetails {
  account: Account;
  summary: {
    total_value: number;
    cash_balance: number;
    invested_amount: number;
    unrealized_pl: number;
    unrealized_pl_percent: number;
  };
  holdings: Holding[];
}

// Dashboard types
export interface DashboardSummary {
  total_assets: {
    krw: number;
    usd: number;
  };
  current_exchange_rate: {
    usd_to_krw: string;  // Decimal as string from backend (e.g., "1300.0000")
    updated_at: string;
  };
  changes: {
    day: { amount_krw: number; amount_usd: number; percent: number };
    month: { amount_krw: number; amount_usd: number; percent: number };
    year: { amount_krw: number; amount_usd: number; percent: number };
  };
  allocation: {
    by_type: Array<{ type: string; value_krw: number; percent: number }>;
    by_risk: Array<{ type: string; value_krw: number; percent: number }>;
  };
  top_assets: Array<{
    ticker: string;
    name: string;
    value_krw: number;
    percent: number;
  }>;
}

export interface AssetChartData {
  date: string;
  total_assets: number;
  principal: number;
  gain_loss: number;
}

// Form input types
export interface CreateAccountInput {
  name: string;
  type: 'Checking' | 'Brokerage' | 'Foreign' | 'MMF';
  currency: string;
  initial_balance: number;
  initial_balance_date: string;
}

export interface CreateTransactionInput {
  account_id: number;
  type: string;
  amount?: number;
  ticker?: string;
  quantity?: number;
  price?: number;
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
  ticker: string;
  date: string;
  closing_price: number;
  currency: string;
  source: string;
  cached: boolean;
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