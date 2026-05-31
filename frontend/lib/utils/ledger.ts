/**
 * Ledger transformation utilities
 *
 * Converts transaction history into traditional accounting ledger format
 * with running balance calculation.
 */

import type { TransactionDetail, LedgerRow, DecimalString } from '../types';
import { parseDecimal } from './decimal';

export {
  LEDGER_DISPLAYABLE_TRANSACTION_TYPES,
  isLedgerDisplayableTransaction,
} from './ledgerFilters';

/**
 * Transaction types that represent internal movements (Patterns ② and ④)
 * These should be hidden from the ledger view.
 */
export const LEDGER_HIDDEN_TRANSACTION_TYPES = [
  'Transfer_In',
  'Transfer_Out',
  'Exchange'
] as const;

/**
 * Converts transactions into ledger rows with running balance.
 *
 * Features:
 * - Sorts transactions chronologically (oldest first)
 * - Merges linked transactions (transfers/exchanges) into single rows
 * - Calculates running balance after each transaction
 * - Handles edge cases (orphaned links, same timestamps)
 *
 * @param transactions - Array of transactions (will be sorted)
 * @param initialBalance - Starting balance (default: 0)
 * @returns Array of ledger rows with running balance
 *
 * @example
 * const transactions = [
 *   { id: 1, date: '2024-01-01', type: 'Deposit', amount: '1000' },
 *   { id: 2, date: '2024-01-02', type: 'Withdrawal', amount: '-500' },
 * ];
 * const ledgerRows = transactionsToLedgerRows(transactions);
 * // Returns:
 * // [
 * //   { date: '2024-01-01', debit: '0.00', credit: '1000.00', balance: '1000.00' },
 * //   { date: '2024-01-02', debit: '500.00', credit: '0.00', balance: '500.00' },
 * // ]
 */
export function transactionsToLedgerRows(
  transactions: TransactionDetail[],
  initialBalance: DecimalString = '0.00'
): LedgerRow[] {
  // 1. Sort chronologically (oldest first)
  // Use secondary sort by ID to ensure consistent ordering for same-timestamp transactions
  const sortedTxs = [...transactions].sort((a, b) => {
    const dateDiff = new Date(a.date).getTime() - new Date(b.date).getTime();
    if (dateDiff !== 0) return dateDiff;
    return a.id - b.id;  // Secondary sort by ID
  });

  // 2. Track which transactions have been merged (for linked pairs)
  const processedIds = new Set<number>();
  const ledgerRows: LedgerRow[] = [];
  let runningBalance = parseDecimal(initialBalance);

  // 3. Process each transaction
  for (const tx of sortedTxs) {
    // Skip if already processed as part of a linked pair
    if (processedIds.has(tx.id)) continue;

    // Check if this is a linked transaction (Transfer or Exchange)
    if (tx.linked_tx_id) {
      const linkedTx = sortedTxs.find(t => t.id === tx.linked_tx_id);

      if (linkedTx) {
        // Merge into single ledger row
        const row = createMergedLedgerRow(tx, linkedTx, runningBalance);
        ledgerRows.push(row);
        runningBalance = parseDecimal(row.balance);

        processedIds.add(tx.id);
        processedIds.add(linkedTx.id);
        continue;
      } else {
        // Orphaned linked transaction - log warning and treat as single
        console.warn(
          `Transaction ${tx.id} has linked_tx_id=${tx.linked_tx_id} but linked transaction not found. Treating as single transaction.`
        );
      }
    }

    // Single transaction (Deposit, Withdrawal, Dividend, etc.)
    const row = createSingleLedgerRow(tx, runningBalance);
    ledgerRows.push(row);
    runningBalance = parseDecimal(row.balance);
    processedIds.add(tx.id);
  }

  return ledgerRows;
}

/**
 * Creates a ledger row from a single transaction.
 *
 * @param tx - Transaction to convert
 * @param currentBalance - Current running balance
 * @returns Ledger row with debit/credit/balance
 */
function createSingleLedgerRow(
  tx: TransactionDetail,
  currentBalance: number
): LedgerRow {
  const amount = parseDecimal(tx.amount);
  const isCredit = amount > 0;  // Positive = incoming money (credit)

  const newBalance = currentBalance + amount;

  return {
    id: tx.id,
    date: tx.date,
    description: tx.description || getDefaultDescription(tx),
    debit: isCredit ? '0.00' : Math.abs(amount).toFixed(2),
    credit: isCredit ? amount.toFixed(2) : '0.00',
    balance: newBalance.toFixed(2),
    ticker: tx.ticker,
    linkedTxId: tx.linked_tx_id,
    accountName: tx.account_name,
  };
}

