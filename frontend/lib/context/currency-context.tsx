'use client';

import { createContext, useContext, useSyncExternalStore } from 'react';

type Currency = 'KRW' | 'USD';
const CURRENCY_STORAGE_KEY = 'pam_currency';
const CURRENCY_CHANGE_EVENT = 'pam_currency_change';

interface CurrencyContextType {
  currency: Currency;
  setCurrency: (c: Currency) => void;
  toggleCurrency: () => void;
}

const CurrencyContext = createContext<CurrencyContextType>({
  currency: 'KRW',
  setCurrency: () => {},
  toggleCurrency: () => {},
});

function readCurrency(): Currency {
  if (typeof window === 'undefined') return 'KRW';

  const saved = window.localStorage.getItem(CURRENCY_STORAGE_KEY);
  return saved === 'KRW' || saved === 'USD' ? saved : 'KRW';
}

function subscribeCurrency(callback: () => void): () => void {
  window.addEventListener('storage', callback);
  window.addEventListener(CURRENCY_CHANGE_EVENT, callback);

  return () => {
    window.removeEventListener('storage', callback);
    window.removeEventListener(CURRENCY_CHANGE_EVENT, callback);
  };
}

export function CurrencyProvider({ children }: { children: React.ReactNode }) {
  const currency = useSyncExternalStore<Currency>(
    subscribeCurrency,
    readCurrency,
    () => 'KRW',
  );

  const updateCurrency = (c: Currency) => {
    window.localStorage.setItem(CURRENCY_STORAGE_KEY, c);
    window.dispatchEvent(new Event(CURRENCY_CHANGE_EVENT));
  };

  const toggleCurrency = () => {
    updateCurrency(currency === 'KRW' ? 'USD' : 'KRW');
  };

  return (
    <CurrencyContext.Provider
      value={{ currency, setCurrency: updateCurrency, toggleCurrency }}
    >
      {children}
    </CurrencyContext.Provider>
  );
}

export const useCurrency = () => useContext(CurrencyContext);
