'use client';

import { useRouter, useSearchParams, usePathname } from 'next/navigation';

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
    <div className="border-b border-gray-200">
      <nav className="-mb-px flex space-x-8">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => handleTabChange(tab.key)}
            className={`py-4 px-1 border-b-2 font-medium text-sm transition ${
              activeTab === tab.key
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </nav>
    </div>
  );
}
