import {
  ApiKeyListItem,
  ApiKeyStatus,
  AuditLogItem,
  CapabilityStatus,
  CreateFunctionalRoleRequest,
  CreateUserRequest,
  CreatePreReviewForm,
  FileParseStatus,
  FunctionalRoleView,
  HistoryItem,
  HistoryListResponse,
  HistoryQuery,
  IssueApiKeyRequest,
  IssueApiKeyResponse,
  ListFunctionalRolesQuery,
  ListMembersQuery,
  ListApiKeysQuery,
  ListAuditLogsQuery,
  ListResponse,
  ListUsersQuery,
  MemberListItem,
  MemberStatus,
  PreReviewReportView,
  Role,
  SessionStatus,
  UpdateFunctionalRoleStatusRequest,
  UpdateMemberFunctionalRoleRequest,
  UpdateMemberRoleRequest,
  UpdateMemberStatusRequest,
  UpdateUserRoleRequest,
  UpdateUserStatusRequest,
  UserListItem,
  UserStatus,
  UploadedFileRef
} from '@/types';

import { authClient } from '@/lib/auth-client';
import { ApiClientError, fetchWithTimeout, parseErrorResponse } from '@/lib/http-client';
import { useAuthStore } from '@/stores/auth-store';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';

export { ApiClientError };

export function isApiClientError(error: unknown): error is ApiClientError {
  return error instanceof ApiClientError;
}

export function getApiErrorMessage(error: unknown, fallback = '请求失败，请稍后重试') {
  if (isApiClientError(error)) {
    if (error.code === 'FILE_UPLOAD_ERROR') return '文件上传失败，请检查文件类型和大小限制。';
    if (error.code === 'FILE_PARSE_ERROR') return '文件解析失败，可删除后重传，或忽略该附件继续。';
    if (error.code === 'WORKFLOW_ERROR') return '预审流程执行失败，请稍后重试。';
    if (error.code === 'VALIDATION_ERROR') return '请求参数不合法，请检查输入内容。';
    if (error.code === 'PERSISTENCE_ERROR') return '结果保存失败，请稍后重试。';
    if (error.code === 'PERMISSION_DENIED') return '当前账号没有此操作权限。';
    if (error.code === 'USER_DISABLED') return '账号已被禁用，请联系管理员。';
    if (error.code === 'API_KEY_REVOKED') return '该密钥已被吊销，请联系管理员。';
    if (error.code === 'RATE_LIMITED') return '请求过于频繁，请稍后再试。';
    if (error.code === 'RESOURCE_NOT_FOUND') return '目标资源不存在。';
    if (error.code === 'LAST_OWNER_PROTECTED') return '组织至少需要保留一名可用的所有者。';
    if (error.code === 'SELF_OPERATION_FORBIDDEN') return '该操作会影响当前登录身份，已被系统拦截。';
    if (error.code === 'OWNER_GUARD_VIOLATION') return '管理员不能直接操作所有者成员。';
    if (error.code === 'FUNCTION_ROLE_MISMATCH') return '所选职能角色与当前组织不匹配。';
    if (error.code === 'AUTH_ERROR' || error.code === 'TOKEN_EXPIRED') return '登录状态已失效，请重新登录。';
    if (error.httpStatus === 401) return '登录状态已失效，请重新登录。';
    if (error.httpStatus === 403) return '当前账号没有此操作权限。';
    if (error.httpStatus === 404 || error.status === 'NOT_FOUND') return '资源不存在或已被删除。';
    if (error.httpStatus === 0) return '网络异常，请检查前后端服务是否启动。';
    if (error.httpStatus === 408) return '请求超时，请稍后重试。';
    if (error.httpStatus >= 500) return '服务暂时不可用，请稍后重试。';
    return error.message || fallback;
  }
  if (error instanceof Error) return error.message || fallback;
  return fallback;
}

