'use client';

import { useState, useEffect } from 'react';

export function usePrivacyToggle() {
  const [isHidden, setIsHidden] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const saved = localStorage.getItem('pam_hide_amounts');
    if (saved === 'true') {
      setIsHidden(true);
    }
  }, []);

  const toggle = () => {
    const newValue = !isHidden;
    setIsHidden(newValue);
    if (mounted) {
      localStorage.setItem('pam_hide_amounts', newValue.toString());
    }
  };

  return { isHidden, toggle };
}
