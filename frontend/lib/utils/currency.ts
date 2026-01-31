/**
 * Currency ticker utilities matching backend currency_inference.py
 */

export const CURRENCY_TICKERS = [
  'KRW', 'USD', 'EUR', 'JPY', 'GBP', 'CHF', 'CNY', 'HKD', 'SGD'
] as const;

export type CurrencyTicker = typeof CURRENCY_TICKERS[number];

export const CURRENCY_SYMBOLS: Record<string, string> = {
  KRW: '₩',
  USD: '$',
  EUR: '€',
  JPY: '¥',
  GBP: '£',
  CHF: 'CHF',
  CNY: '¥',
  HKD: 'HK$',
  SGD: 'S$',
};

export const CURRENCY_NAMES: Record<string, string> = {
  KRW: 'Korean Won',
  USD: 'US Dollar',
  EUR: 'Euro',
  JPY: 'Japanese Yen',
  GBP: 'British Pound',
  CHF: 'Swiss Franc',
  CNY: 'Chinese Yuan',
  HKD: 'Hong Kong Dollar',
  SGD: 'Singapore Dollar',
};

export const KOREAN_BOND_TICKERS = ['S_D'] as const;

/**
 * Check if ticker is a currency code.
 */
export function isCurrencyTicker(ticker: string): boolean {
  if (!ticker) return false;

  const normalized = ticker.toUpperCase();

  // Legacy CASH support (deprecated)
  if (normalized === 'CASH') {
    console.warn('CASH ticker is deprecated. Use explicit currency codes (KRW, USD, etc.)');
    return true;
  }

  return CURRENCY_TICKERS.includes(normalized as CurrencyTicker);
}

/**
 * Get allowed ticker types for account type.
 */
export interface TickerConstraints {
  allowedTypes: 'currency-only' | 'non-krw-currency' | 'any';
  allowedTickers?: string[];  // Explicit whitelist
  disallowedTickers?: string[];  // Explicit blacklist
  requirePrice: (ticker: string) => boolean;
  placeholder: string;
  label: string;
}

export function getTickerConstraints(accountType: string): TickerConstraints {
  switch (accountType) {
    case 'Deposit':
    case 'Savings':
    case 'MoneyMarket':
      return {
        allowedTypes: 'currency-only',
        allowedTickers: ['KRW'],
        requirePrice: () => false,
        placeholder: 'KRW',
        label: 'Initial Balance (KRW)',
      };

    case 'ForeignCurrency':
      return {
        allowedTypes: 'non-krw-currency',
        allowedTickers: CURRENCY_TICKERS.filter(c => c !== 'KRW') as unknown as string[],
        requirePrice: () => false,
        placeholder: 'USD',
        label: 'Currency',
      };

    case 'Securities':
      return {
        allowedTypes: 'any',
        requirePrice: (ticker: string) => !isCurrencyTicker(ticker),
        placeholder: 'AAPL or KRW',
        label: 'Ticker',
      };

    default:
      throw new Error(`Unknown account type: ${accountType}`);
  }
}

/**
 * Validate ticker for account type.
 */
export function validateTickerForAccountType(
  ticker: string,
  accountType: string
): { valid: boolean; error?: string } {
  const constraints = getTickerConstraints(accountType);
  const normalized = ticker.toUpperCase();

  if (constraints.allowedTickers) {
    if (!constraints.allowedTickers.includes(normalized)) {
      return {
        valid: false,
        error: `${accountType} accounts can only hold: ${constraints.allowedTickers.join(', ')}`
      };
    }
  }

  if (constraints.disallowedTickers) {
    if (constraints.disallowedTickers.includes(normalized)) {
      return {
        valid: false,
        error: `${accountType} accounts cannot hold: ${normalized}`
      };
    }
  }

  return { valid: true };
}

/**
 * Format currency with symbol.
 */
export function formatCurrency(amount: number, currency: string): string {
  const symbol = CURRENCY_SYMBOLS[currency] || currency;

  if (currency === 'KRW' || currency === 'JPY') {
    // No decimal places for KRW/JPY
    return `${symbol}${amount.toLocaleString('en-US', { maximumFractionDigits: 0 })}`;
  }

  return `${symbol}${amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}
