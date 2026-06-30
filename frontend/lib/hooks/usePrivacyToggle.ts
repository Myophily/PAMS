'use client';

import { useSyncExternalStore } from 'react';

const PRIVACY_STORAGE_KEY = 'pam_hide_amounts';
const PRIVACY_CHANGE_EVENT = 'pam_hide_amounts_change';

function readPrivacySetting(): boolean {
  if (typeof window === 'undefined') return false;
  return window.localStorage.getItem(PRIVACY_STORAGE_KEY) === 'true';
}

function subscribePrivacySetting(callback: () => void): () => void {
  window.addEventListener('storage', callback);
  window.addEventListener(PRIVACY_CHANGE_EVENT, callback);

  return () => {
    window.removeEventListener('storage', callback);
    window.removeEventListener(PRIVACY_CHANGE_EVENT, callback);
  };
}

export function usePrivacyToggle() {
  const isHidden = useSyncExternalStore(
    subscribePrivacySetting,
    readPrivacySetting,
    () => false,
  );

  const toggle = () => {
    const newValue = !isHidden;
    window.localStorage.setItem(PRIVACY_STORAGE_KEY, newValue.toString());
    window.dispatchEvent(new Event(PRIVACY_CHANGE_EVENT));
  };

  return { isHidden, toggle };
}
