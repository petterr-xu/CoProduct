'use client';

import { useState } from 'react';

import { EmptyState } from '@/components/base/empty-state';
import { ErrorAlert } from '@/components/base/error-alert';
import { LoadingSkeleton } from '@/components/base/loading-skeleton';
import { SubmitButton } from '@/components/base/submit-button';
import { useAdminAuditLogs } from '@/hooks/use-admin-api';
import { getApiErrorMessage } from '@/lib/api-client';
import { formatDateTime } from '@/lib/utils';

export function AuditLogsAdminView() {
  const [actorInput, setActorInput] = useState('');
  const [actionInput, setActionInput] = useState('');

  const [actorUserId, setActorUserId] = useState('');
  const [action, setAction] = useState('');

  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);

  const listQuery = useAdminAuditLogs({
    actorUserId: actorUserId || undefined,
    action: action || undefined,
    page,
    pageSize
  });

  const total = listQuery.data?.total ?? 0;
  const currentPage = listQuery.data?.page ?? page;

  return (
    <div className='space-y-4'>
      <section className='rounded-card border border-black/10 bg-panel p-4'>
        <h2 className='text-sm font-semibold'>审计日志筛选</h2>
        <form
          className='mt-3 grid gap-3 md:grid-cols-[1fr_1fr_auto]'
          onSubmit={(event) => {
            event.preventDefault();
            setActorUserId(actorInput.trim());
            setAction(actionInput.trim());
            setPage(1);
          }}
        >
          <input
            placeholder='按执行人用户 ID 过滤'
            className='rounded-md border border-black/20 bg-white px-3 py-2 text-sm outline-none focus:border-black/50'
            value={actorInput}
            onChange={(event) => setActorInput(event.target.value)}
          />
          <input
            placeholder='按动作过滤（如 user.create）'
            className='rounded-md border border-black/20 bg-white px-3 py-2 text-sm outline-none focus:border-black/50'
            value={actionInput}
            onChange={(event) => setActionInput(event.target.value)}
          />
          <SubmitButton type='submit'>查询</SubmitButton>
        </form>
      </section>

      {listQuery.error ? <ErrorAlert message={getApiErrorMessage(listQuery.error)} /> : null}
      {listQuery.isLoading ? <LoadingSkeleton /> : null}

      {listQuery.data && listQuery.data.items.length === 0 ? (
        <EmptyState title='暂无审计日志' description='当前筛选条件下没有匹配记录。' />
      ) : null}

      {listQuery.data && listQuery.data.items.length > 0 ? (
        <section className='overflow-x-auto rounded-card border border-black/10 bg-white'>
          <table className='min-w-full divide-y divide-black/10 text-sm'>
            <thead className='bg-panel text-left text-xs text-muted'>
              <tr>
                <th className='px-3 py-2'>时间</th>
                <th className='px-3 py-2'>执行人</th>
                <th className='px-3 py-2'>动作</th>
                <th className='px-3 py-2'>目标</th>
                <th className='px-3 py-2'>结果</th>
              </tr>
            </thead>
            <tbody className='divide-y divide-black/10'>
              {listQuery.data.items.map((item) => (
                <tr key={item.id}>
                  <td className='px-3 py-2 text-xs'>{formatDateTime(item.createdAt)}</td>
                  <td className='px-3 py-2 text-xs'>
                    <p>{item.actorUserId || '-'}</p>
                    <p className='text-muted'>{item.actorEmail || '-'}</p>
                  </td>
                  <td className='px-3 py-2 text-xs'>{item.action || '-'}</td>
                  <td className='px-3 py-2 text-xs'>
                    {item.targetType || '-'}
                    {item.targetId ? ` / ${item.targetId}` : ''}
                  </td>
                  <td className='px-3 py-2 text-xs'>{item.result || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      ) : null}

      <div className='flex items-center justify-between text-sm text-muted'>
        <span>
          共 {total} 条 · 第 {currentPage} 页
        </span>
        <div className='flex items-center gap-2'>
          <select
            className='rounded border border-black/20 px-2 py-1 text-xs'
            value={pageSize}
            onChange={(event) => {
              const nextSize = Number(event.target.value);
              setPageSize(nextSize);
              setPage(1);
            }}
          >
            <option value={20}>20 / 页</option>
            <option value={50}>50 / 页</option>
            <option value={100}>100 / 页</option>
          </select>
          <button
            type='button'
            className='rounded border border-black/20 px-2 py-1 disabled:opacity-50'
            disabled={page <= 1}
            onClick={() => setPage((previous) => Math.max(1, previous - 1))}
          >
            上一页
          </button>
          <button
            type='button'
            className='rounded border border-black/20 px-2 py-1 disabled:opacity-50'
            disabled={total <= page * pageSize}
            onClick={() => setPage((previous) => previous + 1)}
          >
            下一页
          </button>
        </div>
      </div>
    </div>
  );
}
