# FRONTEND_COMPONENTS.md - Personal Asset Manager

Component hierarchy, props specifications, and UI patterns for the Next.js frontend.

---

## Overview

The frontend uses:
- **Framework:** Next.js 14+ (App Router)
- **State Management:** React Query (TanStack Query)
- **Styling:** Tailwind CSS
- **Charts:** Recharts
- **TypeScript:** Strict mode enabled

---

## Component Architecture

```
app/
├── page.tsx (Dashboard)
│   ├── <TotalAssetCard />
│   ├── <ExchangeRateDisplay />
│   ├── <AssetChangeStats />
│   ├── <AssetAllocationChart />
│   ├── <TopAssetsBarChart />
│   └── <AssetVolatilityChart />
│
├── accounts/
│   ├── page.tsx (Account List)
│   │   ├── <AccountCard />
│   │   ├── <AccountCard />
│   │   └── <AddAccountButton />
│   │
│   └── [id]/page.tsx (Account Details)
│       ├── <AccountSummaryHeader />
│       ├── <TabNavigation />
│       ├── Tab 1: <HoldingsTable />
│       ├── Tab 2: <TransactionTimeline />
│       └── Tab 3: <AccountAnalysisCharts />
│
└── components/
    ├── modals/
    │   ├── <AddAccountModal />
    │   ├── <AddTransactionModal />
    │   ├── <TransferModal />
    │   ├── <BuySellModal />
    │   └── <ExchangeModal />
    ├── charts/
    │   ├── <AssetAllocationChart />
    │   ├── <AssetVolatilityChart />
    │   ├── <TopAssetsBarChart />
    │   └── <DividendCalendar />
    └── ui/
        ├── <Card />
        ├── <Button />
        ├── <Input />
        ├── <Select />
        └── <DatePicker />
```

---

## Page Components

### 1. Dashboard (`app/page.tsx`)

**Purpose:** Control tower for viewing total asset overview.

**Data Fetching:**
```typescript
import { useDashboardSummary, useAssetChart } from '@/lib/hooks/useDashboard';

export default function DashboardPage() {
  const { data: summary, isLoading } = useDashboardSummary();
  const { data: chartData } = useAssetChart('1M', 'KRW');

  if (isLoading) return <LoadingSpinner />;

  return (
    <div className="space-y-6">
      <TotalAssetCard
        totalKRW={summary.total_assets.krw}
        totalUSD={summary.total_assets.usd}
      />
      <ExchangeRateDisplay rate={summary.current_exchange_rate} />
      <AssetChangeStats changes={summary.changes} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <AssetAllocationChart data={summary.allocation.by_type} />
        <TopAssetsBarChart assets={summary.top_assets} />
      </div>

      <AssetVolatilityChart data={chartData} />
    </div>
  );
}
```

---

### 2. Account List (`app/accounts/page.tsx`)

**Purpose:** Display all accounts in card format with action buttons.

**Data Fetching:**
```typescript
import { useAccounts } from '@/lib/hooks/useAccounts';
import { useState } from 'react';

export default function AccountsPage() {
  const { data: accounts, isLoading } = useAccounts();
  const [isModalOpen, setIsModalOpen] = useState(false);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Accounts</h1>
        <Button onClick={() => setIsModalOpen(true)}>
          Add New Account
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {accounts?.map(account => (
          <AccountCard key={account.id} account={account} />
        ))}
      </div>

      <AddAccountModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />
    </div>
  );
}
```

---

### 3. Account Details (`app/accounts/[id]/page.tsx`)

**Purpose:** Three-tab detailed view of a specific account.

