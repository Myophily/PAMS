'use client';

import { usePathname, useRouter } from 'next/navigation';

interface TabNavigationProps {
  tabs: Array<{ key: string; label: string }>;
  activeTab: string;
}

export function TabNavigation({ tabs, activeTab }: TabNavigationProps) {
  const router = useRouter();
  const pathname = usePathname();

  const handleTabChange = (tabKey: string) => {
    if (tabKey === tabs[0].key) {
      // Default tab - remove query param
      router.push(pathname);
    } else {
      // Other tabs - add query param
      router.push(`${pathname}?tab=${tabKey}`);
    }
  };

  return (
    <div className="border-b border-[var(--hairline)] px-4">
      <nav className="flex gap-2 overflow-x-auto">
        {tabs.map((tab) => (
          <button
            type="button"
            key={tab.key}
            onClick={() => handleTabChange(tab.key)}
            className={`border-b-2 px-2 py-4 text-sm font-medium tracking-[0] transition ${
              activeTab === tab.key
                ? 'border-[var(--primary)] text-[var(--ink)]'
                : 'border-transparent text-[var(--charcoal)] hover:border-[var(--hairline-strong)] hover:text-[var(--ink)]'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </nav>
    </div>
  );
}
