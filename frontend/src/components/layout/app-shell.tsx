'use client';

import type { Route } from 'next';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { ReactNode, useMemo, useState } from 'react';

import { authClient } from '@/lib/auth-client';
import { cn } from '@/lib/utils';
import { isWriteRole, useAuthStore } from '@/stores/auth-store';

type AppShellProps = {
  children: ReactNode;
};

type NavItem = {
  href: Route;
  label: string;
  isActive: (pathname: string) => boolean;
};

export function AppShell({ children }: AppShellProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, clearSession } = useAuthStore((state) => ({
    user: state.user,
    clearSession: state.clearSession
  }));
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  const isLoginRoute = pathname === '/login';
  const navItems = useMemo(() => {
    const base: NavItem[] = [
      {
        href: '/',
        label: '首页',
        isActive: (name) => name === '/'
      },
      {
        href: '/history',
        label: '历史记录',
        isActive: (name) => name.startsWith('/history')
      }
    ];
    if (isWriteRole(user?.role)) {
      base.splice(1, 0, {
        href: '/prereview/new',
        label: '新建预审',
        isActive: (name) => name.startsWith('/prereview')
      });
    }
    return base;
  }, [user?.role]);

  if (isLoginRoute) {
    return <div className='min-h-screen'>{children}</div>;
  }

  return (
    <div className='min-h-screen'>
      <header className='border-b border-black/10 bg-panel/95 backdrop-blur'>
        <div className='mx-auto flex w-full max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-3 md:px-6'>
          <Link href='/' className='text-base font-semibold tracking-tight'>
            CoProduct
          </Link>
          <nav className='flex flex-wrap items-center gap-2'>
            {navItems.map((item) => {
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
            {user ? (
              <div className='ml-1 flex items-center gap-2 rounded-md border border-black/15 bg-white px-2.5 py-1.5 text-xs text-muted'>
                <span>{user.displayName}</span>
                <span className='rounded border border-black/10 bg-panel px-1.5 py-0.5 text-[10px] text-ink'>{user.role}</span>
                <button
                  type='button'
                  disabled={isLoggingOut}
                  className='rounded border border-black/20 px-2 py-0.5 text-[11px] text-ink disabled:opacity-60'
                  onClick={async () => {
                    if (isLoggingOut) return;
                    setIsLoggingOut(true);
                    try {
                      await authClient.logout();
                    } catch {
                      // ignore logout transport errors and enforce local sign-out
                    } finally {
                      clearSession();
                      setIsLoggingOut(false);
                      router.replace('/login' as Route);
                    }
                  }}
                >
                  {isLoggingOut ? '退出中' : '退出'}
                </button>
              </div>
            ) : null}
          </nav>
        </div>
      </header>
      {children}
    </div>
  );
}
