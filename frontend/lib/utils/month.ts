/**
 * Month utilities for grouping and filtering transactions by month.
 * Used for monthly pagination in the ledger view.
 */

import {
  TransactionDetail,
  LedgerRow,
  DecimalString,
  MonthOption,
  MonthlyCashFlowSummary
} from '../types';
import { formatInTimeZone } from 'date-fns-tz';
import { parseDecimal } from './decimal';

const SEOUL_TZ = 'Asia/Seoul';

/**
 * Extract unique months from transactions, sorted newest first.
 *
 * @param transactions - Array of transactions
 * @returns Array of month options with value and label
 *
 * @example
 * const months = getMonthsFromTransactions(transactions);
 * // Returns: [
 * //   { value: "2024-03", label: "March 2024" },
 * //   { value: "2024-02", label: "February 2024" },
 * //   { value: "2024-01", label: "January 2024" }
 * // ]
 */
export function getMonthsFromTransactions(
  transactions: TransactionDetail[]
): MonthOption[] {
  const monthSet = new Set<string>();

  transactions.forEach(tx => {
    const date = new Date(tx.date);
    const monthString = formatInTimeZone(date, SEOUL_TZ, 'yyyy-MM');
    monthSet.add(monthString);
  });

  // Sort newest first
  const sortedMonths = Array.from(monthSet).sort((a, b) => b.localeCompare(a));

  return sortedMonths.map(month => ({
    value: month,
    label: formatMonthLabel(month)
  }));
}

/**
 * Filter transactions to specific month.
 *
 * @param transactions - Array of transactions
 * @param monthString - Format: "2024-01"
 * @returns Transactions from the specified month
 *
 * @example
 * const janTransactions = filterTransactionsByMonth(transactions, "2024-01");
 */
export function filterTransactionsByMonth(
  transactions: TransactionDetail[],
  monthString: string
): TransactionDetail[] {
  return transactions.filter(tx => {
    const date = new Date(tx.date);
    const txMonth = formatInTimeZone(date, SEOUL_TZ, 'yyyy-MM');
    return txMonth === monthString;
  });
}

/**
 * Calculate monthly cash flow summary from ledger rows.
 *
 * @param ledgerRows - Array of ledger rows (already transformed from transactions)
 * @returns Monthly summary with debit, credit, net flow, and balances
 *
 * @example
 * const summary = calculateMonthlyCashFlow(ledgerRows);
 * // Returns: {
 * //   totalDebit: "1500.00",
 * //   totalCredit: "5000.00",
 * //   netCashFlow: "3500.00",
 * //   openingBalance: "10000.00",
 * //   closingBalance: "13500.00",
 * //   transactionCount: 15
 * // }
 */
export function calculateMonthlyCashFlow(
  ledgerRows: LedgerRow[]
): MonthlyCashFlowSummary {
  if (ledgerRows.length === 0) {
    return {
      totalDebit: '0.00',
      totalCredit: '0.00',
      netCashFlow: '0.00',
      openingBalance: '0.00',
      closingBalance: '0.00',
      transactionCount: 0
    };
  }

  let totalDebit = 0;
  let totalCredit = 0;

  ledgerRows.forEach(row => {
    totalDebit += parseDecimal(row.debit);
    totalCredit += parseDecimal(row.credit);
  });

  const netCashFlow = totalCredit - totalDebit;

  // Opening balance = balance before first transaction
  // closingBalance = balance after last transaction
  const firstRow = ledgerRows[0];
  const lastRow = ledgerRows[ledgerRows.length - 1];

  const firstRowChange = parseDecimal(firstRow.credit) - parseDecimal(firstRow.debit);
  const openingBalance = parseDecimal(firstRow.balance) - firstRowChange;
  const closingBalance = parseDecimal(lastRow.balance);

  return {
    totalDebit: totalDebit.toFixed(2),
    totalCredit: totalCredit.toFixed(2),
    netCashFlow: netCashFlow.toFixed(2),
    openingBalance: openingBalance.toFixed(2),
    closingBalance: closingBalance.toFixed(2),
    transactionCount: ledgerRows.length
  };
}

/**
 * Format month string for display.
 *
 * @param monthString - Format: "2024-01"
 * @returns Formatted month label: "January 2024"
 *
 * @example
 * formatMonthLabel("2024-01") // Returns: "January 2024"
 * formatMonthLabel("2024-12") // Returns: "December 2024"
 */
export function formatMonthLabel(monthString: string): string {
  const [year, month] = monthString.split('-');
  const date = new Date(parseInt(year), parseInt(month) - 1, 1);
  return formatInTimeZone(date, SEOUL_TZ, 'MMMM yyyy');
}

/**
 * Get adjacent month (previous or next).
 * Returns null if direction would go out of available range.
 *
 * @param currentMonth - Current month string: "2024-01"
 * @param availableMonths - Array of available month strings
 * @param direction - "prev" for previous month (older), "next" for next month (newer)
 * @returns Adjacent month string or null if none available
 *
 * @example
 * const months = ["2024-03", "2024-02", "2024-01"]; // Newest first
 * getAdjacentMonth("2024-02", months, "prev") // Returns: "2024-01"
 * getAdjacentMonth("2024-02", months, "next") // Returns: "2024-03"
 * getAdjacentMonth("2024-03", months, "next") // Returns: null (at newest)
 */
export function getAdjacentMonth(
  currentMonth: string,
  availableMonths: string[],
  direction: 'prev' | 'next'
): string | null {
  const currentIndex = availableMonths.indexOf(currentMonth);
  if (currentIndex === -1) return null;

  // For "prev" (older), move forward in array (since array is sorted newest first)
  // For "next" (newer), move backward in array
  const targetIndex = direction === 'prev' ? currentIndex + 1 : currentIndex - 1;

  if (targetIndex < 0 || targetIndex >= availableMonths.length) {
    return null;
  }

  return availableMonths[targetIndex];
}
