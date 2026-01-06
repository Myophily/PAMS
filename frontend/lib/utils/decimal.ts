/**
 * Utility functions for handling DecimalString values from the backend.
 *
 * Backend uses Python's Decimal type for precision, which Pydantic serializes
 * to JSON as strings to prevent floating-point errors.
 */

/**
 * Parse DecimalString or number to a number for calculations.
 *
 * @param value - DecimalString from API or a number
 * @returns Parsed number value, or 0 if invalid
 *
 * @example
 * parseDecimal("1234.56") // Returns 1234.56
 * parseDecimal(1234.56) // Returns 1234.56
 * parseDecimal("invalid") // Returns 0 (with console warning)
 */
export function parseDecimal(value: string | number): number {
  if (typeof value === 'number') return value;

  const parsed = parseFloat(value);
  if (isNaN(parsed)) {
    console.warn(`Invalid decimal string: "${value}", returning 0`);
    return 0;
  }

  return parsed;
}

/**
 * Format DecimalString or number for display with locale formatting.
 *
 * Equivalent to Number.toLocaleString() but works with string inputs.
 *
 * @param value - DecimalString from API or a number
 * @param options - Intl.NumberFormatOptions for formatting
 * @returns Formatted string with locale-specific thousands separators
 *
 * @example
 * formatDecimal("1234.56") // Returns "1,234.56"
 * formatDecimal("1000") // Returns "1,000"
 * formatDecimal("1234.5678", { maximumFractionDigits: 2 }) // Returns "1,234.57"
 */
export function formatDecimal(
  value: string | number,
  options?: Intl.NumberFormatOptions
): string {
  const num = parseDecimal(value);
  return num.toLocaleString('ko-KR', options);
}

/**
 * Check if DecimalString or number value is positive (>= 0).
 *
 * @param value - DecimalString from API or a number
 * @returns true if value >= 0, false otherwise
 *
 * @example
 * isPositive("10.5") // Returns true
 * isPositive("0") // Returns true
 * isPositive("-5") // Returns false
 */
export function isPositive(value: string | number): boolean {
  return parseDecimal(value) >= 0;
}

/**
 * Compare two DecimalString or number values.
 *
 * @param a - First value
 * @param b - Second value
 * @returns -1 if a < b, 0 if a === b, 1 if a > b
 *
 * @example
 * compareDecimal("10", "20") // Returns -1
 * compareDecimal("20", "10") // Returns 1
 * compareDecimal("10", "10") // Returns 0
 */
export function compareDecimal(
  a: string | number,
  b: string | number
): number {
  const numA = parseDecimal(a);
  const numB = parseDecimal(b);
  return numA < numB ? -1 : numA > numB ? 1 : 0;
}
