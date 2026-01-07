'use client';

import { useParams, useSearchParams, useRouter } from 'next/navigation';
import { useAccountDetails } from '@/lib/hooks/useAccounts';
import { Spinner } from '@/components/ui/Spinner';
import { AccountSummaryHeader } from './_components/AccountSummaryHeader';
import { TabNavigation } from './_components/TabNavigation';
import { HoldingsTable } from './_components/HoldingsTable';
import { TransactionTimeline } from './_components/TransactionTimeline';
import { AccountAnalysisCharts } from './_components/AccountAnalysisCharts';
import { DeleteAccountModal } from '@/components/modals/DeleteAccountModal';
import { getAccountTypeConfig, isTabAllowed, type AccountTab } from '@/lib/config/accountTypeConfig';

export default function AccountDetailPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const accountId = parseInt(params.id as string);

  const { data: accountData, isLoading, isFetching, error } = useAccountDetails(accountId);

  // Check if delete modal should be shown
  const modal = searchParams.get('modal');
  const modalAccountId = searchParams.get('accountId');
  const showDeleteModal = modal === 'delete-account' &&
                          modalAccountId === accountId.toString();

  const closeModal = () => {
    router.push(`/accounts/${accountId}`);
  };

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
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Account Not Found</h3>
        <p className="text-gray-700">
          The account you are looking for does not exist.
        </p>
      </div>
    );
  }

  const { account, summary, holdings } = accountData;

  // Get account type configuration
  const accountConfig = getAccountTypeConfig(account.type);
  const currency = ['Securities', 'ForeignCurrency'].includes(account.type) ? 'USD' : 'KRW';

  // Build dynamic tabs based on account type
  const ALL_POSSIBLE_TABS = [
    { key: 'holdings' as AccountTab, label: 'Holdings' },
    { key: 'transactions' as AccountTab, label: 'Transactions' },
    { key: 'analysis' as AccountTab, label: 'Analysis' },
  ];

  const availableTabs = ALL_POSSIBLE_TABS.filter(tab =>
    accountConfig.allowedTabs.includes(tab.key)
  );

  // Get active tab from URL, default to first available tab
  const requestedTab = searchParams.get('tab') as AccountTab | null;
  const activeTab = requestedTab && isTabAllowed(account.type, requestedTab)
    ? requestedTab
    : availableTabs[0]?.key || 'transactions';

  return (
    <div className="space-y-6">
      <AccountSummaryHeader
        accountId={accountId}
        name={account.name}
        type={account.type}
        currency={currency}
        totalValue={summary.total_value}
        cashBalance={summary.cash_balance}
        unrealizedPL={summary.unrealized_pl}
        unrealizedPLPercent={summary.unrealized_pl_percent}
        isRefetching={isFetching}
      />

      <div className="bg-white rounded-lg shadow">
        <TabNavigation tabs={availableTabs} activeTab={activeTab} />

        <div className="p-6">
          {activeTab === 'holdings' && isTabAllowed(account.type, 'holdings') && (
            <HoldingsTable holdings={holdings} currency={currency} />
          )}

          {activeTab === 'transactions' && (
            <TransactionTimeline accountId={accountId} />
          )}

          {activeTab === 'analysis' && isTabAllowed(account.type, 'analysis') && (
            <AccountAnalysisCharts accountId={accountId} />
          )}
        </div>
      </div>

      {/* Delete Account Modal */}
      {showDeleteModal && accountData && (
        <DeleteAccountModal
          isOpen={true}
          onClose={closeModal}
          account={{
            ...account,
            balance: summary.total_value,
            balance_usd: summary.total_value, // Using total_value as fallback
            holdings_count: holdings.length,
          }}
        />
      )}
    </div>
  );
}
