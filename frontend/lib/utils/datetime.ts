/**
 * Datetime utility functions for handling datetime-local inputs and display.
 */

/**
 * Get current datetime in format for datetime-local input: "2024-01-15T14:30"
 */
export function getCurrentDateTimeLocal(): string {
  return new Date().toISOString().slice(0, 16);
}

/**
 * Format datetime for display: "Jan 15, 2024 2:30 PM"
 */
export function formatDateTime(isoString: string): string {
  const dt = new Date(isoString);
  return dt.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * Format date only: "Jan 15, 2024"
 */
export function formatDate(isoString: string): string {
  const dt = new Date(isoString);
  return dt.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}
