'use client';

import { useParams, useSearchParams } from 'next/navigation';
import { useAccountDetails } from '@/lib/hooks/useAccounts';
import { Spinner } from '@/components/ui/Spinner';
import { AccountSummaryHeader } from './_components/AccountSummaryHeader';
import { TabNavigation } from './_components/TabNavigation';
import { HoldingsTable } from './_components/HoldingsTable';
import { TransactionTimeline } from './_components/TransactionTimeline';
import { AccountAnalysisCharts } from './_components/AccountAnalysisCharts';

const TABS = [
  { key: 'holdings', label: 'Holdings' },
  { key: 'transactions', label: 'Transactions' },
  { key: 'analysis', label: 'Analysis' },
];

export default function AccountDetailPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const accountId = parseInt(params.id as string);

  const { data: accountData, isLoading, isFetching, error } = useAccountDetails(accountId);

  // Get active tab from URL, default to 'holdings'
  const activeTab = searchParams.get('tab') || 'holdings';

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Spinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
        <strong>Error:</strong> {error.message}
      </div>
    );
  }

  if (!accountData) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold mb-2">Account Not Found</h3>
        <p className="text-gray-700">
          The account you are looking for does not exist.
        </p>
      </div>
    );
  }

  const { account, summary, holdings } = accountData;

  return (
    <div className="space-y-6">
      <AccountSummaryHeader
        name={account.name}
        type={account.type}
        currency={account.currency}
        totalValue={summary.total_value}
        cashBalance={summary.cash_balance}
        unrealizedPL={summary.unrealized_pl}
        unrealizedPLPercent={summary.unrealized_pl_percent}
        isRefetching={isFetching}
      />

      <div className="bg-white rounded-lg shadow">
        <TabNavigation tabs={TABS} activeTab={activeTab} />

        <div className="p-6">
          {activeTab === 'holdings' && (
            <HoldingsTable holdings={holdings} currency={account.currency} />
          )}

          {activeTab === 'transactions' && (
            <TransactionTimeline accountId={accountId} />
          )}

          {activeTab === 'analysis' && (
            <AccountAnalysisCharts accountId={accountId} />
          )}
        </div>
      </div>
    </div>
  );
}
