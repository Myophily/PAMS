'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

export function Navigation() {
  const pathname = usePathname();

  const isActive = (path: string) => {
    if (path === '/' && pathname === '/') return true;
    if (path !== '/' && pathname.startsWith(path)) return true;
    return false;
  };

  const linkClass = (path: string) =>
    `px-4 py-2 rounded transition ${
      isActive(path)
        ? 'bg-gray-700 text-white'
        : 'text-gray-300 hover:bg-gray-700 hover:text-white'
    }`;

  return (
    <nav className="bg-gray-800 text-white p-4">
      <div className="container mx-auto flex items-center justify-between">
        <Link href="/">
          <h1 className="text-xl font-bold cursor-pointer hover:text-gray-300 transition">
            Personal Asset Manager
          </h1>
        </Link>
        <div className="flex gap-2">
          <Link href="/" className={linkClass('/')}>
            Dashboard
          </Link>
          <Link href="/accounts" className={linkClass('/accounts')}>
            Accounts
          </Link>
          <Link href="/recurring-transfers" className={linkClass('/recurring-transfers')}>
            Recurring Transfers
          </Link>
        </div>
      </div>
    </nav>
  );
}