**Data Fetching:**
```typescript
import { useAccountDetails } from '@/lib/hooks/useAccounts';
import { useParams } from 'next/navigation';
import { useState } from 'react';

type TabType = 'holdings' | 'transactions' | 'analysis';

export default function AccountDetailPage() {
  const params = useParams();
  const accountId = parseInt(params.id as string);

  const { data: account, isLoading } = useAccountDetails(accountId);
  const [activeTab, setActiveTab] = useState<TabType>('holdings');

  if (isLoading) return <LoadingSpinner />;

  return (
    <div className="space-y-6">
      <AccountSummaryHeader
        name={account.account.name}
        totalValue={account.summary.total_value}
        unrealizedPL={account.summary.unrealized_pl}
        cashBalance={account.summary.cash_balance}
      />

      <TabNavigation
        tabs={['Holdings', 'Transactions', 'Analysis']}
        activeTab={activeTab}
        onTabChange={setActiveTab}
      />

      {activeTab === 'holdings' && (
        <HoldingsTable holdings={account.holdings} />
      )}

      {activeTab === 'transactions' && (
        <TransactionTimeline accountId={accountId} />
      )}

      {activeTab === 'analysis' && (
        <AccountAnalysisCharts accountId={accountId} />
      )}
    </div>
  );
}
```

#### Conditional Tab Rendering by Account Type

Different account types show different tabs to reflect their specific functionality:

| Account Type | Holdings Tab | Transactions Tab | Analysis Tab | Rationale |
|--------------|--------------|------------------|--------------|-----------|
| **Deposit** | ❌ | ✅ | ❌ | Cash-only accounts have no holdings to display, just transaction history |
| **Securities** | ✅ | ✅ | ✅ | Full view: shows stock holdings, transactions, and performance analysis |
| **ForeignCurrency** | ✅ | ✅ | ❌ | Shows currency holdings (e.g., USD, EUR balances) and transaction history |
| **MoneyMarket** | ❌ | ✅ | ✅ | Shows transactions and interest tracking/performance over time |

**Implementation:**
```typescript
// frontend/lib/accountTypeConfig.ts
export const ACCOUNT_TAB_CONFIG = {
  Deposit: ['transactions'],
  Securities: ['holdings', 'transactions', 'analysis'],
  ForeignCurrency: ['holdings', 'transactions'],
  MoneyMarket: ['transactions', 'analysis'],
};

// Usage in account details page
import { ACCOUNT_TAB_CONFIG } from '@/lib/accountTypeConfig';

const allowedTabs = ACCOUNT_TAB_CONFIG[account.type] || ['transactions'];
const shouldShowHoldingsTab = allowedTabs.includes('holdings');
const shouldShowAnalysisTab = allowedTabs.includes('analysis');

<TabNavigation
  tabs={allowedTabs.map(tab => tab.charAt(0).toUpperCase() + tab.slice(1))}
  activeTab={activeTab}
  onTabChange={setActiveTab}
/>
```

---

## Feature Components

### TotalAssetCard

**Purpose:** Display total asset value with KRW/USD toggle and hide amount feature.

**Props:**
```typescript
interface TotalAssetCardProps {
  totalKRW: number;
  totalUSD: number;
}
```

**Component:**
```typescript
import { useState } from 'react';

export function TotalAssetCard({ totalKRW, totalUSD }: TotalAssetCardProps) {
  const [currency, setCurrency] = useState<'KRW' | 'USD'>('KRW');
  const [isHidden, setIsHidden] = useState(false);

  const displayAmount = currency === 'KRW' ? totalKRW : totalUSD;
  const formattedAmount = new Intl.NumberFormat('ko-KR', {
    style: 'currency',
    currency: currency,
  }).format(displayAmount);

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex justify-between items-center mb-2">
        <h2 className="text-gray-600">Total Assets</h2>
        <div className="flex gap-2">
          <button
            onClick={() => setIsHidden(!isHidden)}
            className="text-gray-400 hover:text-gray-600"
          >
            {isHidden ? '👁️' : '👁️‍🗨️'}
          </button>
          <button
            onClick={() => setCurrency(currency === 'KRW' ? 'USD' : 'KRW')}
            className="text-blue-600 hover:text-blue-800"
          >
            {currency === 'KRW' ? 'USD' : 'KRW'}
          </button>
        </div>
      </div>

      <div className="text-4xl font-bold">
        {isHidden ? '••••••••' : formattedAmount}
      </div>
    </div>
  );
}
```

