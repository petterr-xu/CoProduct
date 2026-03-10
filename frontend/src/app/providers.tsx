'use client';

import { QueryClientProvider } from '@tanstack/react-query';
import { ReactNode, useState } from 'react';

import { createQueryClient } from '@/lib/query-client';

type Props = {
  children: ReactNode;
};

export function Providers({ children }: Props) {
  const [queryClient] = useState(() => createQueryClient());
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}
