'use client';

import { ReactNode } from 'react';

import { isWriteRole, useAuthStore } from '@/stores/auth-store';

type WriteAccessProps = {
  children: ReactNode;
  fallback?: ReactNode;
};

export function WriteAccess({ children, fallback = null }: WriteAccessProps) {
  const role = useAuthStore((state) => state.user?.role);
  if (!isWriteRole(role)) {
    return <>{fallback}</>;
  }
  return <>{children}</>;
}

