import assert from 'node:assert/strict';
import test from 'node:test';

import { filterLedgerMoneyFlowTransactions } from './ledgerFilters.ts';

const accounts = [
  {
    id: 1,
    name: 'Checking',
    type: 'Deposit',
    created_at: '2026-01-01T00:00:00+09:00',
  },
  {
    id: 2,
    name: 'Brokerage',
    type: 'Securities',
    created_at: '2026-01-01T00:00:00+09:00',
  },
  {
    id: 3,
    name: 'Foreign Cash',
    type: 'ForeignCurrency',
    created_at: '2026-01-01T00:00:00+09:00',
  },
];

const baseTransaction = {
  date: '2026-01-02T09:00:00+09:00',
  created_at: '2026-01-02T09:00:00+09:00',
  amount: '0.00',
  account_name: '',
};

test('keeps external money in/out transactions from every account type', () => {
  const transactions = [
    {
      ...baseTransaction,
      id: 1,
      account_id: 1,
      type: 'Withdrawal',
      amount: '-5000.00',
    },
    {
      ...baseTransaction,
      id: 2,
      account_id: 2,
      type: 'Dividend',
      amount: '1200.00',
      ticker: 'AAPL',
    },
    {
      ...baseTransaction,
      id: 3,
      account_id: 3,
      type: 'Deposit',
      amount: '100.00',
      ticker: 'USD',
    },
    {
      ...baseTransaction,
      id: 4,
      account_id: 2,
      type: 'Buy',
      amount: '-900.00',
      ticker: 'AAPL',
    },
    {
      ...baseTransaction,
      id: 5,
      account_id: 1,
      type: 'Transfer_Out',
      amount: '-2000.00',
      linked_tx_id: 6,
    },
  ];

  const filtered = filterLedgerMoneyFlowTransactions(
    transactions,
    accounts,
    []
  );

  assert.deepEqual(
    filtered.map(tx => [tx.id, tx.account_name]),
    [
      [1, 'Checking'],
      [2, 'Brokerage'],
      [3, 'Foreign Cash'],
    ]
  );
});

test('limits money flow transactions to selected accounts when provided', () => {
  const transactions = [
    {
      ...baseTransaction,
      id: 1,
      account_id: 1,
      type: 'Deposit',
      amount: '1000.00',
    },
    {
      ...baseTransaction,
      id: 2,
      account_id: 2,
      type: 'Dividend',
      amount: '50.00',
    },
  ];

  const filtered = filterLedgerMoneyFlowTransactions(
    transactions,
    accounts,
    [2]
  );

  assert.deepEqual(filtered.map(tx => tx.id), [2]);
});
