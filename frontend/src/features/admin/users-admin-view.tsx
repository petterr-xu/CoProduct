'use client';

import { FormEvent, useEffect, useMemo, useState } from 'react';

import { EmptyState } from '@/components/base/empty-state';
import { ErrorAlert } from '@/components/base/error-alert';
import { LoadingSkeleton } from '@/components/base/loading-skeleton';
import { SubmitButton } from '@/components/base/submit-button';
import {
  useAdminCreateUser,
  useAdminFunctionalRoles,
  useAdminMembers,
  useAdminUpdateMemberFunctionalRole,
  useAdminUpdateMemberRole,
  useAdminUpdateMemberStatus
} from '@/hooks/use-admin-api';
import { getApiErrorMessage } from '@/lib/api-client';
import { MEMBER_STATUS_LABEL_MAP, ROLE_LABEL_MAP } from '@/lib/constants';
import { formatDateTime } from '@/lib/utils';
import { useAuthStore } from '@/stores/auth-store';
import { MemberStatus, Role } from '@/types';

const ROLE_OPTIONS: Role[] = ['OWNER', 'ADMIN', 'MEMBER', 'VIEWER'];
const MEMBER_STATUS_OPTIONS: MemberStatus[] = ['INVITED', 'ACTIVE', 'SUSPENDED', 'REMOVED'];

