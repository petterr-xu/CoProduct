'use client';

import { FormEvent, useEffect, useMemo, useState } from 'react';

import { EmptyState } from '@/components/base/empty-state';
import { ErrorAlert } from '@/components/base/error-alert';
import { LoadingSkeleton } from '@/components/base/loading-skeleton';
import { SubmitButton } from '@/components/base/submit-button';
import { useAdminApiKeys, useAdminIssueApiKey, useAdminMemberOptions, useAdminRevokeApiKey } from '@/hooks/use-admin-api';
import { getApiErrorMessage } from '@/lib/api-client';
import { API_KEY_STATUS_LABEL_MAP } from '@/lib/constants';
import { formatDateTime } from '@/lib/utils';
import { useAuthStore } from '@/stores/auth-store';
import { ApiKeyStatus, IssueApiKeyResponse, MemberOptionItem } from '@/types';

const API_KEY_STATUS_OPTIONS: ApiKeyStatus[] = ['ACTIVE', 'REVOKED', 'EXPIRED'];
const MEMBER_SEARCH_MIN_LENGTH = 2;
const MEMBER_SEARCH_DEBOUNCE_MS = 250;

function getMemberOptionLabel(item: MemberOptionItem): string {
  const primary = item.displayName.trim() || item.email.trim() || item.userId;
  return `${primary} · ${item.email}`;
}

