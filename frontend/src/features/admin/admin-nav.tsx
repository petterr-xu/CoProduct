'use client';

import Link from 'next/link';
import type { Route } from 'next';
import { usePathname } from 'next/navigation';

import { cn } from '@/lib/utils';

const ADMIN_LINKS = [
  { href: '/admin/users', label: '用户管理' },
  { href: '/admin/api-keys', label: 'API Key 管理' },
  { href: '/admin/audit-logs', label: '审计日志' }
] as const;

export function AdminNav() {
  const pathname = usePathname();

  return (
    <div className='flex flex-wrap items-center gap-2'>
      {ADMIN_LINKS.map((item) => {
        const active = pathname.startsWith(item.href);
        return (
          <Link
            key={item.href}
            href={item.href as Route}
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
    </div>
  );
}