---

### AssetChangeStats

**Purpose:** Display increase/decrease rate by period (Day, Month, Year).

**Props:**
```typescript
interface AssetChangeStatsProps {
  changes: {
    day: { amount_krw: number; percent: number };
    month: { amount_krw: number; percent: number };
    year: { amount_krw: number; percent: number };
  };
}
```

**Component:**
```typescript
export function AssetChangeStats({ changes }: AssetChangeStatsProps) {
  const periods = [
    { label: 'Day', data: changes.day },
    { label: 'Month', data: changes.month },
    { label: 'Year', data: changes.year },
  ];

  return (
    <div className="grid grid-cols-3 gap-4">
      {periods.map(({ label, data }) => (
        <div key={label} className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-600 mb-1">{label}</div>
          <div
            className={`text-2xl font-bold ${
              data.amount_krw >= 0 ? 'text-green-600' : 'text-red-600'
            }`}
          >
            {data.amount_krw >= 0 ? '+' : ''}
            {data.percent.toFixed(2)}%
          </div>
          <div className="text-sm text-gray-500">
            {data.amount_krw.toLocaleString()} KRW
          </div>
        </div>
      ))}
    </div>
  );
}
```

---

### AccountCard

**Purpose:** Display account summary with action buttons by type.

**Props:**
```typescript
interface AccountCardProps {
  account: {
    id: number;
    name: string;
    type: 'Deposit' | 'Securities' | 'ForeignCurrency' | 'MoneyMarket';
    currency: string;
    balance: number;
    balance_usd: number;
    holdings_count: number;
  };
}
```

**Component:**
```typescript
import Link from 'next/link';
import { useState } from 'react';

export function AccountCard({ account }: AccountCardProps) {
  const [showActions, setShowActions] = useState(false);

  // Action buttons based on account type
  const actionButtons = {
    Deposit: ['Transfer', 'Deposit', 'Withdrawal'],
    Securities: ['Buy', 'Sell', 'Dividend', 'Transfer'],
    ForeignCurrency: ['Exchange', 'Transfer'],
    MoneyMarket: ['Interest', 'Transfer'],
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition">
      <Link href={`/accounts/${account.id}`}>
        <div className="mb-4">
          <h3 className="text-xl font-bold mb-1">{account.name}</h3>
          <span className="text-sm text-gray-500">{account.type}</span>
        </div>

        <div className="text-3xl font-bold mb-2">
          {account.balance.toLocaleString()} {account.currency}
        </div>

        <div className="text-sm text-gray-600">
          ${account.balance_usd.toLocaleString()}
        </div>

        <div className="text-sm text-gray-500 mt-2">
          {account.holdings_count} holdings
        </div>
      </Link>

      <div className="mt-4 flex gap-2">
        {actionButtons[account.type].map(action => (
          <button
            key={action}
            className="text-sm px-3 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
            onClick={() => {/* Open modal */}}
          >
            {action}
          </button>
        ))}
      </div>
    </div>
  );
}
```

---

### HoldingsTable

**Purpose:** Display list of holdings with ticker, quantity, avg price, current price, and return %.

**Props:**
```typescript
interface HoldingsTableProps {
  holdings: Array<{
    ticker: string;
    ticker_name?: string;
    quantity: number;
    avg_price: number;
    current_price: number;
    current_value: number;
    cost_basis: number;
    unrealized_pl: number;
    unrealized_pl_percent: number;
  }>;
}
```

