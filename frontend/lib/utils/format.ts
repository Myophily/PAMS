import { parseDecimal } from './decimal';

/**
 * Format a currency amount with locale-specific formatting.
 *
 * @param amount - Numeric value (number or DecimalString from API)
 * @param currency - Currency code ('KRW' | 'USD')
 * @param isHidden - Whether to hide the value for privacy
 * @returns Formatted currency string (e.g., "₩1,234,567" or "$1,234.56")
 */
export function formatCurrency(
  amount: number | string,
  currency: 'KRW' | 'USD',
  isHidden: boolean = false
): string {
  if (isHidden) return '••••••••';

  const numValue = parseDecimal(amount);

  return new Intl.NumberFormat('ko-KR', {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: currency === 'KRW' ? 0 : 2,
    maximumFractionDigits: currency === 'KRW' ? 0 : 2,
  }).format(numValue);
}

/**
 * Format a percentage value with sign and precision.
 *
 * @param value - Numeric value (number or DecimalString from API)
 * @param decimals - Number of decimal places (default: 2)
 * @returns Formatted percent string (e.g., "+5.25%" or "-3.14%")
 */
export function formatPercent(value: number | string, decimals: number = 2): string {
  const numValue = parseDecimal(value);
  return `${numValue >= 0 ? '+' : ''}${numValue.toFixed(decimals)}%`;
}

export function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
}

/**
 * Format a number with locale-specific thousands separators.
 *
 * @param value - Numeric value (number or DecimalString from API)
 * @param decimals - Number of decimal places (default: 0)
 * @returns Formatted number string (e.g., "1,234" or "1,234.56")
 */
export function formatNumber(value: number | string, decimals: number = 0): string {
  const numValue = parseDecimal(value);
  return numValue.toLocaleString('ko-KR', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

export function formatShortDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  });
}
