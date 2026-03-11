'use client';

import type { Route } from 'next';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ReactNode } from 'react';

import { cn } from '@/lib/utils';

type AppShellProps = {
  children: ReactNode;
};

type NavItem = {
  href: Route;
  label: string;
  isActive: (pathname: string) => boolean;
};

const NAV_ITEMS: NavItem[] = [
  {
    href: '/',
    label: '首页',
    isActive: (pathname) => pathname === '/'
  },
  {
    href: '/prereview/new',
    label: '新建预审',
    isActive: (pathname) => pathname.startsWith('/prereview')
  },
  {
    href: '/history',
    label: '历史记录',
    isActive: (pathname) => pathname.startsWith('/history')
  }
];

export function AppShell({ children }: AppShellProps) {
  const pathname = usePathname();

  return (
    <div className='min-h-screen'>
      <header className='border-b border-black/10 bg-panel/95 backdrop-blur'>
        <div className='mx-auto flex w-full max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-3 md:px-6'>
          <Link href='/' className='text-base font-semibold tracking-tight'>
            CoProduct
          </Link>
          <nav className='flex flex-wrap items-center gap-2'>
            {NAV_ITEMS.map((item) => {
              const active = item.isActive(pathname);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    'rounded-md border px-3 py-1.5 text-sm transition',
                    active
                      ? 'border-black bg-black text-white'
                      : 'border-black/20 bg-white text-ink hover:border-black/40'
                  )}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>
      </header>
      {children}
    </div>
  );
}