/**
 * Creates a merged ledger row from linked transactions (Transfer/Exchange).
 *
 * For transfers, both debit and credit are shown in a single row.
 * The net effect on balance is determined by which transaction belongs to the current account.
 *
 * @param tx - First transaction
 * @param linkedTx - Linked transaction
 * @param currentBalance - Current running balance
 * @returns Merged ledger row
 */
function createMergedLedgerRow(
  tx: TransactionDetail,
  linkedTx: TransactionDetail,
  currentBalance: number
): LedgerRow {
  // Determine which transaction is debit and which is credit
  const txAmount = parseDecimal(tx.amount);
  const linkedTxAmount = parseDecimal(linkedTx.amount);

  // For the current account, determine if money is going out (debit) or coming in (credit)
  const isDebit = txAmount < 0;

  // Both amounts should be shown in their absolute values
  const debitAmount = Math.abs(isDebit ? txAmount : linkedTxAmount);
  const creditAmount = Math.abs(isDebit ? linkedTxAmount : txAmount);

  // Net effect on balance for THIS account
  const netChange = txAmount;
  const newBalance = currentBalance + netChange;

  // Determine counterparty for description
  let counterpartyInfo = '';
  if (tx.type === 'Transfer_Out' || tx.type === 'Transfer_In') {
    // For transfers, show the other account
    if (linkedTx.account_name && linkedTx.account_name !== tx.account_name) {
      counterpartyInfo = isDebit
        ? `To ${linkedTx.account_name}`
        : `From ${linkedTx.account_name}`;
    }
  } else if (tx.type === 'Exchange') {
    // For exchanges, show currency conversion
    const fromCurrency = isDebit ? tx.ticker : linkedTx.ticker;
    const toCurrency = isDebit ? linkedTx.ticker : tx.ticker;
    if (linkedTx.account_name && linkedTx.account_name !== tx.account_name) {
      // Cross-account exchange
      counterpartyInfo = `${fromCurrency} → ${toCurrency} (${isDebit ? 'To' : 'From'} ${linkedTx.account_name})`;
    } else {
      // Same-account exchange
      counterpartyInfo = `${fromCurrency} → ${toCurrency}`;
    }
  }

  const description = tx.description || `Transfer ${counterpartyInfo}`;

  return {
    id: tx.id,
    date: tx.date,
    description,
    debit: debitAmount.toFixed(2),
    credit: creditAmount.toFixed(2),
    balance: newBalance.toFixed(2),
    ticker: tx.ticker,
    linkedTxId: linkedTx.id,
    counterpartyAccount: counterpartyInfo,
    accountName: tx.account_name,
  };
}

/**
 * Generate default description based on transaction type.
 *
 * @param tx - Transaction
 * @returns Human-readable description
 */
function getDefaultDescription(tx: TransactionDetail): string {
  switch (tx.type) {
    case 'Deposit':
      return 'Deposit';
    case 'Withdrawal':
      return 'Withdrawal';
    case 'Dividend':
      return tx.ticker ? `Dividend from ${tx.ticker}` : 'Dividend';
    case 'Interest':
      return 'Interest income';
    case 'Buy':
      return tx.ticker ? `Buy ${tx.ticker}` : 'Buy securities';
    case 'Sell':
      return tx.ticker ? `Sell ${tx.ticker}` : 'Sell securities';
    case 'Transfer_Out':
      return 'Transfer out';
    case 'Transfer_In':
      return 'Transfer in';
    case 'Exchange':
      return tx.ticker ? `Exchange ${tx.ticker}` : 'Currency exchange';
    default:
      return tx.type;
  }
}

/**
 * Calculate initial balance by working backwards from current cash balance.
 *
 * Useful when account was created with an unknown initial balance.
 * Subtracts all transaction amounts from current balance to get initial balance.
 *
 * @param transactions - All transactions for the account (sorted chronologically)
 * @param currentCashBalance - Current cash balance from account summary
 * @returns Calculated initial balance
 *
 * @example
 * const transactions = [
 *   { amount: '1000' },  // Deposit
 *   { amount: '-500' },  // Withdrawal
 * ];
 * const currentBalance = 1500;
 * const initialBalance = calculateInitialBalance(transactions, currentBalance);
 * // Returns: 1000 (currentBalance - sum of all amounts)
 */
export function calculateInitialBalance(
  transactions: TransactionDetail[],
  currentCashBalance: DecimalString
): DecimalString {
  const current = parseDecimal(currentCashBalance);

  // Sum all transaction amounts
  const totalChange = transactions.reduce((sum, tx) => {
    return sum + parseDecimal(tx.amount);
  }, 0);

  const initial = current - totalChange;
  return initial.toFixed(2);
}
