import { CapabilityStatus, SessionStatus } from '@/types';

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

export const QUERY_KEYS = {
  prereviewDetail: (sessionId: string) => ['prereview-detail', sessionId] as const,
  history: (keyword: string, capabilityStatus: string, page: number, pageSize: number) =>
    ['history', keyword, capabilityStatus, page, pageSize] as const,
  adminUsersRoot: ['admin-users'] as const,
  adminUsers: (query: string, role: string, status: string, page: number, pageSize: number) =>
    ['admin-users', query, role, status, page, pageSize] as const,
  adminApiKeysRoot: ['admin-api-keys'] as const,
  adminApiKeys: (userId: string, status: string, page: number, pageSize: number) =>
    ['admin-api-keys', userId, status, page, pageSize] as const,
  adminAuditLogsRoot: ['admin-audit-logs'] as const,
  adminAuditLogs: (actorUserId: string, action: string, page: number, pageSize: number) =>
    ['admin-audit-logs', actorUserId, action, page, pageSize] as const
};
