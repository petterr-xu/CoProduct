import type { Metadata } from 'next';
import type { ReactNode } from 'react';

import { Providers } from '@/app/providers';
import { RouteGuard } from '@/components/auth/route-guard';
import { AppShell } from '@/components/layout/app-shell';
import '@/styles/globals.css';

export const metadata: Metadata = {
  title: 'CoProduct',
  description: '需求预审平台'
};

type LayoutProps = {
  children: ReactNode;
};

export default function RootLayout({ children }: LayoutProps) {
  return (
    <html lang='zh-CN'>
      <body>
        <Providers>
          <RouteGuard>
            <AppShell>{children}</AppShell>
          </RouteGuard>
        </Providers>
      </body>
    </html>
  );
}
