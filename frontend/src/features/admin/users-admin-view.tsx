'use client';

import { FormEvent, useMemo, useState } from 'react';

import { EmptyState } from '@/components/base/empty-state';
import { ErrorAlert } from '@/components/base/error-alert';
import { LoadingSkeleton } from '@/components/base/loading-skeleton';
import { SubmitButton } from '@/components/base/submit-button';
import {
  useAdminCreateUser,
  useAdminUpdateUserRole,
  useAdminUpdateUserStatus,
  useAdminUsers
} from '@/hooks/use-admin-api';
import { getApiErrorMessage } from '@/lib/api-client';
import { formatDateTime } from '@/lib/utils';
import { Role, UserStatus } from '@/types';

const ROLE_OPTIONS: Role[] = ['OWNER', 'ADMIN', 'MEMBER', 'VIEWER'];
const USER_STATUS_OPTIONS: UserStatus[] = ['ACTIVE', 'DISABLED', 'PENDING_INVITE'];

export function UsersAdminView() {
  const [queryInput, setQueryInput] = useState('');
  const [roleInput, setRoleInput] = useState<Role | ''>('');
  const [statusInput, setStatusInput] = useState<UserStatus | ''>('');

  const [query, setQuery] = useState('');
  const [role, setRole] = useState<Role | ''>('');
  const [status, setStatus] = useState<UserStatus | ''>('');

  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);

  const [createForm, setCreateForm] = useState({
    email: '',
    displayName: '',
    role: 'MEMBER' as Role,
    orgId: ''
  });
  const [roleDrafts, setRoleDrafts] = useState<Record<string, Role>>({});
  const [statusDrafts, setStatusDrafts] = useState<Record<string, UserStatus>>({});

  const listQuery = useAdminUsers({
    query: query || undefined,
    role: role || undefined,
    status: status || undefined,
    page,
    pageSize
  });
  const createMutation = useAdminCreateUser();
  const updateRoleMutation = useAdminUpdateUserRole();
  const updateStatusMutation = useAdminUpdateUserStatus();

  const actionError = useMemo(
    () => createMutation.error ?? updateRoleMutation.error ?? updateStatusMutation.error,
    [createMutation.error, updateRoleMutation.error, updateStatusMutation.error]
  );

  const isMutating = createMutation.isPending || updateRoleMutation.isPending || updateStatusMutation.isPending;
  const total = listQuery.data?.total ?? 0;
  const currentPage = listQuery.data?.page ?? page;

  async function onCreateUser(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      await createMutation.mutateAsync({
        email: createForm.email.trim(),
        displayName: createForm.displayName.trim(),
        role: createForm.role,
        orgId: createForm.orgId.trim() || undefined
      });
      setCreateForm((previous) => ({
        ...previous,
        email: '',
        displayName: ''
      }));
      setPage(1);
    } catch {
      // mutation error is rendered by actionError
    }
  }

  return (
    <div className='space-y-4'>
      <section className='rounded-card border border-black/10 bg-panel p-4'>
        <h2 className='text-sm font-semibold'>创建用户</h2>
        <form className='mt-3 grid gap-3 md:grid-cols-4' onSubmit={(event) => void onCreateUser(event)}>
          <input
            required
            type='email'
            placeholder='邮箱'
            className='rounded-md border border-black/20 bg-white px-3 py-2 text-sm outline-none focus:border-black/50'
            value={createForm.email}
            onChange={(event) => setCreateForm((p) => ({ ...p, email: event.target.value }))}
          />
          <input
            required
            placeholder='显示名'
            className='rounded-md border border-black/20 bg-white px-3 py-2 text-sm outline-none focus:border-black/50'
            value={createForm.displayName}
            onChange={(event) => setCreateForm((p) => ({ ...p, displayName: event.target.value }))}
          />
          <select
            className='rounded-md border border-black/20 bg-white px-3 py-2 text-sm outline-none focus:border-black/50'
            value={createForm.role}
            onChange={(event) => setCreateForm((p) => ({ ...p, role: event.target.value as Role }))}
          >
            {ROLE_OPTIONS.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
          <input
            placeholder='组织 ID（可选）'
            className='rounded-md border border-black/20 bg-white px-3 py-2 text-sm outline-none focus:border-black/50'
            value={createForm.orgId}
            onChange={(event) => setCreateForm((p) => ({ ...p, orgId: event.target.value }))}
          />
          <div className='md:col-span-4'>
            <SubmitButton loading={createMutation.isPending}>创建用户</SubmitButton>
          </div>
        </form>
      </section>

      <section className='rounded-card border border-black/10 bg-panel p-4'>
        <h2 className='text-sm font-semibold'>用户筛选</h2>
        <form
          className='mt-3 grid gap-3 md:grid-cols-[1fr_220px_220px_auto]'
          onSubmit={(event) => {
            event.preventDefault();
            setQuery(queryInput.trim());
            setRole(roleInput);
            setStatus(statusInput);
            setPage(1);
          }}
        >
          <input
            className='rounded-md border border-black/20 bg-white px-3 py-2 text-sm outline-none focus:border-black/50'
            placeholder='按邮箱或名称搜索'
            value={queryInput}
            onChange={(event) => setQueryInput(event.target.value)}
          />
          <select
            className='rounded-md border border-black/20 bg-white px-3 py-2 text-sm outline-none focus:border-black/50'
            value={roleInput}
            onChange={(event) => setRoleInput(event.target.value as Role | '')}
          >
            <option value=''>全部角色</option>
            {ROLE_OPTIONS.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
          <select
            className='rounded-md border border-black/20 bg-white px-3 py-2 text-sm outline-none focus:border-black/50'
            value={statusInput}
            onChange={(event) => setStatusInput(event.target.value as UserStatus | '')}
          >
            <option value=''>全部状态</option>
            {USER_STATUS_OPTIONS.map((value) => (
              <option key={value} value={value}>
                {value}
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
        <EmptyState title='暂无用户数据' description='可先创建用户，或调整筛选条件后重试。' />
      ) : null}

      {listQuery.data && listQuery.data.items.length > 0 ? (
        <section className='overflow-x-auto rounded-card border border-black/10 bg-white'>
          <table className='min-w-full divide-y divide-black/10 text-sm'>
            <thead className='bg-panel text-left text-xs text-muted'>
              <tr>
                <th className='px-3 py-2'>邮箱 / 显示名</th>
                <th className='px-3 py-2'>角色</th>
                <th className='px-3 py-2'>状态</th>
                <th className='px-3 py-2'>组织</th>
                <th className='px-3 py-2'>最后登录</th>
                <th className='px-3 py-2'>操作</th>
              </tr>
            </thead>
            <tbody className='divide-y divide-black/10'>
              {listQuery.data.items.map((item) => {
                const roleDraft = roleDrafts[item.id] ?? item.role;
                const statusDraft = statusDrafts[item.id] ?? item.status;
                return (
                  <tr key={item.id}>
                    <td className='px-3 py-2'>
                      <p className='font-medium'>{item.displayName || '-'}</p>
                      <p className='text-xs text-muted'>{item.email}</p>
                    </td>
                    <td className='px-3 py-2'>
                      <select
                        className='rounded border border-black/20 px-2 py-1 text-xs'
                        value={roleDraft}
                        onChange={(event) =>
                          setRoleDrafts((previous) => ({
                            ...previous,
                            [item.id]: event.target.value as Role
                          }))
                        }
                      >
                        {ROLE_OPTIONS.map((value) => (
                          <option key={value} value={value}>
                            {value}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td className='px-3 py-2'>
                      <select
                        className='rounded border border-black/20 px-2 py-1 text-xs'
                        value={statusDraft}
                        onChange={(event) =>
                          setStatusDrafts((previous) => ({
                            ...previous,
                            [item.id]: event.target.value as UserStatus
                          }))
                        }
                      >
                        {USER_STATUS_OPTIONS.map((value) => (
                          <option key={value} value={value}>
                            {value}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td className='px-3 py-2 text-xs'>{item.orgId || '-'}</td>
                    <td className='px-3 py-2 text-xs'>{item.lastLoginAt ? formatDateTime(item.lastLoginAt) : '-'}</td>
                    <td className='px-3 py-2'>
                      <div className='flex flex-wrap gap-2'>
                        <button
                          type='button'
                          className='rounded border border-black/20 px-2 py-1 text-xs disabled:opacity-60'
                          disabled={isMutating || roleDraft === item.role}
                          onClick={() => {
                            updateRoleMutation.mutate({
                              userId: item.id,
                              body: { role: roleDraft }
                            });
                          }}
                        >
                          更新角色
                        </button>
                        <button
                          type='button'
                          className='rounded border border-black/20 px-2 py-1 text-xs disabled:opacity-60'
                          disabled={isMutating || statusDraft === item.status}
                          onClick={() => {
                            updateStatusMutation.mutate({
                              userId: item.id,
                              body: { status: statusDraft }
                            });
                          }}
                        >
                          更新状态
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
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
