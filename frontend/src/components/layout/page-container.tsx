import { ReactNode } from 'react';

type Props = {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  children: ReactNode;
};

export function PageContainer({ title, subtitle, actions, children }: Props) {
  return (
    <main className='mx-auto flex w-full max-w-6xl flex-col gap-6 px-4 py-8 md:px-6'>
      <header className='flex flex-col gap-3 border-b border-black/10 pb-4 md:flex-row md:items-end md:justify-between'>
        <div>
          <h1 className='text-2xl font-semibold tracking-tight'>{title}</h1>
          {subtitle ? <p className='mt-1 text-sm text-muted'>{subtitle}</p> : null}
        </div>
        {actions ? <div className='flex items-center gap-2'>{actions}</div> : null}
      </header>
      {children}
    </main>
  );
}
