'use client';

import { FormEvent, useMemo, useState } from 'react';

import { EmptyState } from '@/components/base/empty-state';
import { ErrorAlert } from '@/components/base/error-alert';
import { LoadingSkeleton } from '@/components/base/loading-skeleton';
import { SubmitButton } from '@/components/base/submit-button';
import { useAdminApiKeys, useAdminIssueApiKey, useAdminRevokeApiKey } from '@/hooks/use-admin-api';
import { getApiErrorMessage } from '@/lib/api-client';
import { API_KEY_STATUS_LABEL_MAP } from '@/lib/constants';
import { formatDateTime } from '@/lib/utils';
import { ApiKeyStatus, IssueApiKeyResponse } from '@/types';

const API_KEY_STATUS_OPTIONS: ApiKeyStatus[] = ['ACTIVE', 'REVOKED', 'EXPIRED'];

export function ApiKeysAdminView() {
  const [userIdInput, setUserIdInput] = useState('');
  const [statusInput, setStatusInput] = useState<ApiKeyStatus | ''>('');

  const [userId, setUserId] = useState('');
  const [status, setStatus] = useState<ApiKeyStatus | ''>('');

  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);

  const [issueForm, setIssueForm] = useState({
    userId: '',
    name: '',
    expiresAt: ''
  });
  const [latestIssuedKey, setLatestIssuedKey] = useState<IssueApiKeyResponse | null>(null);

  const listQuery = useAdminApiKeys({
    userId: userId || undefined,
    status: status || undefined,
    page,
    pageSize
  });
  const issueMutation = useAdminIssueApiKey();
  const revokeMutation = useAdminRevokeApiKey();

  const actionError = useMemo(() => issueMutation.error ?? revokeMutation.error, [issueMutation.error, revokeMutation.error]);
  const total = listQuery.data?.total ?? 0;
  const currentPage = listQuery.data?.page ?? page;

  async function onIssueKey(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedExpiresAt = issueForm.expiresAt.trim();
    const parsedExpiresAt = trimmedExpiresAt ? new Date(trimmedExpiresAt) : null;
    const expiresAt =
      parsedExpiresAt && !Number.isNaN(parsedExpiresAt.getTime()) ? parsedExpiresAt.toISOString() : undefined;
    try {
      const issued = await issueMutation.mutateAsync({
        userId: issueForm.userId.trim(),
        name: issueForm.name.trim(),
        expiresAt
      });
      setLatestIssuedKey(issued);
      setIssueForm({
        userId: issueForm.userId,
        name: '',
        expiresAt: ''
      });
      setPage(1);
    } catch {
      // mutation error is rendered by actionError
    }
  }

  return (
    <div className='space-y-4'>
      <section className='rounded-card border border-black/10 bg-panel p-4'>
        <h2 className='text-sm font-semibold'>签发 API Key</h2>
        <form className='mt-3 grid gap-3 md:grid-cols-3' onSubmit={(event) => void onIssueKey(event)}>
          <input
            required
            placeholder='目标用户 ID'
            className='rounded-md border border-black/20 bg-white px-3 py-2 text-sm outline-none focus:border-black/50'
            value={issueForm.userId}
            onChange={(event) => setIssueForm((previous) => ({ ...previous, userId: event.target.value }))}
          />
          <input
            required
            placeholder='密钥名称（如 team-laptop）'
            className='rounded-md border border-black/20 bg-white px-3 py-2 text-sm outline-none focus:border-black/50'
            value={issueForm.name}
            onChange={(event) => setIssueForm((previous) => ({ ...previous, name: event.target.value }))}
          />
          <input
            type='datetime-local'
            className='rounded-md border border-black/20 bg-white px-3 py-2 text-sm outline-none focus:border-black/50'
            value={issueForm.expiresAt}
            onChange={(event) => setIssueForm((previous) => ({ ...previous, expiresAt: event.target.value }))}
          />
          <div className='md:col-span-3'>
            <SubmitButton loading={issueMutation.isPending}>签发密钥</SubmitButton>
          </div>
        </form>
        {latestIssuedKey ? (
          <div className='mt-3 rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-900'>
            <p className='font-medium'>密钥已签发（仅显示一次）</p>
            <p className='mt-2 break-all font-mono text-xs'>{latestIssuedKey.plainTextKey}</p>
            <p className='mt-1 text-xs'>
              前缀：{latestIssuedKey.keyPrefix}；到期：{latestIssuedKey.expiresAt ? formatDateTime(latestIssuedKey.expiresAt) : '永不过期'}
            </p>
          </div>
        ) : null}
      </section>

      <section className='rounded-card border border-black/10 bg-panel p-4'>
        <h2 className='text-sm font-semibold'>密钥筛选</h2>
        <form
          className='mt-3 grid gap-3 md:grid-cols-[1fr_220px_auto]'
          onSubmit={(event) => {
            event.preventDefault();
            setUserId(userIdInput.trim());
            setStatus(statusInput);
            setPage(1);
          }}
        >
          <input
            placeholder='按用户 ID 过滤'
            className='rounded-md border border-black/20 bg-white px-3 py-2 text-sm outline-none focus:border-black/50'
            value={userIdInput}
            onChange={(event) => setUserIdInput(event.target.value)}
          />
          <select
            className='rounded-md border border-black/20 bg-white px-3 py-2 text-sm outline-none focus:border-black/50'
            value={statusInput}
            onChange={(event) => setStatusInput(event.target.value as ApiKeyStatus | '')}
          >
            <option value=''>全部状态</option>
            {API_KEY_STATUS_OPTIONS.map((value) => (
              <option key={value} value={value}>
                {API_KEY_STATUS_LABEL_MAP[value]}
              </option>
            ))}
          </select>
          <SubmitButton type='submit'>查询</SubmitButton>
        </form>
      </section>

      {actionError ? <ErrorAlert message={getApiErrorMessage(actionError)} /> : null}
      {listQuery.error ? <ErrorAlert message={getApiErrorMessage(listQuery.error)} /> : null}
      {listQuery.isLoading ? <LoadingSkeleton /> : null}

      {listQuery.data && listQuery.data.items.length === 0 ? (
        <EmptyState title='暂无密钥数据' description='签发第一个 API Key 后，这里会展示密钥状态和使用情况。' />
      ) : null}

      {listQuery.data && listQuery.data.items.length > 0 ? (
        <section className='overflow-x-auto rounded-card border border-black/10 bg-white'>
          <table className='min-w-full divide-y divide-black/10 text-sm'>
            <thead className='bg-panel text-left text-xs text-muted'>
              <tr>
                <th className='px-3 py-2'>名称 / 前缀</th>
                <th className='px-3 py-2'>用户</th>
                <th className='px-3 py-2'>状态</th>
                <th className='px-3 py-2'>最近使用</th>
                <th className='px-3 py-2'>到期时间</th>
                <th className='px-3 py-2'>操作</th>
              </tr>
            </thead>
            <tbody className='divide-y divide-black/10'>
              {listQuery.data.items.map((item) => (
                <tr key={item.keyId}>
                  <td className='px-3 py-2'>
                    <p className='font-medium'>{item.name || '-'}</p>
                    <p className='font-mono text-xs text-muted'>{item.keyPrefix}</p>
                  </td>
                  <td className='px-3 py-2 text-xs'>{item.userId}</td>
                  <td className='px-3 py-2 text-xs'>{API_KEY_STATUS_LABEL_MAP[item.status]}</td>
                  <td className='px-3 py-2 text-xs'>{item.lastUsedAt ? formatDateTime(item.lastUsedAt) : '-'}</td>
                  <td className='px-3 py-2 text-xs'>{item.expiresAt ? formatDateTime(item.expiresAt) : '永不过期'}</td>
                  <td className='px-3 py-2'>
                    <button
                      type='button'
                      disabled={revokeMutation.isPending || item.status !== 'ACTIVE'}
                      className='rounded border border-black/20 px-2 py-1 text-xs disabled:opacity-60'
                      onClick={() => {
                        const confirmed = window.confirm(`确认吊销密钥 ${item.keyPrefix} 吗？`);
                        if (!confirmed) return;
                        revokeMutation.mutate(item.keyId);
                      }}
                    >
                      吊销
                    </button>
                  </td>
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
