'use client';

import { createContext, useContext, useState, useEffect } from 'react';

type Currency = 'KRW' | 'USD';

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

export function CurrencyProvider({ children }: { children: React.ReactNode }) {
  const [currency, setCurrency] = useState<Currency>('KRW');
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const saved = localStorage.getItem('pam_currency') as Currency;
    if (saved && (saved === 'KRW' || saved === 'USD')) {
      setCurrency(saved);
    }
  }, []);

  const updateCurrency = (c: Currency) => {
    setCurrency(c);
    if (mounted) {
      localStorage.setItem('pam_currency', c);
    }
  };

  const toggleCurrency = () => {
    updateCurrency(currency === 'KRW' ? 'USD' : 'KRW');
  };

  return (
    <CurrencyContext.Provider value={{ currency, setCurrency: updateCurrency, toggleCurrency }}>
      {children}
    </CurrencyContext.Provider>
  );
}

export const useCurrency = () => useContext(CurrencyContext);
