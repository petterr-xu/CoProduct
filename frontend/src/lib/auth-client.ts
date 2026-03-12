import { AuthTokenResponse, AuthUserView, RefreshResponse } from '@/types';

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

function authEndpoint(path: string): string {
  return `${API_BASE_URL}/api/auth${path}`;
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
