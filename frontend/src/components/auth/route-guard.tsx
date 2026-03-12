'use client';

import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import type { Route } from 'next';
import type { ReadonlyURLSearchParams } from 'next/navigation';
import { ReactNode, useEffect } from 'react';

import { useAuthStore } from '@/stores/auth-store';

type RouteGuardProps = {
  children: ReactNode;
};

function buildLoginRedirect(pathname: string, searchParams: ReadonlyURLSearchParams | null): string {
  const query = searchParams?.toString();
  const rawPath = query ? `${pathname}?${query}` : pathname;
  const redirect = encodeURIComponent(rawPath);
  return `/login?redirect=${redirect}`;
}

export function RouteGuard({ children }: RouteGuardProps) {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const router = useRouter();
  const user = useAuthStore((state) => state.user);
  const hasBootstrapped = useAuthStore((state) => state.hasBootstrapped);
  const isBootstrapping = useAuthStore((state) => state.isBootstrapping);

  const isPublicRoute = pathname === '/login';
  const isAuthenticated = Boolean(user);

  useEffect(() => {
    if (!hasBootstrapped || isBootstrapping) return;

    if (!isAuthenticated && !isPublicRoute) {
      router.replace(buildLoginRedirect(pathname, searchParams) as Route);
      return;
    }

    if (isAuthenticated && isPublicRoute) {
      const target = searchParams?.get('redirect') || '/';
      router.replace(target as Route);
    }
  }, [hasBootstrapped, isAuthenticated, isBootstrapping, isPublicRoute, pathname, router, searchParams]);

  if (!hasBootstrapped || isBootstrapping) {
    return (
      <div className='flex min-h-screen items-center justify-center bg-panel text-sm text-muted'>
        正在检查登录状态...
      </div>
    );
  }

  if (!isAuthenticated && !isPublicRoute) return null;
  if (isAuthenticated && isPublicRoute) return null;

  return <>{children}</>;
}
