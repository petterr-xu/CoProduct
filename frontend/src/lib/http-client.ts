import { ReviewViewStatus } from '@/types';

const REQUEST_TIMEOUT_MS = 15_000;

export type ApiErrorPayload = {
  error_code?: string;
  message?: string;
  status?: ReviewViewStatus | string;
};

export class ApiClientError extends Error {
  code?: string;
  status?: ReviewViewStatus | string;
  httpStatus: number;

  constructor(message: string, options: { httpStatus: number; code?: string; status?: ReviewViewStatus | string }) {
    super(message);
    this.name = 'ApiClientError';
    this.httpStatus = options.httpStatus;
    this.code = options.code;
    this.status = options.status;
  }
}

export function isApiClientError(error: unknown): error is ApiClientError {
  return error instanceof ApiClientError;
}

export async function fetchWithTimeout(url: string, init: RequestInit): Promise<Response> {
  const timeoutController = new AbortController();
  let timedOut = false;
  const timeoutId = setTimeout(() => {
    timedOut = true;
    timeoutController.abort();
  }, REQUEST_TIMEOUT_MS);

  const externalSignal = init.signal;
  const mergedController = new AbortController();
  const abortMergedSignal = () => mergedController.abort();

  if (externalSignal?.aborted || timeoutController.signal.aborted) {
    mergedController.abort();
  } else {
    externalSignal?.addEventListener('abort', abortMergedSignal, { once: true });
    timeoutController.signal.addEventListener('abort', abortMergedSignal, { once: true });
  }

  try {
    return await fetch(url, { ...init, signal: mergedController.signal });
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      if (timedOut) {
        throw new ApiClientError('请求超时，请稍后重试。', { httpStatus: 408 });
      }
      throw error;
    }
    throw error;
  } finally {
    clearTimeout(timeoutId);
    externalSignal?.removeEventListener('abort', abortMergedSignal);
    timeoutController.signal.removeEventListener('abort', abortMergedSignal);
  }
}

export async function parseErrorResponse(response: Response): Promise<ApiErrorPayload | undefined> {
  try {
    const body = await response.json();
    const detail = body?.detail ?? body;
    if (typeof detail === 'object' && detail !== null) {
      return detail as ApiErrorPayload;
    }
    return undefined;
  } catch {
    return undefined;
  }
}

export function getCookieValue(name: string): string | null {
  if (typeof document === 'undefined') return null;
  const encodedName = encodeURIComponent(name);
  const chunks = document.cookie.split(';');
  for (const chunk of chunks) {
    const trimmed = chunk.trim();
    if (!trimmed.startsWith(`${encodedName}=`)) continue;
    const value = trimmed.slice(encodedName.length + 1);
    return decodeURIComponent(value);
  }
  return null;
}