const SESSION_STATUS_SET = new Set<SessionStatus>(['PROCESSING', 'DONE', 'FAILED']);
const CAPABILITY_STATUS_SET = new Set<CapabilityStatus>([
  'SUPPORTED',
  'PARTIALLY_SUPPORTED',
  'NOT_SUPPORTED',
  'NEED_MORE_INFO'
]);
const ROLE_SET = new Set<Role>(['OWNER', 'ADMIN', 'MEMBER', 'VIEWER']);
const USER_STATUS_SET = new Set<UserStatus>(['ACTIVE', 'DISABLED', 'PENDING_INVITE']);
const MEMBER_STATUS_SET = new Set<MemberStatus>(['INVITED', 'ACTIVE', 'SUSPENDED', 'REMOVED']);
const API_KEY_STATUS_SET = new Set<ApiKeyStatus>(['ACTIVE', 'REVOKED', 'EXPIRED']);
const CONFIDENCE_SET = new Set(['high', 'medium', 'low']);
const FILE_PARSE_STATUS_SET = new Set<FileParseStatus>(['PENDING', 'PARSING', 'DONE', 'FAILED']);

function asArray(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

function asString(value: unknown, fallback = ''): string {
  return typeof value === 'string' ? value : fallback;
}

function asNumber(value: unknown, fallback = 0): number {
  return typeof value === 'number' && Number.isFinite(value) ? value : fallback;
}

function pickString(row: Record<string, unknown>, keys: string[], fallback = ''): string {
  for (const key of keys) {
    const value = row[key];
    if (typeof value === 'string') return value;
  }
  return fallback;
}

function pickNullableString(row: Record<string, unknown>, keys: string[]): string | null {
  for (const key of keys) {
    const value = row[key];
    if (typeof value === 'string' && value.length > 0) return value;
  }
  return null;
}

function normalizeSessionStatus(value: unknown): SessionStatus {
  const text = asString(value).toUpperCase();
  if (text === 'SUCCESS') return 'DONE';
  if (SESSION_STATUS_SET.has(text as SessionStatus)) {
    return text as SessionStatus;
  }
  return 'FAILED';
}

function normalizeCapabilityStatus(value: unknown): CapabilityStatus {
  const text = asString(value).toUpperCase();
  if (CAPABILITY_STATUS_SET.has(text as CapabilityStatus)) {
    return text as CapabilityStatus;
  }
  return 'NEED_MORE_INFO';
}

function normalizeRole(value: unknown): Role {
  const text = asString(value).toUpperCase();
  if (ROLE_SET.has(text as Role)) {
    return text as Role;
  }
  return 'VIEWER';
}

function normalizeUserStatus(value: unknown): UserStatus {
  const text = asString(value).toUpperCase();
  if (USER_STATUS_SET.has(text as UserStatus)) {
    return text as UserStatus;
  }
  return 'ACTIVE';
}

function normalizeMemberStatus(value: unknown): MemberStatus {
  const text = asString(value).toUpperCase();
  if (MEMBER_STATUS_SET.has(text as MemberStatus)) {
    return text as MemberStatus;
  }
  return 'ACTIVE';
}

function normalizeApiKeyStatus(value: unknown): ApiKeyStatus {
  const text = asString(value).toUpperCase();
  if (API_KEY_STATUS_SET.has(text as ApiKeyStatus)) {
    return text as ApiKeyStatus;
  }
  return 'ACTIVE';
}

function normalizeConfidence(value: unknown): 'high' | 'medium' | 'low' | null {
  const text = asString(value).toLowerCase();
  if (CONFIDENCE_SET.has(text)) {
    return text as 'high' | 'medium' | 'low';
  }
  return null;
}

function normalizeFileParseStatus(value: unknown): FileParseStatus {
  const text = asString(value).toUpperCase();
  if (FILE_PARSE_STATUS_SET.has(text as FileParseStatus)) {
    return text as FileParseStatus;
  }
  return 'PENDING';
}

function normalizeReviewDetail(payload: unknown): PreReviewReportView {
  const data = (payload ?? {}) as Record<string, unknown>;
  const capability = (data.capability ?? {}) as Record<string, unknown>;
  const structuredRequirement = (data.structuredRequirement ?? {}) as Record<string, unknown>;

  return {
    sessionId: asString(data.sessionId),
    parentSessionId: asString(data.parentSessionId, '') || null,
    version: asNumber(data.version, 1),
    status: normalizeSessionStatus(data.status),
    summary: asString(data.summary),
    capability: {
      status: normalizeCapabilityStatus(capability.status),
      reason: asString(capability.reason),
      confidence: normalizeConfidence(capability.confidence)
    },
    evidence: asArray(data.evidence).map((item) => {
      const row = item as Record<string, unknown>;
      return {
        doc_id: asString(row.doc_id),
        doc_title: asString(row.doc_title),
        chunk_id: asString(row.chunk_id),
        snippet: asString(row.snippet),
        source_type: asString(row.source_type, 'product_doc'),
        relevance_score: asNumber(row.relevance_score),
        trust_level: asString(row.trust_level, 'MEDIUM')
      };
    }),
    structuredRequirement: {
      goal: asString(structuredRequirement.goal),
      actors: asArray(structuredRequirement.actors).map((item) => asString(item)).filter(Boolean),
      scope: asArray(structuredRequirement.scope).map((item) => asString(item)).filter(Boolean),
      constraints: asArray(structuredRequirement.constraints).map((item) => asString(item)).filter(Boolean),
      expectedOutput: asString(structuredRequirement.expectedOutput)
    },
    missingInfo: asArray(data.missingInfo).map((item) => asString(item)).filter(Boolean),
    risks: asArray(data.risks).map((item) => {
      const row = item as Record<string, unknown>;
      const rawLevel = asString(row.level, 'medium').toLowerCase();
      const level = rawLevel === 'high' || rawLevel === 'low' ? rawLevel : 'medium';
      return {
        title: asString(row.title, 'risk'),
        description: asString(row.description),
        level
      };
    }),
    impactScope: asArray(data.impactScope).map((item) => asString(item)).filter(Boolean),
    nextActions: asArray(data.nextActions).map((item) => asString(item)).filter(Boolean),
    uncertainties: asArray(data.uncertainties).map((item) => asString(item)).filter(Boolean),
    errorCode: asString(data.errorCode, '') || null,
    errorMessage: asString(data.errorMessage, '') || null
  };
}

function normalizeHistoryResponse(payload: unknown): HistoryListResponse {
  const data = (payload ?? {}) as Record<string, unknown>;
  const items = asArray(data.items).map((item) => {
    const row = item as Record<string, unknown>;
    return {
      sessionId: asString(row.sessionId),
      requestText: asString(row.requestText),
      capabilityStatus: normalizeCapabilityStatus(row.capabilityStatus),
      version: asNumber(row.version, 1),
      createdAt: asString(row.createdAt)
    } satisfies HistoryItem;
  });

  return {
    total: asNumber(data.total, items.length),
    page: asNumber(data.page, 1),
    pageSize: asNumber(data.pageSize, 20),
    items
  };
}

function normalizeListResponse<T>(payload: unknown, mapItem: (item: unknown) => T): ListResponse<T> {
  const data = (payload ?? {}) as Record<string, unknown>;
  const items = asArray(data.items).map(mapItem);
  return {
    items,
    total: asNumber(data.total, items.length),
    page: asNumber(data.page, 1),
    pageSize: asNumber(data.pageSize, 20)
  };
}

function normalizeUserItem(payload: unknown): UserListItem {
  const row = (payload ?? {}) as Record<string, unknown>;
  return {
    id: pickString(row, ['id']),
    email: pickString(row, ['email']),
    displayName: pickString(row, ['displayName', 'display_name']),
    role: normalizeRole(row.role),
    status: normalizeUserStatus(row.status),
    orgId: pickString(row, ['orgId', 'org_id']),
    createdAt: pickString(row, ['createdAt', 'created_at']),
    lastLoginAt: pickNullableString(row, ['lastLoginAt', 'last_login_at'])
  };
}

function normalizeApiKeyItem(payload: unknown): ApiKeyListItem {
  const row = (payload ?? {}) as Record<string, unknown>;
  return {
    keyId: pickString(row, ['keyId', 'key_id']),
    userId: pickString(row, ['userId', 'user_id']),
    keyPrefix: pickString(row, ['keyPrefix', 'key_prefix']),
    status: normalizeApiKeyStatus(row.status),
    name: pickString(row, ['name']),
    expiresAt: pickNullableString(row, ['expiresAt', 'expires_at']),
    lastUsedAt: pickNullableString(row, ['lastUsedAt', 'last_used_at']),
    createdAt: pickString(row, ['createdAt', 'created_at'])
  };
}

function normalizeIssuedApiKey(payload: unknown): IssueApiKeyResponse {
  const row = (payload ?? {}) as Record<string, unknown>;
  return {
    keyId: pickString(row, ['keyId', 'key_id']),
    keyPrefix: pickString(row, ['keyPrefix', 'key_prefix']),
    plainTextKey: pickString(row, ['plainTextKey', 'plain_text_key']),
    expiresAt: pickNullableString(row, ['expiresAt', 'expires_at'])
  };
}

function normalizeAuditLogItem(payload: unknown): AuditLogItem {
  const row = (payload ?? {}) as Record<string, unknown>;
  return {
    id: pickString(row, ['id']),
    actorUserId: pickNullableString(row, ['actorUserId', 'actor_user_id']),
    actorEmail: pickNullableString(row, ['actorEmail', 'actor_email']),
    action: pickString(row, ['action']),
    targetType: pickNullableString(row, ['targetType', 'target_type']),
    targetId: pickNullableString(row, ['targetId', 'target_id']),
    result: pickNullableString(row, ['result']),
    createdAt: pickString(row, ['createdAt', 'created_at'])
  };
}

function normalizeMemberItem(payload: unknown): MemberListItem {
  const row = (payload ?? {}) as Record<string, unknown>;
  return {
    membershipId: pickString(row, ['membershipId', 'membership_id']),
    userId: pickString(row, ['userId', 'user_id']),
    email: pickString(row, ['email']),
    displayName: pickString(row, ['displayName', 'display_name']),
    permissionRole: normalizeRole(row.permissionRole ?? row.role),
    memberStatus: normalizeMemberStatus(row.memberStatus ?? row.status),
    functionalRoleId: pickString(row, ['functionalRoleId', 'functional_role_id']),
    functionalRoleCode: pickString(row, ['functionalRoleCode', 'functional_role_code']),
    functionalRoleName: pickString(row, ['functionalRoleName', 'functional_role_name']),
    orgId: pickString(row, ['orgId', 'org_id']),
    createdAt: pickString(row, ['createdAt', 'created_at']),
    lastLoginAt: pickNullableString(row, ['lastLoginAt', 'last_login_at'])
  };
}

function normalizeFunctionalRoleItem(payload: unknown): FunctionalRoleView {
  const row = (payload ?? {}) as Record<string, unknown>;
  return {
    id: pickString(row, ['id']),
    orgId: pickString(row, ['orgId', 'org_id']),
    code: pickString(row, ['code']),
    name: pickString(row, ['name']),
    description: pickNullableString(row, ['description']),
    isActive: Boolean(row.isActive ?? row.is_active),
    sortOrder: asNumber(row.sortOrder ?? row.sort_order, 100),
    createdAt: pickString(row, ['createdAt', 'created_at']),
    updatedAt: pickString(row, ['updatedAt', 'updated_at'])
  };
}

type RequestOptions = {
  requiresAuth?: boolean;
  retryOnUnauthorized?: boolean;
};

async function ensureFreshAccessToken(): Promise<string> {
  const refreshed = await authClient.refresh();
  const store = useAuthStore.getState();
  if (store.user) {
    store.setSession({ accessToken: refreshed.accessToken, user: store.user });
    return refreshed.accessToken;
  }

  const user = await authClient.getMe(refreshed.accessToken);
  useAuthStore.getState().setSession({ accessToken: refreshed.accessToken, user });
  return refreshed.accessToken;
}

function buildHeaders(init: RequestInit | undefined, requiresAuth: boolean): Headers {
  const headers = new Headers(init?.headers ?? {});
  const isFormData = typeof FormData !== 'undefined' && init?.body instanceof FormData;
  if (!isFormData && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }
  if (requiresAuth) {
    const accessToken = useAuthStore.getState().accessToken;
    if (accessToken) {
      headers.set('Authorization', `Bearer ${accessToken}`);
    }
  }
  return headers;
}

async function performRequest(path: string, init?: RequestInit, options?: RequestOptions): Promise<Response> {
  const requiresAuth = options?.requiresAuth ?? true;
  const retryOnUnauthorized = options?.retryOnUnauthorized ?? true;
  const url = `${API_BASE_URL}${path}`;
  const requestInit: RequestInit = {
    ...init,
    credentials: 'include',
    cache: 'no-store',
    headers: buildHeaders(init, requiresAuth)
  };

  let response: Response;
  try {
    response = await fetchWithTimeout(url, requestInit);
  } catch (error) {
    if (error instanceof ApiClientError) throw error;
    throw new ApiClientError('网络异常，请检查服务是否可访问。', { httpStatus: 0 });
  }

  if (response.ok) {
    return response;
  }

  const detail = await parseErrorResponse(response);
  const isUnauthorized = response.status === 401;
  if (requiresAuth && retryOnUnauthorized && isUnauthorized) {
    try {
      const nextToken = await ensureFreshAccessToken();
      const retryHeaders = buildHeaders(init, requiresAuth);
      retryHeaders.set('Authorization', `Bearer ${nextToken}`);
      const retryResponse = await fetchWithTimeout(url, {
        ...requestInit,
        headers: retryHeaders
      });
      if (retryResponse.ok) {
        return retryResponse;
      }
      const retryDetail = await parseErrorResponse(retryResponse);
      throw new ApiClientError(retryDetail?.message ?? `Request failed: ${retryResponse.status}`, {
        httpStatus: retryResponse.status,
        code: retryDetail?.error_code,
        status: retryDetail?.status
      });
    } catch (refreshError) {
      useAuthStore.getState().clearSession();
      if (refreshError instanceof ApiClientError) {
        throw refreshError;
      }
      throw new ApiClientError('登录状态已失效，请重新登录。', {
        httpStatus: 401,
        code: 'AUTH_ERROR'
      });
    }
  }

  throw new ApiClientError(detail?.message ?? `Request failed: ${response.status}`, {
    httpStatus: response.status,
    code: detail?.error_code,
    status: detail?.status
  });
}

async function requestJson<T>(path: string, init?: RequestInit, options?: RequestOptions): Promise<T> {
  const response = await performRequest(path, init, options);
  return (await response.json()) as T;
}

export const apiClient = {
  createPrereview(payload: CreatePreReviewForm) {
    return requestJson<{ sessionId: string; status: string }>('/api/prereview', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  async getPrereviewDetail(sessionId: string) {
    const raw = await requestJson<unknown>(`/api/prereview/${sessionId}`);
    return normalizeReviewDetail(raw);
  },

  regeneratePrereview(
    sessionId: string,
    payload: {
      additionalContext: string;
      attachments?: UploadedFileRef[];
    }
  ) {
    const trimmedContext = payload.additionalContext.trim();
    const attachments = payload.attachments ?? [];
    return requestJson<{ sessionId: string; status: string }>(`/api/prereview/${sessionId}/regenerate`, {
      method: 'POST',
      body: JSON.stringify({
        additionalContext: trimmedContext,
        attachments: attachments.map((f) => ({ fileId: f.fileId }))
      })
    });
  },

  async getHistory(query: HistoryQuery) {
    const page = Math.max(1, Math.trunc(query.page));
    const pageSize = Math.min(100, Math.max(1, Math.trunc(query.pageSize)));
    const params = new URLSearchParams();
    if (query.keyword) params.set('keyword', query.keyword);
    if (query.capabilityStatus) params.set('capabilityStatus', query.capabilityStatus);
    params.set('page', String(page));
    params.set('pageSize', String(pageSize));
    const raw = await requestJson<unknown>(`/api/history?${params.toString()}`);
    return normalizeHistoryResponse(raw);
  },

  async uploadFile(file: File): Promise<UploadedFileRef> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await performRequest(
      '/api/files/upload',
      {
        method: 'POST',
        body: formData
      },
      { requiresAuth: true, retryOnUnauthorized: true }
    );

    const raw = (await response.json()) as Record<string, unknown>;
    return {
      fileId: asString(raw.fileId),
      fileName: asString(raw.fileName),
      fileSize: asNumber(raw.fileSize),
      parseStatus: normalizeFileParseStatus(raw.parseStatus)
    };
  },

  async createUser(payload: CreateUserRequest): Promise<UserListItem> {
    const raw = await requestJson<unknown>('/api/admin/users', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
    return normalizeUserItem(raw);
  },

  async listUsers(query: ListUsersQuery): Promise<ListResponse<UserListItem>> {
    const page = Math.max(1, Math.trunc(query.page));
    const pageSize = Math.min(100, Math.max(1, Math.trunc(query.pageSize)));
    const params = new URLSearchParams();
    if (query.query) params.set('query', query.query);
    if (query.role) params.set('role', query.role);
    if (query.status) params.set('status', query.status);
    params.set('page', String(page));
    params.set('pageSize', String(pageSize));
    const raw = await requestJson<unknown>(`/api/admin/users?${params.toString()}`);
    return normalizeListResponse(raw, normalizeUserItem);
  },

  async listMembers(query: ListMembersQuery): Promise<ListResponse<MemberListItem>> {
    const page = Math.max(1, Math.trunc(query.page));
    const pageSize = Math.min(100, Math.max(1, Math.trunc(query.pageSize)));
    const params = new URLSearchParams();
    if (query.query) params.set('query', query.query);
    if (query.permissionRole) params.set('permissionRole', query.permissionRole);
    if (query.memberStatus) params.set('memberStatus', query.memberStatus);
    if (query.functionalRoleId) params.set('functionalRoleId', query.functionalRoleId);
    params.set('page', String(page));
    params.set('pageSize', String(pageSize));
    const raw = await requestJson<unknown>(`/api/admin/members?${params.toString()}`);
    return normalizeListResponse(raw, normalizeMemberItem);
  },

  async updateUserStatus(userId: string, payload: UpdateUserStatusRequest): Promise<UserListItem> {
    const raw = await requestJson<unknown>(`/api/admin/users/${userId}/status`, {
      method: 'PATCH',
      body: JSON.stringify(payload)
    });
    return normalizeUserItem(raw);
  },

  async updateUserRole(userId: string, payload: UpdateUserRoleRequest): Promise<UserListItem> {
    const raw = await requestJson<unknown>(`/api/admin/users/${userId}/role`, {
      method: 'PATCH',
      body: JSON.stringify(payload)
    });
    return normalizeUserItem(raw);
  },

  async updateMemberRole(memberId: string, payload: UpdateMemberRoleRequest): Promise<MemberListItem> {
    const raw = await requestJson<unknown>(`/api/admin/members/${memberId}/role`, {
      method: 'PATCH',
      body: JSON.stringify(payload)
    });
    return normalizeMemberItem(raw);
  },

  async updateMemberStatus(memberId: string, payload: UpdateMemberStatusRequest): Promise<MemberListItem> {
    const raw = await requestJson<unknown>(`/api/admin/members/${memberId}/status`, {
      method: 'PATCH',
      body: JSON.stringify(payload)
    });
    return normalizeMemberItem(raw);
  },

  async updateMemberFunctionalRole(
    memberId: string,
    payload: UpdateMemberFunctionalRoleRequest
  ): Promise<MemberListItem> {
    const raw = await requestJson<unknown>(`/api/admin/members/${memberId}/functional-role`, {
      method: 'PATCH',
      body: JSON.stringify(payload)
    });
    return normalizeMemberItem(raw);
  },

  async listFunctionalRoles(query: ListFunctionalRolesQuery): Promise<ListResponse<FunctionalRoleView>> {
    const page = Math.max(1, Math.trunc(query.page));
    const pageSize = Math.min(100, Math.max(1, Math.trunc(query.pageSize)));
    const params = new URLSearchParams();
    if (typeof query.isActive === 'boolean') params.set('isActive', query.isActive ? 'true' : 'false');
    params.set('page', String(page));
    params.set('pageSize', String(pageSize));
    const raw = await requestJson<unknown>(`/api/admin/functional-roles?${params.toString()}`);
    return normalizeListResponse(raw, normalizeFunctionalRoleItem);
  },

  async createFunctionalRole(payload: CreateFunctionalRoleRequest): Promise<FunctionalRoleView> {
    const raw = await requestJson<unknown>('/api/admin/functional-roles', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
    return normalizeFunctionalRoleItem(raw);
  },

  async updateFunctionalRoleStatus(
    roleId: string,
    payload: UpdateFunctionalRoleStatusRequest
  ): Promise<FunctionalRoleView> {
    const raw = await requestJson<unknown>(`/api/admin/functional-roles/${roleId}/status`, {
      method: 'PATCH',
      body: JSON.stringify(payload)
    });
    return normalizeFunctionalRoleItem(raw);
  },

  async issueApiKey(payload: IssueApiKeyRequest): Promise<IssueApiKeyResponse> {
    const raw = await requestJson<unknown>('/api/admin/api-keys', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
    return normalizeIssuedApiKey(raw);
  },

  async listApiKeys(query: ListApiKeysQuery): Promise<ListResponse<ApiKeyListItem>> {
    const page = Math.max(1, Math.trunc(query.page));
    const pageSize = Math.min(100, Math.max(1, Math.trunc(query.pageSize)));
    const params = new URLSearchParams();
    if (query.userId) params.set('userId', query.userId);
    if (query.status) params.set('status', query.status);
    params.set('page', String(page));
    params.set('pageSize', String(pageSize));
    const raw = await requestJson<unknown>(`/api/admin/api-keys?${params.toString()}`);
    return normalizeListResponse(raw, normalizeApiKeyItem);
  },

  revokeApiKey(keyId: string) {
    return requestJson<{ success: true }>(`/api/admin/api-keys/${keyId}/revoke`, {
      method: 'POST',
      body: JSON.stringify({})
    });
  },

  async listAuditLogs(query: ListAuditLogsQuery): Promise<ListResponse<AuditLogItem>> {
    const page = Math.max(1, Math.trunc(query.page));
    const pageSize = Math.min(100, Math.max(1, Math.trunc(query.pageSize)));
    const params = new URLSearchParams();
    if (query.actorUserId) params.set('actorUserId', query.actorUserId);
    if (query.action) params.set('action', query.action);
    params.set('page', String(page));
    params.set('pageSize', String(pageSize));
    const raw = await requestJson<unknown>(`/api/admin/audit-logs?${params.toString()}`);
    return normalizeListResponse(raw, normalizeAuditLogItem);
  }
};
