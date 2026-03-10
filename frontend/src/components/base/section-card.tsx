import { ReactNode } from 'react';

import { cn } from '@/lib/utils';

type Props = {
  title: string;
  children: ReactNode;
  className?: string;
};

export function SectionCard({ title, children, className }: Props) {
  return (
    <section className={cn('rounded-card border border-black/10 bg-panel p-4 shadow-panel', className)}>
      <h2 className='mb-3 text-base font-semibold'>{title}</h2>
      {children}
    </section>
  );
}