export function UsersAdminView() {
  const currentUser = useAuthStore((state) => state.user);
  const authContext = useAuthStore((state) => state.authContext);

  const [queryInput, setQueryInput] = useState('');
  const [permissionRoleInput, setPermissionRoleInput] = useState<Role | ''>('');
  const [memberStatusInput, setMemberStatusInput] = useState<MemberStatus | ''>('');
  const [functionalRoleIdInput, setFunctionalRoleIdInput] = useState('');

  const [query, setQuery] = useState('');
  const [permissionRole, setPermissionRole] = useState<Role | ''>('');
  const [memberStatus, setMemberStatus] = useState<MemberStatus | ''>('');
  const [functionalRoleId, setFunctionalRoleId] = useState('');

  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);

  const [createForm, setCreateForm] = useState({
    email: '',
    displayName: '',
    role: 'MEMBER' as Role,
    orgId: ''
  });
  const [createGuardError, setCreateGuardError] = useState<string | null>(null);
  const [roleDrafts, setRoleDrafts] = useState<Record<string, Role>>({});
  const [statusDrafts, setStatusDrafts] = useState<Record<string, MemberStatus>>({});
  const [functionalRoleDrafts, setFunctionalRoleDrafts] = useState<Record<string, string>>({});

  const listQuery = useAdminMembers({
    query: query || undefined,
    permissionRole: permissionRole || undefined,
    memberStatus: memberStatus || undefined,
    functionalRoleId: functionalRoleId || undefined,
    page,
    pageSize
  });
  const functionalRolesQuery = useAdminFunctionalRoles({
    isActive: true,
    page: 1,
    pageSize: 100
  });
  const createMutation = useAdminCreateUser();
  const updateRoleMutation = useAdminUpdateMemberRole();
  const updateStatusMutation = useAdminUpdateMemberStatus();
  const updateFunctionalRoleMutation = useAdminUpdateMemberFunctionalRole();

  const actionError = useMemo(
    () => createMutation.error ?? updateRoleMutation.error ?? updateStatusMutation.error ?? updateFunctionalRoleMutation.error,
    [createMutation.error, updateRoleMutation.error, updateStatusMutation.error, updateFunctionalRoleMutation.error]
  );

  const isMutating =
    createMutation.isPending ||
    updateRoleMutation.isPending ||
    updateStatusMutation.isPending ||
    updateFunctionalRoleMutation.isPending;
  const total = listQuery.data?.total ?? 0;
  const currentPage = listQuery.data?.page ?? page;

  const functionalRoleOptions = functionalRolesQuery.data?.items ?? [];
  const activeOrg = authContext?.activeOrg ?? null;
  const availableOrgs = authContext?.availableOrgs ?? [];
  const scopeMode = authContext?.scopeMode ?? 'ORG_SCOPED';
  const isOrgScoped = scopeMode === 'ORG_SCOPED';
  const hasOrgContext = isOrgScoped ? Boolean(activeOrg?.orgId) : Boolean(createForm.orgId.trim());
  const actorRole = currentUser?.role;
  const actorUserId = currentUser?.id;

  useEffect(() => {
    const defaultOrgId = activeOrg?.orgId ?? '';
    setCreateForm((previous) => {
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
    if (hasOrgContext) {
      setCreateGuardError(null);
    }
  }, [hasOrgContext]);

  async function onCreateUser(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setCreateGuardError(null);

    const targetOrgId = isOrgScoped ? activeOrg?.orgId ?? '' : createForm.orgId.trim();
    if (!targetOrgId) {
      setCreateGuardError('当前账号无可用组织，暂时无法创建成员，请联系管理员。');
      return;
    }

    try {
      await createMutation.mutateAsync({
        email: createForm.email.trim(),
        displayName: createForm.displayName.trim(),
        role: createForm.role,
        orgId: targetOrgId
      });
      setCreateForm((previous) => ({
        ...previous,
        email: '',
        displayName: '',
        orgId: isOrgScoped ? activeOrg?.orgId ?? previous.orgId : previous.orgId
      }));
      setPage(1);
    } catch {
      // mutation error is rendered by actionError
    }
  }

  function getFunctionalRoleDraft(memberId: string, currentRoleId: string): string {
    return functionalRoleDrafts[memberId] ?? currentRoleId;
  }

  function getRoleUpdateDisabledReason(item: { permissionRole: Role; userId: string }, roleDraft: Role): string | null {
    if (roleDraft === item.permissionRole) return '角色未变更';
    if (actorRole === 'ADMIN' && item.permissionRole === 'OWNER') return 'ADMIN 不能操作 OWNER 成员';
    if (actorUserId && actorUserId === item.userId && roleDraft !== item.permissionRole) return '不能修改自己的权限角色';
    return null;
  }

  function getStatusUpdateDisabledReason(
    item: { permissionRole: Role; userId: string; memberStatus: MemberStatus },
    statusDraft: MemberStatus
  ): string | null {
    if (statusDraft === item.memberStatus) return '成员状态未变更';
    if (actorRole === 'ADMIN' && item.permissionRole === 'OWNER') return 'ADMIN 不能操作 OWNER 成员';
    if (actorUserId && actorUserId === item.userId && statusDraft !== 'ACTIVE') return '不能将自己调整为非在岗状态';
    return null;
  }

  function getFunctionalRoleUpdateDisabledReason(
    item: { permissionRole: Role; functionalRoleId: string },
    functionalRoleDraft: string
  ): string | null {
    if (!functionalRoleDraft) return '请选择职能角色';
    if (functionalRoleDraft === item.functionalRoleId) return '职能角色未变更';
    if (actorRole === 'ADMIN' && item.permissionRole === 'OWNER') return 'ADMIN 不能操作 OWNER 成员';
    return null;
  }

  return (
    <div className='space-y-4'>
      <section className='rounded-card border border-black/10 bg-panel p-4'>
        <h2 className='text-sm font-semibold'>新增成员账号</h2>
        <p className='mt-1 text-xs text-muted'>
          当前组织：{activeOrg ? `${activeOrg.orgName} (${activeOrg.orgId})` : '无'} · 上下文模式：{scopeMode}
        </p>
        {!activeOrg ? <p className='mt-1 text-xs text-danger'>当前账号暂无可用组织，创建成员功能已禁用。</p> : null}
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
                {ROLE_LABEL_MAP[value]}
              </option>
            ))}
          </select>
          <select
            className='rounded-md border border-black/20 bg-white px-3 py-2 text-sm outline-none focus:border-black/50'
            value={createForm.orgId}
            onChange={(event) => setCreateForm((p) => ({ ...p, orgId: event.target.value }))}
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
          <div className='md:col-span-4'>
            <SubmitButton loading={createMutation.isPending} disabled={!hasOrgContext}>
              创建成员
            </SubmitButton>
          </div>
        </form>
        {createGuardError ? <ErrorAlert title='组织上下文不可用' message={createGuardError} /> : null}
      </section>

      <section className='rounded-card border border-black/10 bg-panel p-4'>
        <h2 className='text-sm font-semibold'>成员筛选</h2>
        <form
          className='mt-3 grid gap-3 md:grid-cols-[1fr_220px_220px_220px_auto]'
          onSubmit={(event) => {
            event.preventDefault();
            setQuery(queryInput.trim());
            setPermissionRole(permissionRoleInput);
            setMemberStatus(memberStatusInput);
            setFunctionalRoleId(functionalRoleIdInput);
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
            value={permissionRoleInput}
            onChange={(event) => setPermissionRoleInput(event.target.value as Role | '')}
          >
            <option value=''>全部角色</option>
            {ROLE_OPTIONS.map((value) => (
              <option key={value} value={value}>
                {ROLE_LABEL_MAP[value]}
              </option>
            ))}
          </select>
          <select
            className='rounded-md border border-black/20 bg-white px-3 py-2 text-sm outline-none focus:border-black/50'
            value={memberStatusInput}
            onChange={(event) => setMemberStatusInput(event.target.value as MemberStatus | '')}
          >
            <option value=''>全部状态</option>
            {MEMBER_STATUS_OPTIONS.map((value) => (
              <option key={value} value={value}>
                {MEMBER_STATUS_LABEL_MAP[value]}
              </option>
            ))}
          </select>
          <select
            className='rounded-md border border-black/20 bg-white px-3 py-2 text-sm outline-none focus:border-black/50'
            value={functionalRoleIdInput}
            onChange={(event) => setFunctionalRoleIdInput(event.target.value)}
          >
            <option value=''>全部职能</option>
            {functionalRoleOptions.map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
          </select>
          <SubmitButton type='submit'>查询</SubmitButton>
        </form>
      </section>

      {actionError ? <ErrorAlert message={getApiErrorMessage(actionError)} /> : null}
      {listQuery.error ? <ErrorAlert message={getApiErrorMessage(listQuery.error)} /> : null}
      {functionalRolesQuery.error ? <ErrorAlert message={getApiErrorMessage(functionalRolesQuery.error)} /> : null}
      {listQuery.isLoading ? <LoadingSkeleton /> : null}

      {listQuery.data && listQuery.data.items.length === 0 ? (
        <EmptyState title='暂无成员数据' description='可先创建成员账号，或调整筛选条件后重试。' />
      ) : null}

      {listQuery.data && listQuery.data.items.length > 0 ? (
        <section className='overflow-x-auto rounded-card border border-black/10 bg-white'>
          <table className='min-w-full divide-y divide-black/10 text-sm'>
            <thead className='bg-panel text-left text-xs text-muted'>
              <tr>
                <th className='px-3 py-2'>成员信息</th>
                <th className='px-3 py-2'>权限角色</th>
                <th className='px-3 py-2'>成员状态</th>
                <th className='px-3 py-2'>职能角色</th>
                <th className='px-3 py-2'>组织</th>
                <th className='px-3 py-2'>最后登录</th>
                <th className='px-3 py-2'>操作</th>
              </tr>
            </thead>
            <tbody className='divide-y divide-black/10'>
              {listQuery.data.items.map((item) => {
                const roleDraft = roleDrafts[item.membershipId] ?? item.permissionRole;
                const statusDraft = statusDrafts[item.membershipId] ?? item.memberStatus;
                const functionalRoleDraft = getFunctionalRoleDraft(item.membershipId, item.functionalRoleId);
                const roleDisabledReason = getRoleUpdateDisabledReason(item, roleDraft);
                const statusDisabledReason = getStatusUpdateDisabledReason(item, statusDraft);
                const functionalRoleDisabledReason = getFunctionalRoleUpdateDisabledReason(item, functionalRoleDraft);
                const isSelf = actorUserId && actorUserId === item.userId;
                const isOwnerTarget = item.permissionRole === 'OWNER';

                const selectableFunctionalRoles = [...functionalRoleOptions];
                if (
                  item.functionalRoleId &&
                  !selectableFunctionalRoles.some((roleItem) => roleItem.id === item.functionalRoleId)
                ) {
                  selectableFunctionalRoles.push({
                    id: item.functionalRoleId,
                    orgId: item.orgId,
                    code: item.functionalRoleCode || item.functionalRoleId,
                    name: item.functionalRoleName || item.functionalRoleCode || item.functionalRoleId,
                    description: '历史角色（当前列表未启用）',
                    isActive: false,
                    sortOrder: 9999,
                    createdAt: item.createdAt,
                    updatedAt: item.createdAt
                  });
                }

                return (
                  <tr key={item.membershipId}>
                    <td className='px-3 py-2'>
                      <p className='font-medium'>{item.displayName || '-'}</p>
                      <p className='text-xs text-muted'>{item.email}</p>
                      {isSelf ? <p className='text-xs text-blue-700'>当前登录成员</p> : null}
                    </td>
                    <td className='px-3 py-2'>
                      <select
                        className='rounded border border-black/20 px-2 py-1 text-xs'
                        value={roleDraft}
                        onChange={(event) =>
                          setRoleDrafts((previous) => ({
                            ...previous,
                            [item.membershipId]: event.target.value as Role
                          }))
                        }
                      >
                        {ROLE_OPTIONS.map((value) => (
                          <option key={value} value={value}>
                            {ROLE_LABEL_MAP[value]}
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
                            [item.membershipId]: event.target.value as MemberStatus
                          }))
                        }
                      >
                        {MEMBER_STATUS_OPTIONS.map((value) => (
                          <option key={value} value={value}>
                            {MEMBER_STATUS_LABEL_MAP[value]}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td className='px-3 py-2'>
                      <select
                        className='rounded border border-black/20 px-2 py-1 text-xs'
                        value={functionalRoleDraft}
                        onChange={(event) =>
                          setFunctionalRoleDrafts((previous) => ({
                            ...previous,
                            [item.membershipId]: event.target.value
                          }))
                        }
                      >
                        {selectableFunctionalRoles.map((roleItem) => (
                          <option key={roleItem.id} value={roleItem.id}>
                            {roleItem.name}
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
                          disabled={isMutating || Boolean(roleDisabledReason)}
                          title={roleDisabledReason || ''}
                          onClick={() => {
                            updateRoleMutation.mutate({
                              memberId: item.membershipId,
                              body: { role: roleDraft, reason: 'manual member role update' }
                            });
                          }}
                        >
                          更新角色
                        </button>
                        <button
                          type='button'
                          className='rounded border border-black/20 px-2 py-1 text-xs disabled:opacity-60'
                          disabled={isMutating || Boolean(statusDisabledReason)}
                          title={statusDisabledReason || ''}
                          onClick={() => {
                            updateStatusMutation.mutate({
                              memberId: item.membershipId,
                              body: { status: statusDraft, reason: 'manual member status update' }
                            });
                          }}
                        >
                          更新状态
                        </button>
                        <button
                          type='button'
                          className='rounded border border-black/20 px-2 py-1 text-xs disabled:opacity-60'
                          disabled={isMutating || Boolean(functionalRoleDisabledReason)}
                          title={functionalRoleDisabledReason || ''}
                          onClick={() => {
                            updateFunctionalRoleMutation.mutate({
                              memberId: item.membershipId,
                              body: {
                                functionalRoleId: functionalRoleDraft,
                                reason: 'manual member functional role update'
                              }
                            });
                          }}
                        >
                          更新职能
                        </button>
                      </div>
                      {isOwnerTarget && actorRole === 'ADMIN' ? (
                        <p className='mt-1 text-xs text-muted'>OWNER 成员仅可由 OWNER 管理</p>
                      ) : null}
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
