import { ButtonHTMLAttributes } from 'react';

import { cn } from '@/lib/utils';

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  loading?: boolean;
};

export function SubmitButton({ loading, className, children, ...rest }: Props) {
  return (
    <button
      type='submit'
      className={cn(
        'inline-flex items-center justify-center rounded-md bg-black px-4 py-2 text-sm font-medium text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60',
        className
      )}
      disabled={loading || rest.disabled}
      {...rest}
    >
      {loading ? '处理中...' : children}
    </button>
  );
}
