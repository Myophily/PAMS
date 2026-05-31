import type { Account, TransactionDetail } from '../types';

/**
 * Transaction types that represent money entering or leaving current assets.
 * Internal transfers, exchanges, buys, and sells are excluded from this view.
 */
export const LEDGER_DISPLAYABLE_TRANSACTION_TYPES = [
  'Deposit',
  'Withdrawal',
  'Dividend',
  'Interest',
] as const;

export type LedgerDisplayableTransactionType =
  (typeof LEDGER_DISPLAYABLE_TRANSACTION_TYPES)[number];

export function isLedgerDisplayableTransaction(
  transactionType: string
): boolean {
  return LEDGER_DISPLAYABLE_TRANSACTION_TYPES.includes(
    transactionType as LedgerDisplayableTransactionType
  );
}

export function filterLedgerMoneyFlowTransactions(
  transactions: TransactionDetail[],
  accounts: Account[],
  selectedAccountIds: number[]
): TransactionDetail[] {
  const selectedIds =
    selectedAccountIds.length > 0
      ? new Set(selectedAccountIds)
      : new Set(accounts.map(account => account.id));

  return transactions
    .filter(tx => selectedIds.has(tx.account_id))
    .filter(tx => isLedgerDisplayableTransaction(tx.type))
    .map(tx => {
      const account = accounts.find(acc => acc.id === tx.account_id);

      return {
        ...tx,
        account_name: tx.account_name || account?.name || 'Unknown',
      };
    })
    .sort((a, b) => {
      const dateDiff = new Date(a.date).getTime() - new Date(b.date).getTime();
      if (dateDiff !== 0) return dateDiff;
      return a.id - b.id;
    });
}
