import { ApiKeyStatus, CapabilityStatus, MemberStatus, Role, SessionStatus, UserStatus } from '@/types';

export const STATUS_COLOR_MAP: Record<CapabilityStatus, string> = {
  SUPPORTED: 'text-success bg-green-100 border-green-200',
  PARTIALLY_SUPPORTED: 'text-warning bg-amber-100 border-amber-200',
  NOT_SUPPORTED: 'text-danger bg-red-100 border-red-200',
  NEED_MORE_INFO: 'text-info bg-blue-100 border-blue-200'
};

export const CAPABILITY_LABEL_MAP: Record<CapabilityStatus, string> = {
  SUPPORTED: '已支持',
  PARTIALLY_SUPPORTED: '部分支持',
  NOT_SUPPORTED: '暂不支持',
  NEED_MORE_INFO: '需补充信息'
};

export const CONFIDENCE_LABEL_MAP = {
  high: '高',
  medium: '中',
  low: '低'
} as const;

export const SESSION_STATUS_COLOR_MAP: Record<SessionStatus, string> = {
  PROCESSING: 'text-info bg-blue-100 border-blue-200',
  DONE: 'text-success bg-green-100 border-green-200',
  FAILED: 'text-danger bg-red-100 border-red-200'
};

export const SESSION_STATUS_LABEL_MAP: Record<SessionStatus, string> = {
  PROCESSING: '处理中',
  DONE: '已完成',
  FAILED: '失败'
};

export const ROLE_LABEL_MAP: Record<Role, string> = {
  OWNER: '组织所有者',
  ADMIN: '管理员',
  MEMBER: '成员',
  VIEWER: '只读成员'
};

export const USER_STATUS_LABEL_MAP: Record<UserStatus, string> = {
  ACTIVE: '激活',
  DISABLED: '禁用',
  PENDING_INVITE: '待邀请'
};

export const MEMBER_STATUS_LABEL_MAP: Record<MemberStatus, string> = {
  INVITED: '待加入',
  ACTIVE: '在岗',
  SUSPENDED: '停用',
  REMOVED: '移除'
};

export const API_KEY_STATUS_LABEL_MAP: Record<ApiKeyStatus, string> = {
  ACTIVE: '可用',
  REVOKED: '已吊销',
  EXPIRED: '已过期'
};

export const QUERY_KEYS = {
  prereviewDetail: (sessionId: string) => ['prereview-detail', sessionId] as const,
  history: (keyword: string, capabilityStatus: string, page: number, pageSize: number) =>
    ['history', keyword, capabilityStatus, page, pageSize] as const,
  adminUsersRoot: ['admin-users'] as const,
  adminUsers: (query: string, role: string, status: string, page: number, pageSize: number) =>
    ['admin-users', query, role, status, page, pageSize] as const,
  adminMembersRoot: ['admin-members'] as const,
  adminMembers: (
    query: string,
    permissionRole: string,
    memberStatus: string,
    functionalRoleId: string,
    page: number,
    pageSize: number
  ) => ['admin-members', query, permissionRole, memberStatus, functionalRoleId, page, pageSize] as const,
  adminFunctionalRolesRoot: ['admin-functional-roles'] as const,
  adminFunctionalRoles: (isActive: string, page: number, pageSize: number) =>
    ['admin-functional-roles', isActive, page, pageSize] as const,
  adminApiKeysRoot: ['admin-api-keys'] as const,
  adminApiKeys: (userId: string, status: string, page: number, pageSize: number) =>
    ['admin-api-keys', userId, status, page, pageSize] as const,
  adminAuditLogsRoot: ['admin-audit-logs'] as const,
  adminAuditLogs: (actorUserId: string, action: string, page: number, pageSize: number) =>
    ['admin-audit-logs', actorUserId, action, page, pageSize] as const
};