**Component:**
```typescript
export function HoldingsTable({ holdings }: HoldingsTableProps) {
  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Asset
            </th>
            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
              Quantity
            </th>
            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
              Avg Price
            </th>
            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
              Current Price
            </th>
            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
              Value
            </th>
            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
              Return
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {holdings.map(holding => (
            <tr key={holding.ticker}>
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="text-sm font-medium text-gray-900">
                  {holding.ticker}
                </div>
                {holding.ticker_name && (
                  <div className="text-sm text-gray-500">
                    {holding.ticker_name}
                  </div>
                )}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900">
                {holding.quantity.toLocaleString()}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900">
                {holding.avg_price.toLocaleString()}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900">
                {holding.current_price.toLocaleString()}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900">
                {holding.current_value.toLocaleString()}
              </td>
              <td className={`px-6 py-4 whitespace-nowrap text-right text-sm font-medium ${
                holding.unrealized_pl >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {holding.unrealized_pl >= 0 ? '+' : ''}
                {holding.unrealized_pl_percent.toFixed(2)}%
                <div className="text-xs">
                  ({holding.unrealized_pl.toLocaleString()})
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

---

### TransactionTimeline

**Purpose:** Timeline-style log of transactions with filtering and edit/delete.

**Props:**
```typescript
interface TransactionTimelineProps {
  accountId: number;
}
```

**Component:**
```typescript
import { useTransactions } from '@/lib/hooks/useTransactions';
import { useState } from 'react';

export function TransactionTimeline({ accountId }: TransactionTimelineProps) {
  const [filters, setFilters] = useState({
    type: '',
    startDate: '',
    endDate: '',
  });

  const { data: transactions, isLoading } = useTransactions({
    account_id: accountId,
    ...filters,
  });

  if (isLoading) return <LoadingSpinner />;

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex gap-4">
        <select
          value={filters.type}
          onChange={(e) => setFilters({ ...filters, type: e.target.value })}
          className="border rounded px-3 py-2"
        >
          <option value="">All Types</option>
          <option value="Buy">Buy</option>
          <option value="Sell">Sell</option>
          <option value="Deposit">Deposit</option>
          <option value="Withdrawal">Withdrawal</option>
        </select>

        <input
          type="date"
          value={filters.startDate}
          onChange={(e) => setFilters({ ...filters, startDate: e.target.value })}
          className="border rounded px-3 py-2"
        />

        <input
          type="date"
          value={filters.endDate}
          onChange={(e) => setFilters({ ...filters, endDate: e.target.value })}
          className="border rounded px-3 py-2"
        />
      </div>

      {/* Timeline */}
      <div className="space-y-3">
        {transactions?.transactions.map(tx => (
          <div key={tx.id} className="bg-white rounded-lg shadow p-4">
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className={`px-2 py-1 text-xs rounded ${
                    tx.type === 'Buy' || tx.type === 'Deposit'
                      ? 'bg-green-100 text-green-700'
                      : 'bg-red-100 text-red-700'
                  }`}>
                    {tx.type}
                  </span>
                  <span className="text-sm text-gray-600">{tx.date}</span>
                </div>

                <div className="text-lg font-semibold">
                  {tx.ticker && `${tx.ticker} `}
                  {tx.quantity && `${tx.quantity} shares @ ${tx.price}`}
                  {tx.amount && `${tx.amount.toLocaleString()} KRW`}
                </div>

                {tx.description && (
                  <div className="text-sm text-gray-600 mt-1">
                    {tx.description}
                  </div>
                )}
              </div>

              <div className="flex gap-2">
                <button className="text-sm text-blue-600 hover:text-blue-800">
                  Edit
                </button>
                <button className="text-sm text-red-600 hover:text-red-800">
                  Delete
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

## Modal Components

### AddAccountModal

**Purpose:** Create new account with initial balance.

**Props:**
```typescript
interface AddAccountModalProps {
  isOpen: boolean;
  onClose: () => void;
}
```

**Component:**
```typescript
import { useState } from 'react';
import { useCreateAccount } from '@/lib/hooks/useAccounts';

export function AddAccountModal({ isOpen, onClose }: AddAccountModalProps) {
  const [formData, setFormData] = useState({
    name: '',
    type: 'Deposit' as const,
    currency: 'KRW',
    initial_balance: 0,
    initial_balance_date: new Date().toISOString().split('T')[0],
  });

  const createAccount = useCreateAccount();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    await createAccount.mutateAsync(formData);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full">
        <h2 className="text-2xl font-bold mb-4">Add New Account</h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">
              Account Name
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full border rounded px-3 py-2"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Type</label>
            <select
              value={formData.type}
              onChange={(e) => setFormData({
                ...formData,
                type: e.target.value as any
              })}
              className="w-full border rounded px-3 py-2"
            >
              <option value="Deposit">Deposit/Withdrawal</option>
              <option value="Securities">Securities</option>
              <option value="ForeignCurrency">Foreign Currency</option>
              <option value="MoneyMarket">Money Market</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Currency</label>
            <select
              value={formData.currency}
              onChange={(e) => setFormData({
                ...formData,
                currency: e.target.value
              })}
              className="w-full border rounded px-3 py-2"
            >
              <option value="KRW">KRW (₩)</option>
              <option value="USD">USD ($)</option>
              <option value="EUR">EUR (€)</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">
              Initial Balance
            </label>
            <input
              type="number"
              value={formData.initial_balance}
              onChange={(e) => setFormData({
                ...formData,
                initial_balance: parseFloat(e.target.value)
              })}
              className="w-full border rounded px-3 py-2"
              min="0"
              step="0.01"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">
              Initial Balance Date
            </label>
            <input
              type="date"
              value={formData.initial_balance_date}
              onChange={(e) => setFormData({
                ...formData,
                initial_balance_date: e.target.value
              })}
              className="w-full border rounded px-3 py-2"
            />
          </div>

          <div className="flex gap-2 justify-end">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border rounded hover:bg-gray-100"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Create Account
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
```

---

## Chart Components

### AssetAllocationChart

**Purpose:** Pie chart showing asset allocation by type or risk.

**Props:**
```typescript
interface AssetAllocationChartProps {
  data: Array<{
    type: string;
    value_krw: number;
    percent: number;
  }>;
}
```

**Component:**
```typescript
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

export function AssetAllocationChart({ data }: AssetAllocationChartProps) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-bold mb-4">Asset Allocation</h3>

      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ type, percent }) => `${type} ${percent.toFixed(1)}%`}
            outerRadius={80}
            fill="#8884d8"
            dataKey="value_krw"
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip formatter={(value: number) => value.toLocaleString()} />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
```

---

### AssetVolatilityChart

**Purpose:** Line/candle chart showing total asset changes over time.

**Props:**
```typescript
interface AssetVolatilityChartProps {
  data: Array<{
    date: string;
    total_assets: number;
    principal: number;
    gain_loss: number;
  }>;
}
```

**Component:**
```typescript
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

