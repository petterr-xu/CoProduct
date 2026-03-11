'use client';

import { useState } from 'react';

import { ErrorAlert } from '@/components/base/error-alert';
import { LoadingSkeleton } from '@/components/base/loading-skeleton';
import { SubmitButton } from '@/components/base/submit-button';
import { HistoryList } from '@/components/business/history-list';
import { useHistoryList } from '@/hooks/use-prereview-api';
import { getApiErrorMessage } from '@/lib/api-client';
import { CapabilityStatus } from '@/types';

export function HistoryView() {
  const [keyword, setKeyword] = useState('');
  const [capabilityStatus, setCapabilityStatus] = useState<CapabilityStatus | ''>('');
  const [page, setPage] = useState(1);
  const pageSize = 20;

  const query = useHistoryList({
    keyword: keyword || undefined,
    capabilityStatus: capabilityStatus || undefined,
    page,
    pageSize
  });

  return (
    <div className='space-y-4'>
      <form
        className='grid gap-3 rounded-card border border-black/10 bg-panel p-4 md:grid-cols-[1fr_220px_auto]'
        onSubmit={(e) => {
          e.preventDefault();
          setPage(1);
          void query.refetch();
        }}
      >
        <input
          className='w-full rounded-md border border-black/20 bg-white px-3 py-2 text-sm outline-none focus:border-black/50'
          placeholder='搜索需求关键字'
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
        />
        <select
          className='rounded-md border border-black/20 bg-white px-3 py-2 text-sm outline-none focus:border-black/50'
          value={capabilityStatus}
          onChange={(e) => setCapabilityStatus(e.target.value as CapabilityStatus | '')}
        >
          <option value=''>全部状态</option>
          <option value='SUPPORTED'>SUPPORTED</option>
          <option value='PARTIALLY_SUPPORTED'>PARTIALLY_SUPPORTED</option>
          <option value='NOT_SUPPORTED'>NOT_SUPPORTED</option>
          <option value='NEED_MORE_INFO'>NEED_MORE_INFO</option>
        </select>
        <SubmitButton type='submit'>查询</SubmitButton>
      </form>

      {query.isLoading ? <LoadingSkeleton /> : null}
      {query.error ? <ErrorAlert message={getApiErrorMessage(query.error)} /> : null}
      {query.data ? <HistoryList items={query.data.items} /> : null}

      <div className='flex items-center justify-between text-sm text-muted'>
        <span>
          共 {query.data?.total ?? 0} 条 · 第 {query.data?.page ?? 1} 页
        </span>
        <div className='flex items-center gap-2'>
          <button
            className='rounded border border-black/20 px-2 py-1 disabled:opacity-50'
            disabled={page <= 1}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
          >
            上一页
          </button>
          <button
            className='rounded border border-black/20 px-2 py-1 disabled:opacity-50'
            disabled={(query.data?.items.length ?? 0) < pageSize}
            onClick={() => setPage((p) => p + 1)}
          >
            下一页
          </button>
        </div>
      </div>
    </div>
  );
}
