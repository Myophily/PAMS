/**
 * Account Type Configuration
 *
 * Centralized configuration for account type-specific UI behavior.
 * This defines which tabs, actions, and features are available for each account type.
 */

export type AccountTab = 'holdings' | 'transactions' | 'analysis' | 'ledger';

export interface AccountTypeConfig {
  displayName: string;
  description: string;
  allowedTabs: AccountTab[];
  primaryActions: string[];
}

/**
 * Configuration mapping for each account type.
 *
 * Account Type Rules:
 * - Deposit: Cash-only operations, no holdings tracking needed
 * - Securities: Full investment tracking with holdings, transactions, and analysis
 * - ForeignCurrency: Multi-currency holdings with exchange capabilities
 * - MoneyMarket: Interest-earning accounts with transaction and analysis tracking
 */
export const ACCOUNT_TYPE_CONFIG: Record<string, AccountTypeConfig> = {
  Deposit: {
    displayName: 'Deposit Account',
    description: 'Daily spending and cash management',
    allowedTabs: ['transactions', 'ledger'],
    primaryActions: ['deposit', 'transfer', 'exchange'],
  },
  Securities: {
    displayName: 'Securities Account',
    description: 'Investment and stock trading',
    allowedTabs: ['holdings', 'transactions', 'analysis'],
    primaryActions: ['buy', 'sell', 'dividend', 'transfer'],
  },
  ForeignCurrency: {
    displayName: 'Foreign Currency Account',
    description: 'Multi-currency holdings',
    allowedTabs: ['holdings', 'transactions'],
    primaryActions: ['exchange'],  // Transfer removed - use Exchange with target account
  },
  MoneyMarket: {
    displayName: 'Money Market Fund',
    description: 'Interest-earning cash account',
    allowedTabs: ['transactions', 'ledger', 'analysis'],
    primaryActions: ['interest', 'transfer'],
  },
  Savings: {
    displayName: 'Savings Account',
    description: 'Interest-bearing savings account',
    allowedTabs: ['transactions', 'ledger', 'analysis'],
    primaryActions: ['deposit', 'interest', 'transfer'],
  },
};

/**
 * Get configuration for an account type.
 * Fallback to Deposit configuration if type not found.
 */
export function getAccountTypeConfig(accountType: string): AccountTypeConfig {
  return ACCOUNT_TYPE_CONFIG[accountType] || ACCOUNT_TYPE_CONFIG.Deposit;
}

/**
 * Check if a specific tab is allowed for an account type.
 */
export function isTabAllowed(
  accountType: string,
  tab: AccountTab
): boolean {
  const config = getAccountTypeConfig(accountType);
  return config.allowedTabs.includes(tab);
}

/**
 * Get all allowed tabs for an account type.
 */
export function getAllowedTabs(accountType: string): AccountTab[] {
  const config = getAccountTypeConfig(accountType);
  return config.allowedTabs;
}

/**
 * Get primary actions for an account type.
 */
export function getPrimaryActions(accountType: string): string[] {
  const config = getAccountTypeConfig(accountType);
  return config.primaryActions;
}

/**
 * Get display name for an account type.
 */
export function getAccountTypeDisplayName(accountType: string): string {
  const config = getAccountTypeConfig(accountType);
  return config.displayName;
}
