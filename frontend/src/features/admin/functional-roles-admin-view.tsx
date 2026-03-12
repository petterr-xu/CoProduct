'use client';

import { FormEvent, useMemo, useState } from 'react';

import { EmptyState } from '@/components/base/empty-state';
import { ErrorAlert } from '@/components/base/error-alert';
import { LoadingSkeleton } from '@/components/base/loading-skeleton';
import { SubmitButton } from '@/components/base/submit-button';
import {
  useAdminCreateFunctionalRole,
  useAdminFunctionalRoles,
  useAdminUpdateFunctionalRoleStatus
} from '@/hooks/use-admin-api';
import { getApiErrorMessage } from '@/lib/api-client';
import { formatDateTime } from '@/lib/utils';

export function FunctionalRolesAdminView() {
  const [name, setName] = useState('');
  const [code, setCode] = useState('');
  const [description, setDescription] = useState('');

  const [isActiveFilterInput, setIsActiveFilterInput] = useState<'all' | 'true' | 'false'>('all');
  const [isActiveFilter, setIsActiveFilter] = useState<'all' | 'true' | 'false'>('all');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);

  const listQuery = useAdminFunctionalRoles({
    isActive: isActiveFilter === 'all' ? undefined : isActiveFilter === 'true',
    page,
    pageSize
  });
  const createMutation = useAdminCreateFunctionalRole();
  const updateStatusMutation = useAdminUpdateFunctionalRoleStatus();

  const actionError = useMemo(
    () => createMutation.error ?? updateStatusMutation.error,
    [createMutation.error, updateStatusMutation.error]
  );

  async function onCreateRole(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      await createMutation.mutateAsync({
        code: code.trim().toLowerCase(),
        name: name.trim(),
        description: description.trim() || undefined
      });
      setName('');
      setCode('');
      setDescription('');
      setPage(1);
    } catch {
      // error rendered by actionError
    }
  }

  const total = listQuery.data?.total ?? 0;
  const currentPage = listQuery.data?.page ?? page;

  return (
    <div className='space-y-4'>
      <section className='rounded-card border border-black/10 bg-panel p-4'>
        <h2 className='text-sm font-semibold'>新增职能角色</h2>
        <form className='mt-3 grid gap-3 md:grid-cols-3' onSubmit={(event) => void onCreateRole(event)}>
          <input
            required
            placeholder='角色编码（如 pm）'
            className='rounded-md border border-black/20 bg-white px-3 py-2 text-sm outline-none focus:border-black/50'
            value={code}
            onChange={(event) => setCode(event.target.value)}
          />
          <input
            required
            placeholder='角色名称（如 产品经理）'
            className='rounded-md border border-black/20 bg-white px-3 py-2 text-sm outline-none focus:border-black/50'
            value={name}
            onChange={(event) => setName(event.target.value)}
          />
          <input
            placeholder='说明（可选）'
            className='rounded-md border border-black/20 bg-white px-3 py-2 text-sm outline-none focus:border-black/50'
            value={description}
            onChange={(event) => setDescription(event.target.value)}
          />
          <div className='md:col-span-3'>
            <SubmitButton loading={createMutation.isPending}>创建角色</SubmitButton>
          </div>
        </form>
      </section>

      <section className='rounded-card border border-black/10 bg-panel p-4'>
        <h2 className='text-sm font-semibold'>角色筛选</h2>
        <form
          className='mt-3 grid gap-3 md:grid-cols-[220px_auto]'
          onSubmit={(event) => {
            event.preventDefault();
            setIsActiveFilter(isActiveFilterInput);
            setPage(1);
          }}
        >
          <select
            className='rounded-md border border-black/20 bg-white px-3 py-2 text-sm outline-none focus:border-black/50'
            value={isActiveFilterInput}
            onChange={(event) => setIsActiveFilterInput(event.target.value as 'all' | 'true' | 'false')}
          >
            <option value='all'>全部状态</option>
            <option value='true'>仅启用</option>
            <option value='false'>仅停用</option>
          </select>
          <SubmitButton type='submit'>查询</SubmitButton>
        </form>
      </section>

      {actionError ? <ErrorAlert message={getApiErrorMessage(actionError)} /> : null}
      {listQuery.error ? <ErrorAlert message={getApiErrorMessage(listQuery.error)} /> : null}
      {listQuery.isLoading ? <LoadingSkeleton /> : null}

      {listQuery.data && listQuery.data.items.length === 0 ? (
        <EmptyState title='暂无职能角色' description='请先创建团队职能角色，供成员绑定使用。' />
      ) : null}

      {listQuery.data && listQuery.data.items.length > 0 ? (
        <section className='overflow-x-auto rounded-card border border-black/10 bg-white'>
          <table className='min-w-full divide-y divide-black/10 text-sm'>
            <thead className='bg-panel text-left text-xs text-muted'>
              <tr>
                <th className='px-3 py-2'>角色信息</th>
                <th className='px-3 py-2'>编码</th>
                <th className='px-3 py-2'>状态</th>
                <th className='px-3 py-2'>更新时间</th>
                <th className='px-3 py-2'>操作</th>
              </tr>
            </thead>
            <tbody className='divide-y divide-black/10'>
              {listQuery.data.items.map((item) => {
                const isUnassigned = item.code === 'unassigned';
                const nextStatus = !item.isActive;
                const statusLabel = item.isActive ? '启用' : '停用';
                const actionLabel = item.isActive ? '停用' : '启用';

                return (
                  <tr key={item.id}>
                    <td className='px-3 py-2'>
                      <p className='font-medium'>{item.name}</p>
                      <p className='text-xs text-muted'>{item.description || '-'}</p>
                    </td>
                    <td className='px-3 py-2 font-mono text-xs'>{item.code}</td>
                    <td className='px-3 py-2 text-xs'>{statusLabel}</td>
                    <td className='px-3 py-2 text-xs'>{formatDateTime(item.updatedAt || item.createdAt)}</td>
                    <td className='px-3 py-2'>
                      <button
                        type='button'
                        className='rounded border border-black/20 px-2 py-1 text-xs disabled:opacity-60'
                        disabled={updateStatusMutation.isPending || isUnassigned}
                        title={isUnassigned ? '默认角色 unassigned 不可停用' : ''}
                        onClick={() => {
                          const confirmed = window.confirm(`确认${actionLabel}职能角色「${item.name}」吗？`);
                          if (!confirmed) return;
                          updateStatusMutation.mutate({
                            roleId: item.id,
                            body: { isActive: nextStatus }
                          });
                        }}
                      >
                        {actionLabel}
                      </button>
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