export function AssetVolatilityChart({ data }: AssetVolatilityChartProps) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-bold mb-4">Asset Growth</h3>

      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip formatter={(value: number) => value.toLocaleString()} />
          <Legend />
          <Line
            type="monotone"
            dataKey="total_assets"
            stroke="#8884d8"
            name="Total Assets"
          />
          <Line
            type="monotone"
            dataKey="principal"
            stroke="#82ca9d"
            name="Principal"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
```

---

## React Query Hooks

### useAccounts

**File:** `lib/hooks/useAccounts.ts`

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

interface Account {
  id: number;
  name: string;
  type: string;
  currency: string;
  balance: number;
  balance_usd: number;
  holdings_count: number;
}

export function useAccounts() {
  return useQuery<{ accounts: Account[] }>({
    queryKey: ['accounts'],
    queryFn: async () => {
      const res = await fetch('/api/accounts');
      if (!res.ok) throw new Error('Failed to fetch accounts');
      return res.json();
    },
  });
}

export function useAccountDetails(id: number) {
  return useQuery({
    queryKey: ['accounts', id],
    queryFn: async () => {
      const res = await fetch(`/api/accounts/${id}`);
      if (!res.ok) throw new Error('Failed to fetch account details');
      return res.json();
    },
  });
}

export function useCreateAccount() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: any) => {
      const res = await fetch('/api/accounts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!res.ok) throw new Error('Failed to create account');
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] });
    },
  });
}
```

---

## TypeScript Types

**File:** `lib/types.ts`