export function ApiKeysAdminView() {
  const authContext = useAuthStore((state) => state.authContext);
  const [userIdInput, setUserIdInput] = useState('');
  const [statusInput, setStatusInput] = useState<ApiKeyStatus | ''>('');

  const [userId, setUserId] = useState('');
  const [status, setStatus] = useState<ApiKeyStatus | ''>('');

  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);

  const [issueForm, setIssueForm] = useState({
    orgId: '',
    name: '',
    expiresAt: ''
  });
  const [memberKeywordInput, setMemberKeywordInput] = useState('');
  const [debouncedMemberKeyword, setDebouncedMemberKeyword] = useState('');
  const [selectedMember, setSelectedMember] = useState<MemberOptionItem | null>(null);
  const [issueGuardError, setIssueGuardError] = useState<string | null>(null);
  const [latestIssuedKey, setLatestIssuedKey] = useState<IssueApiKeyResponse | null>(null);

  const activeOrg = authContext?.activeOrg ?? null;
  const availableOrgs = authContext?.availableOrgs ?? [];
  const scopeMode = authContext?.scopeMode ?? 'ORG_SCOPED';
  const isOrgScoped = scopeMode === 'ORG_SCOPED';
  const selectedOrgId = isOrgScoped ? activeOrg?.orgId ?? '' : issueForm.orgId.trim();
  const hasOrgContext = Boolean(selectedOrgId);

  useEffect(() => {
    const defaultOrgId = activeOrg?.orgId ?? '';
    setIssueForm((previous) => {
      if (isOrgScoped) {
        if (previous.orgId === defaultOrgId) return previous;
        return { ...previous, orgId: defaultOrgId };
      }
      if (!previous.orgId && defaultOrgId) {
        return { ...previous, orgId: defaultOrgId };
      }
      return previous;
    });
  }, [activeOrg?.orgId, isOrgScoped]);

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      setDebouncedMemberKeyword(memberKeywordInput.trim());
    }, MEMBER_SEARCH_DEBOUNCE_MS);
    return () => window.clearTimeout(timeoutId);
  }, [memberKeywordInput]);

  useEffect(() => {
    setSelectedMember(null);
    setMemberKeywordInput('');
    setDebouncedMemberKeyword('');
    setIssueGuardError(null);
  }, [selectedOrgId]);

  const memberSearchEnabled =
    hasOrgContext && !selectedMember && debouncedMemberKeyword.length >= MEMBER_SEARCH_MIN_LENGTH;
  const memberOptionsQuery = useAdminMemberOptions(
    {
      query: debouncedMemberKeyword,
      orgId: selectedOrgId || undefined,
      limit: 20
    },
    { enabled: memberSearchEnabled }
  );

  const listQuery = useAdminApiKeys({
    userId: userId || undefined,
    orgId: selectedOrgId || undefined,
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
    setIssueGuardError(null);

    if (!hasOrgContext) {
      setIssueGuardError('当前账号暂无可用组织，无法签发 API Key。');
      return;
    }
    if (!selectedMember) {
      setIssueGuardError('请先通过成员联想搜索选择目标成员。');
      return;
    }
    if (selectedMember.orgId !== selectedOrgId) {
      setIssueGuardError('目标成员不在当前组织，请切换组织后重试。');
      return;
    }
    if (!issueForm.name.trim()) {
      setIssueGuardError('请填写有效的密钥名称。');
      return;
    }

    const trimmedExpiresAt = issueForm.expiresAt.trim();
    const parsedExpiresAt = trimmedExpiresAt ? new Date(trimmedExpiresAt) : null;
    const expiresAt =
      parsedExpiresAt && !Number.isNaN(parsedExpiresAt.getTime()) ? parsedExpiresAt.toISOString() : undefined;
    try {
      const issued = await issueMutation.mutateAsync({
        userId: selectedMember.userId,
        name: issueForm.name.trim(),
        expiresAt,
        orgId: selectedOrgId || undefined
      });
      setLatestIssuedKey(issued);
      setIssueForm((previous) => ({ ...previous, name: '', expiresAt: '' }));
      setPage(1);
    } catch {
      // mutation error is rendered by actionError
    }
  }

  return (
    <div className='space-y-4'>
      <section className='rounded-card border border-black/10 bg-panel p-4'>
        <h2 className='text-sm font-semibold'>签发 API Key</h2>
        <p className='mt-1 text-xs text-muted'>
          当前组织：{activeOrg ? `${activeOrg.orgName} (${activeOrg.orgId})` : '无'} · 上下文模式：{scopeMode}
        </p>
        {!activeOrg ? <p className='mt-1 text-xs text-danger'>当前账号暂无可用组织，签发功能暂不可用。</p> : null}
        <form className='mt-3 grid gap-3 md:grid-cols-2' onSubmit={(event) => void onIssueKey(event)}>
          <select
            className='rounded-md border border-black/20 bg-white px-3 py-2 text-sm outline-none focus:border-black/50'
            value={issueForm.orgId}
            onChange={(event) => setIssueForm((previous) => ({ ...previous, orgId: event.target.value }))}
            disabled={isOrgScoped || availableOrgs.length === 0}
            title={isOrgScoped ? 'ORG_SCOPED 模式下组织由登录上下文固定' : undefined}
          >
            <option value='' disabled>
              {availableOrgs.length === 0 ? '无可用组织' : '请选择组织'}
            </option>
            {availableOrgs.map((org) => (
              <option key={org.orgId} value={org.orgId}>
                {org.orgName} ({org.orgId})
              </option>
            ))}
          </select>
          <input
            required
            placeholder='搜索成员（邮箱或显示名前缀）'
            className='rounded-md border border-black/20 bg-white px-3 py-2 text-sm outline-none focus:border-black/50'
            value={memberKeywordInput}
            onChange={(event) => {
              setMemberKeywordInput(event.target.value);
              setSelectedMember(null);
              setIssueGuardError(null);
            }}
            disabled={!hasOrgContext}
          />
          {!hasOrgContext ? (
            <p className='md:col-span-2 text-xs text-danger'>请先选择可用组织，再检索目标成员。</p>
          ) : null}
          {hasOrgContext && selectedMember ? (
            <div className='md:col-span-2 rounded-md border border-green-200 bg-green-50 p-2 text-xs text-green-900'>
              <p>
                已选择：{selectedMember.displayName || selectedMember.email}（{selectedMember.email}）
              </p>
              <button
                type='button'
                className='mt-1 rounded border border-green-300 px-2 py-1 text-[11px]'
                onClick={() => {
                  setSelectedMember(null);
                  setMemberKeywordInput('');
                }}
              >
                重新选择
              </button>
            </div>
          ) : null}
          {hasOrgContext && !selectedMember && memberKeywordInput.trim().length < MEMBER_SEARCH_MIN_LENGTH ? (
            <p className='md:col-span-2 text-xs text-muted'>请输入至少 {MEMBER_SEARCH_MIN_LENGTH} 个字符后开始联想搜索。</p>
          ) : null}
          {memberSearchEnabled && memberOptionsQuery.isFetching ? (
            <p className='md:col-span-2 text-xs text-muted'>正在检索候选成员...</p>
          ) : null}
          {memberSearchEnabled && memberOptionsQuery.error ? (
            <div className='md:col-span-2'>
              <ErrorAlert title='成员检索失败' message={getApiErrorMessage(memberOptionsQuery.error)} />
            </div>
          ) : null}
          {memberSearchEnabled &&
          !memberOptionsQuery.isFetching &&
          !memberOptionsQuery.error &&
          (memberOptionsQuery.data?.items.length ?? 0) === 0 ? (
            <p className='md:col-span-2 text-xs text-muted'>未找到候选成员。请尝试调整关键词或切换组织后重试。</p>
          ) : null}
          {memberSearchEnabled &&
          !memberOptionsQuery.isFetching &&
          !memberOptionsQuery.error &&
          (memberOptionsQuery.data?.items.length ?? 0) > 0 ? (
            <div className='md:col-span-2 rounded-md border border-black/10 bg-white p-2'>
              <p className='mb-2 text-xs text-muted'>请选择目标成员：</p>
              <div className='max-h-44 space-y-2 overflow-y-auto'>
                {memberOptionsQuery.data?.items.map((item) => (
                  <button
                    key={item.membershipId}
                    type='button'
                    className='w-full rounded border border-black/10 px-2 py-2 text-left text-xs hover:bg-panel'
                    onClick={() => {
                      setSelectedMember(item);
                      setMemberKeywordInput(getMemberOptionLabel(item));
                      setIssueGuardError(null);
                    }}
                  >
                    <p className='font-medium'>{item.displayName || item.email}</p>
                    <p className='text-muted'>{item.email}</p>
                  </button>
                ))}
              </div>
            </div>
          ) : null}
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
          <div className='md:col-span-2'>
            <SubmitButton loading={issueMutation.isPending} disabled={!hasOrgContext || !selectedMember}>
              签发密钥
            </SubmitButton>
          </div>
        </form>
        {issueGuardError ? <ErrorAlert title='签发条件未满足' message={issueGuardError} /> : null}
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
                  <td className='px-3 py-2 text-xs'>
                    <p className='font-medium text-black'>{item.userDisplayName || item.userEmail || item.userId}</p>
                    {item.userEmail ? <p className='text-muted'>{item.userEmail}</p> : null}
                    <p className='font-mono text-[11px] text-muted'>{item.userId}</p>
                  </td>
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
