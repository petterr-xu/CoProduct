import type { Metadata } from 'next';
import type { ReactNode } from 'react';

import { Providers } from '@/app/providers';
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
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