```typescript
// Mirror backend Pydantic schemas

export interface Account {
  id: number;
  name: string;
  type: 'Deposit' | 'Securities' | 'ForeignCurrency' | 'MoneyMarket';
  currency: string;
  created_at: string;
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

export interface Transaction {
  id: number;
  account_id: number;
  account_name: string;
  type: 'Buy' | 'Sell' | 'Deposit' | 'Withdrawal' | 'Transfer_In' | 'Transfer_Out' | 'Exchange' | 'Dividend';
  ticker?: string;
  ticker_name?: string;
  quantity?: number;
  price?: number;
  amount: number;
  date: string;
  description?: string;
  linked_tx_id?: number;
  created_at: string;
}

export interface DashboardSummary {
  total_assets: {
    krw: number;
    usd: number;
  };
  current_exchange_rate: {
    usd_to_krw: number;
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
```

---

## Styling Patterns

### Tailwind Utility Classes

**Common patterns:**

```typescript
// Card container
<div className="bg-white rounded-lg shadow-lg p-6">

// Button primary
<button className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">

// Button secondary
<button className="px-4 py-2 border rounded hover:bg-gray-100">

// Input field
<input className="w-full border rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500" />

// Table header
<th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">

// Positive/negative numbers
<span className={value >= 0 ? 'text-green-600' : 'text-red-600'}>
  {value >= 0 ? '+' : ''}{value.toFixed(2)}%
</span>
```

---

## Form Validation

**Example using Zod:**

```typescript
import { z } from 'zod';

const accountSchema = z.object({
  name: z.string().min(1, 'Account name is required'),
  type: z.enum(['Deposit', 'Securities', 'ForeignCurrency', 'MoneyMarket']),
  currency: z.string().length(3),
  initial_balance: z.number().min(0),
  initial_balance_date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
});

type AccountFormData = z.infer<typeof accountSchema>;

// In component
const { register, handleSubmit, formState: { errors } } = useForm<AccountFormData>({
  resolver: zodResolver(accountSchema),
});
```

---

## Error Handling

**Example error boundary:**

```typescript
import { useEffect } from 'react';

export function ErrorBoundary({ error, reset }: {
  error: Error;
  reset: () => void;
}) {
  useEffect(() => {
    console.error('Error:', error);
  }, [error]);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <h2 className="text-2xl font-bold mb-4">Something went wrong!</h2>
        <p className="text-gray-600 mb-4">{error.message}</p>
        <button
          onClick={reset}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Try again
        </button>
      </div>
    </div>
  );
}
```

---

## Loading States

**Skeleton loaders:**

```typescript
export function AccountCardSkeleton() {
  return (
    <div className="bg-white rounded-lg shadow-lg p-6 animate-pulse">
      <div className="h-6 bg-gray-200 rounded w-3/4 mb-4"></div>
      <div className="h-8 bg-gray-200 rounded w-1/2 mb-2"></div>
      <div className="h-4 bg-gray-200 rounded w-1/4"></div>
    </div>
  );
}
```

---

## Accessibility

**Best practices:**

```typescript
// Semantic HTML
<button aria-label="Close modal" onClick={onClose}>
  ×
</button>

// Keyboard navigation
<div
  role="button"
  tabIndex={0}
  onKeyDown={(e) => e.key === 'Enter' && onClick()}
  onClick={onClick}
>
  Click me
</div>

// ARIA labels
<input
  type="number"
  aria-label="Transfer amount"
  aria-describedby="amount-help"
/>
<span id="amount-help" className="text-sm text-gray-600">
  Enter the amount to transfer
</span>
```

---

## Performance Optimization

**Memoization:**

```typescript
import { useMemo } from 'react';

function ExpensiveComponent({ data }: { data: Transaction[] }) {
  const sortedData = useMemo(() => {
    return data.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
  }, [data]);

  return <TransactionList transactions={sortedData} />;
}
```

**Code splitting:**

```typescript
import dynamic from 'next/dynamic';

const HeavyChart = dynamic(() => import('@/components/charts/HeavyChart'), {
  loading: () => <LoadingSpinner />,
  ssr: false,  // Disable SSR for heavy components
});
```
