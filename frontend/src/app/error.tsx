'use client';

import Link from 'next/link';
import { useEffect } from 'react';

type ErrorPageProps = {
  error: Error & { digest?: string };
  reset: () => void;
};

export default function ErrorPage({ error, reset }: ErrorPageProps) {
  useEffect(() => {
    // Keep boundary observable in browser console for local troubleshooting.
    console.error(error);
  }, [error]);

  return (
    <main className='mx-auto flex min-h-screen w-full max-w-3xl items-center justify-center px-6'>
      <section className='w-full rounded-card border border-red-200 bg-red-50 p-6 shadow-panel'>
        <h1 className='text-lg font-semibold text-danger'>页面发生异常</h1>
        <p className='mt-2 text-sm text-muted'>请重试当前操作；若问题持续，请返回新建预审页重新发起任务。</p>
        <div className='mt-4 flex flex-wrap gap-2'>
          <button
            type='button'
            onClick={reset}
            className='rounded-md bg-black px-4 py-2 text-sm font-medium text-white'
          >
            重试
          </button>
          <Link
            href='/prereview/new'
            className='rounded-md border border-black/20 bg-white px-4 py-2 text-sm font-medium'
          >
            返回新建页
          </Link>
        </div>
      </section>
    </main>
  );
}
