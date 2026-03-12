'use client';

import Link from 'next/link';

import { WriteAccess } from '@/components/auth/write-access';
import { EmptyState } from '@/components/base/empty-state';
import { ErrorAlert } from '@/components/base/error-alert';
import { LoadingSkeleton } from '@/components/base/loading-skeleton';
import { StatusBadge } from '@/components/base/status-badge';
import { getApiErrorMessage } from '@/lib/api-client';
import { formatDateTime } from '@/lib/utils';

import { useHistoryList } from '@/hooks/use-prereview-api';

export function HomeDashboard() {
  const recentQuery = useHistoryList({
    page: 1,
    pageSize: 5
  });

  return (
    <div className='space-y-5'>
      <section className='grid gap-4 md:grid-cols-2'>
        <WriteAccess
          fallback={
            <section className='rounded-card border border-black/10 bg-panel p-5 shadow-panel'>
              <h2 className='text-lg font-semibold'>发起新预审</h2>
              <p className='mt-2 text-sm text-muted'>当前账号为只读角色，无法发起新预审。</p>
            </section>
          }
        >
          <Link
            href='/prereview/new'
            className='rounded-card border border-black/10 bg-panel p-5 shadow-panel transition hover:-translate-y-0.5'
          >
            <h2 className='text-lg font-semibold'>发起新预审</h2>
            <p className='mt-2 text-sm text-muted'>提交需求描述、背景与附件，生成结构化预审结论。</p>
            <p className='mt-4 text-sm font-medium text-info'>进入新建页 →</p>
          </Link>
        </WriteAccess>

        <Link
          href='/history'
          className='rounded-card border border-black/10 bg-panel p-5 shadow-panel transition hover:-translate-y-0.5'
        >
          <h2 className='text-lg font-semibold'>查看历史记录</h2>
          <p className='mt-2 text-sm text-muted'>浏览历史会话，按关键字和能力判断快速筛选。</p>
          <p className='mt-4 text-sm font-medium text-info'>进入历史页 →</p>
        </Link>
      </section>

      <section className='rounded-card border border-black/10 bg-panel p-4 shadow-panel'>
        <div className='mb-3 flex items-center justify-between gap-2'>
          <h2 className='text-base font-semibold'>最近预审会话</h2>
          <Link href='/history' className='text-xs text-info underline-offset-2 hover:underline'>
            查看全部
          </Link>
        </div>

        {recentQuery.isLoading ? <LoadingSkeleton /> : null}
        {recentQuery.error ? <ErrorAlert message={getApiErrorMessage(recentQuery.error)} /> : null}

        {recentQuery.data && recentQuery.data.items.length === 0 ? (
          <EmptyState title='暂无历史记录' description='先发起一个预审任务，这里会显示最近会话。' />
        ) : null}

        {recentQuery.data && recentQuery.data.items.length > 0 ? (
          <ul className='space-y-2'>
            {recentQuery.data.items.map((item) => (
              <li key={`${item.sessionId}-${item.version}`} className='rounded-md border border-black/10 bg-white px-3 py-2'>
                <div className='flex flex-wrap items-center justify-between gap-2'>
                  <Link href={`/prereview/${item.sessionId}`} className='text-sm font-medium hover:underline'>
                    {item.requestText || '未命名需求'}
                  </Link>
                  <span className='text-xs text-muted'>v{item.version}</span>
                </div>
                <div className='mt-2 flex flex-wrap items-center gap-2 text-xs text-muted'>
                  <StatusBadge status={item.capabilityStatus} />
                  <span>{formatDateTime(item.createdAt)}</span>
                </div>
              </li>
            ))}
          </ul>
        ) : null}
      </section>
    </div>
  );
}
