'use client';

import { useState } from 'react';

import { Menu, X } from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

const NAV_ITEMS = [
  { href: '/', label: 'Dashboard' },
  { href: '/accounts', label: 'Accounts' },
  { href: '/ledger', label: 'Ledger' },
  { href: '/recurring-transfers', label: 'Recurring' },
];

export function Navigation() {
  const pathname = usePathname();
  const [isOpen, setIsOpen] = useState(false);

  const isActive = (path: string) => {
    if (path === '/' && pathname === '/') return true;
    if (path !== '/' && pathname.startsWith(path)) return true;
    return false;
  };

  const linkClass = (path: string) =>
    `rounded-full px-3 py-2 text-sm font-medium tracking-[0] transition ${
      isActive(path)
        ? 'bg-[var(--surface-elevated)] text-[var(--ink)]'
        : 'text-[var(--charcoal)] hover:bg-[var(--surface-card)] hover:text-[var(--ink)]'
    }`;

  return (
    <nav className="sticky top-0 z-40 border-b border-[var(--hairline)] bg-[var(--canvas)]/95 text-[var(--body)] backdrop-blur">
      <div className="mx-auto flex h-16 w-full max-w-[1200px] items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link
          href="/"
          className="group flex items-center gap-3"
          onClick={() => setIsOpen(false)}
        >
          <span className="flex h-8 w-8 items-center justify-center rounded-full border border-[var(--hairline-strong)] bg-[var(--surface-card)] font-mono text-sm text-[var(--ink)]">
            P
          </span>
          <span className="font-semibold tracking-[0] text-[var(--ink)] transition group-hover:text-[var(--primary)]">
            PAMS
          </span>
        </Link>

        <div className="hidden items-center gap-1 lg:flex">
          {NAV_ITEMS.map((item) => (
            <Link key={item.href} href={item.href} className={linkClass(item.href)}>
              {item.label}
            </Link>
          ))}
        </div>

        <button
          type="button"
          className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-[var(--hairline-strong)] bg-[var(--surface-card)] text-[var(--ink)] transition hover:bg-[var(--surface-elevated)] lg:hidden"
          onClick={() => setIsOpen((current) => !current)}
          aria-label="Toggle navigation"
          aria-expanded={isOpen}
        >
          {isOpen ? <X size={18} /> : <Menu size={18} />}
        </button>
      </div>

      {isOpen && (
        <div className="border-t border-[var(--hairline)] bg-[var(--canvas)] px-4 py-3 lg:hidden">
          <div className="mx-auto grid max-w-[1200px] gap-2">
            {NAV_ITEMS.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={linkClass(item.href)}
                onClick={() => setIsOpen(false)}
              >
                {item.label}
              </Link>
            ))}
          </div>
        </div>
      )}
    </nav>
  );
}
