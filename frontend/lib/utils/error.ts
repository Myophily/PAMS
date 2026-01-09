/**
 * Pydantic validation error structure from FastAPI
 */
export interface PydanticValidationError {
  type: string;
  loc: (string | number)[];
  msg: string;
  input?: unknown;
  ctx?: Record<string, unknown>;
}

/**
 * Backend error response structure
 */
export interface BackendErrorResponse {
  detail: string | PydanticValidationError[] | Record<string, unknown>;
}

/**
 * Extracts a user-friendly error message from various error response formats.
 *
 * Handles:
 * - Pydantic validation errors (array of error objects)
 * - Simple string error messages
 * - Error objects with message properties
 * - Unknown error types with fallback
 *
 * @param error - The error response from the backend
 * @param fallbackMessage - Default message if extraction fails
 * @returns A human-readable error message
 */
export function extractErrorMessage(
  error: unknown,
  fallbackMessage: string = 'An unexpected error occurred'
): string {
  // Case 1: Error is a string (simple message)
  if (typeof error === 'string') {
    return error;
  }

  // Case 2: Error is an object
  if (error && typeof error === 'object') {
    const errorObj = error as Record<string, unknown>;

    // Case 2a: Pydantic validation error array
    if (Array.isArray(errorObj.detail)) {
      const firstError = errorObj.detail[0];
      if (firstError && typeof firstError === 'object') {
        const validationError = firstError as Record<string, unknown>;

        // Extract the error message
        const msg = validationError.msg as string;

        // Include the field location for context
        const loc = validationError.loc;
        if (Array.isArray(loc) && loc.length > 0) {
          // Get the last part of the location path (the actual field name)
          const fieldName = loc[loc.length - 1];
          return `${fieldName}: ${msg}`;
        }

        return msg || fallbackMessage;
      }
      // If detail array exists but is empty or malformed
      return fallbackMessage;
    }

    // Case 2b: Simple string detail property
    if (typeof errorObj.detail === 'string') {
      return errorObj.detail;
    }

    // Case 2c: Object with message property
    if (typeof errorObj.message === 'string') {
      return errorObj.message;
    }

    // Case 2d: Object with msg property (single validation error)
    if (typeof errorObj.msg === 'string') {
      return errorObj.msg;
    }
  }

  // Case 3: Fallback for unknown formats
  return fallbackMessage;
}
