'use client';

import Link from 'next/link';
import { ReactNode } from 'react';

import { ErrorAlert } from '@/components/base/error-alert';
import { isAdminRole, useAuthStore } from '@/stores/auth-store';

type AdminOnlyProps = {
  children: ReactNode;
};

export function AdminOnly({ children }: AdminOnlyProps) {
  const role = useAuthStore((state) => state.user?.role);
  if (!isAdminRole(role)) {
    return (
      <ErrorAlert
        title='无权访问管理后台'
        message={
          <span>
            当前账号角色为只读业务角色，请联系管理员分配权限，或返回
            <Link href='/' className='ml-1 underline underline-offset-2'>
              首页
            </Link>
            。
          </span>
        }
      />
    );
  }
  return <>{children}</>;
}
