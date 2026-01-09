import { describe, test, expect } from '@jest/globals';
import { extractErrorMessage } from './error';

describe('extractErrorMessage', () => {
  test('handles string error detail', () => {
    expect(extractErrorMessage({ detail: 'Simple error' }))
      .toBe('Simple error');
  });

  test('handles Pydantic validation error array with field name', () => {
    const error = {
      detail: [
        {
          type: 'value_error',
          loc: ['body', 'initial_holdings', 0, 'price_currency'],
          msg: 'price_currency should not be provided for currency ticker USD',
          input: {}
        }
      ]
    };
    expect(extractErrorMessage(error))
      .toBe('price_currency: price_currency should not be provided for currency ticker USD');
  });

  test('handles Pydantic validation error without location', () => {
    const error = {
      detail: [
        {
          type: 'value_error',
          loc: [],
          msg: 'Invalid request',
        }
      ]
    };
    expect(extractErrorMessage(error))
      .toBe('Invalid request');
  });

  test('handles empty validation error array', () => {
    expect(extractErrorMessage({ detail: [] }, 'Default'))
      .toBe('Default');
  });

  test('handles error with message property', () => {
    expect(extractErrorMessage({ message: 'Error message' }))
      .toBe('Error message');
  });

  test('handles unknown error format', () => {
    expect(extractErrorMessage({ random: 'data' }, 'Fallback'))
      .toBe('Fallback');
  });

  test('handles string input', () => {
    expect(extractErrorMessage('Plain string error'))
      .toBe('Plain string error');
  });

  test('handles null/undefined', () => {
    expect(extractErrorMessage(null, 'Fallback'))
      .toBe('Fallback');
    expect(extractErrorMessage(undefined, 'Fallback'))
      .toBe('Fallback');
  });
});
