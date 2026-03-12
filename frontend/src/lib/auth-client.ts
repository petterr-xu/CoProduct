import {
  AuthContextOrgView,
  AuthContextResponse,
  AuthContextScopeMode,
  AuthTokenResponse,
  AuthUserView,
  RefreshResponse,
  Role,
  UserStatus
} from '@/types';

import { ApiClientError, fetchWithTimeout, getCookieValue, parseErrorResponse } from '@/lib/http-client';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';

type KeyLoginRequest = {
  apiKey: string;
  deviceInfo?: string;
};

type LogoutRequest = {
  allDevices?: boolean;
};

let refreshPromise: Promise<RefreshResponse> | null = null;
const ROLE_SET = new Set<Role>(['OWNER', 'ADMIN', 'MEMBER', 'VIEWER']);
const USER_STATUS_SET = new Set<UserStatus>(['ACTIVE', 'DISABLED', 'PENDING_INVITE']);
const CONTEXT_SCOPE_MODE_SET = new Set<AuthContextScopeMode>(['ORG_SCOPED', 'USER_SCOPED']);

function authEndpoint(path: string): string {
  return `${API_BASE_URL}/api/auth${path}`;
}

function asString(value: unknown, fallback = ''): string {
  return typeof value === 'string' ? value : fallback;
}

function pickString(row: Record<string, unknown>, keys: string[], fallback = ''): string {
  for (const key of keys) {
    const value = row[key];
    if (typeof value === 'string') return value;
  }
  return fallback;
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

function normalizeContextScopeMode(value: unknown): AuthContextScopeMode {
  const text = asString(value).toUpperCase();
  if (CONTEXT_SCOPE_MODE_SET.has(text as AuthContextScopeMode)) {
    return text as AuthContextScopeMode;
  }
  return 'ORG_SCOPED';
}

function normalizeAuthUserView(payload: unknown): AuthUserView {
  const row = (payload ?? {}) as Record<string, unknown>;
  return {
    id: pickString(row, ['id']),
    email: pickString(row, ['email']),
    displayName: pickString(row, ['displayName', 'display_name']),
    role: normalizeRole(row.role),
    orgId: pickString(row, ['orgId', 'org_id']),
    status: normalizeUserStatus(row.status)
  };
}

function normalizeContextOrg(payload: unknown): AuthContextOrgView | null {
  if (!payload || typeof payload !== 'object') return null;
  const row = payload as Record<string, unknown>;
  const orgId = pickString(row, ['orgId', 'org_id']);
  if (!orgId) return null;
  return {
    orgId,
    orgName: pickString(row, ['orgName', 'org_name'], orgId)
  };
}

function normalizeAuthContextResponse(payload: unknown): AuthContextResponse {
  const row = (payload ?? {}) as Record<string, unknown>;
  const user = normalizeAuthUserView(row.user);
  const activeOrg = normalizeContextOrg(row.activeOrg ?? row.active_org);
  const rawAvailableOrgs = Array.isArray(row.availableOrgs ?? row.available_orgs)
    ? ((row.availableOrgs ?? row.available_orgs) as unknown[])
    : [];
  const availableOrgs = rawAvailableOrgs
    .map((item) => normalizeContextOrg(item))
    .filter((item): item is AuthContextOrgView => item !== null);

  if (activeOrg && !availableOrgs.some((item) => item.orgId === activeOrg.orgId)) {
    availableOrgs.unshift(activeOrg);
  }

  return {
    user,
    activeOrg,
    availableOrgs,
    scopeMode: normalizeContextScopeMode(row.scopeMode ?? row.scope_mode)
  };
}

async function parseAuthResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const detail = await parseErrorResponse(response);
    throw new ApiClientError(detail?.message ?? 'Authentication failed', {
      httpStatus: response.status,
      code: detail?.error_code,
      status: detail?.status
    });
  }
  return (await response.json()) as T;
}

function csrfHeader(): HeadersInit {
  const csrfToken = getCookieValue('csrf_token');
  return csrfToken ? { 'X-CSRF-Token': csrfToken } : {};
}

export const authClient = {
  async keyLogin(payload: KeyLoginRequest): Promise<AuthTokenResponse> {
    let response: Response;
    try {
      response = await fetchWithTimeout(authEndpoint('/key-login'), {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });
    } catch (error) {
      if (error instanceof ApiClientError) throw error;
      throw new ApiClientError('网络异常，请检查服务是否可访问。', { httpStatus: 0 });
    }
    return parseAuthResponse<AuthTokenResponse>(response);
  },

  async getMe(accessToken: string): Promise<AuthUserView> {
    let response: Response;
    try {
      response = await fetchWithTimeout(authEndpoint('/me'), {
        method: 'GET',
        credentials: 'include',
        headers: {
          Authorization: `Bearer ${accessToken}`
        }
      });
    } catch (error) {
      if (error instanceof ApiClientError) throw error;
      throw new ApiClientError('网络异常，请检查服务是否可访问。', { httpStatus: 0 });
    }
    return parseAuthResponse<AuthUserView>(response);
  },

  async getContext(accessToken: string): Promise<AuthContextResponse> {
    let response: Response;
    try {
      response = await fetchWithTimeout(authEndpoint('/context'), {
        method: 'GET',
        credentials: 'include',
        headers: {
          Authorization: `Bearer ${accessToken}`
        }
      });
    } catch (error) {
      if (error instanceof ApiClientError) throw error;
      throw new ApiClientError('网络异常，请检查服务是否可访问。', { httpStatus: 0 });
    }
    const payload = await parseAuthResponse<unknown>(response);
    return normalizeAuthContextResponse(payload);
  },

  async refresh(): Promise<RefreshResponse> {
    if (refreshPromise) return refreshPromise;

    refreshPromise = (async () => {
      let response: Response;
      try {
        response = await fetchWithTimeout(authEndpoint('/refresh'), {
          method: 'POST',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
            ...csrfHeader()
          },
          body: JSON.stringify({})
        });
      } catch (error) {
        if (error instanceof ApiClientError) throw error;
        throw new ApiClientError('网络异常，请检查服务是否可访问。', { httpStatus: 0 });
      }
      return parseAuthResponse<RefreshResponse>(response);
    })();

    try {
      return await refreshPromise;
    } finally {
      refreshPromise = null;
    }
  },

  async logout(payload: LogoutRequest = {}): Promise<{ success: true }> {
    let response: Response;
    try {
      response = await fetchWithTimeout(authEndpoint('/logout'), {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          ...csrfHeader()
        },
        body: JSON.stringify(payload)
      });
    } catch (error) {
      if (error instanceof ApiClientError) throw error;
      throw new ApiClientError('网络异常，请检查服务是否可访问。', { httpStatus: 0 });
    }
    return parseAuthResponse<{ success: true }>(response);
  }
};
