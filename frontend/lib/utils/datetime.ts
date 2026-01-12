/**
 * Datetime utility functions for handling datetime-local inputs and display.
 * All times are displayed in Korea (Seoul) timezone (KST).
 */

import { formatInTimeZone } from 'date-fns-tz';

// Constant for Seoul timezone
const SEOUL_TZ = 'Asia/Seoul';

/**
 * Get current datetime in format for datetime-local input (KST).
 * Returns: "2024-01-15T14:30"
 *
 * Always returns KST time regardless of browser timezone.
 */
export function getCurrentDateTimeLocal(): string {
  return formatInTimeZone(new Date(), SEOUL_TZ, "yyyy-MM-dd'T'HH:mm");
}

/**
 * Format datetime for display in KST: "Jan 15, 2024 2:30 PM KST"
 *
 * @param isoString - ISO datetime string from backend
 * @returns Formatted datetime string in KST
 */
export function formatDateTime(isoString: string): string {
  const dt = new Date(isoString);
  return formatInTimeZone(dt, SEOUL_TZ, 'MMM d, yyyy h:mm a') + ' KST';
}

/**
 * Format date only in KST: "Jan 15, 2024"
 *
 * @param isoString - ISO datetime string from backend
 * @returns Formatted date string
 */
export function formatDate(isoString: string): string {
  const dt = new Date(isoString);
  return formatInTimeZone(dt, SEOUL_TZ, 'MMM d, yyyy');
}

/**
 * Format compact datetime for ledger/timeline: "2024-01-15 14:30"
 *
 * @param isoString - ISO datetime string from backend
 * @returns Formatted datetime in KST without timezone suffix
 */
export function formatDateTimeCompact(isoString: string): string {
  const dt = new Date(isoString);
  return formatInTimeZone(dt, SEOUL_TZ, 'yyyy-MM-dd HH:mm');
}
