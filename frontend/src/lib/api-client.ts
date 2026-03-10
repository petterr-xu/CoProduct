import {
  CreatePreReviewForm,
  HistoryListResponse,
  HistoryQuery,
  PreReviewReportView,
  UploadedFileRef
} from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://127.0.0.1:8000';
const API_TOKEN = process.env.NEXT_PUBLIC_API_TOKEN ?? 'dev-token';

type ApiError = {
  error_code?: string;
  message?: string;
  status?: string;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${API_TOKEN}`,
      ...(init?.headers ?? {})
    },
    cache: 'no-store'
  });

  if (!response.ok) {
    let detail: ApiError | undefined;
    try {
      const body = await response.json();
      detail = body?.detail;
    } catch {
      // ignore parse errors and fallback to generic error message
    }
    const message = detail?.message ?? `Request failed: ${response.status}`;
    const error = new Error(message);
    (error as Error & { code?: string; status?: string }).code = detail?.error_code;
    (error as Error & { code?: string; status?: string }).status = detail?.status;
    throw error;
  }

  return (await response.json()) as T;
}

export const apiClient = {
  createPreReview(payload: CreatePreReviewForm) {
    return request<{ sessionId: string; status: string }>('/api/prereview', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },
  getReviewDetail(sessionId: string) {
    return request<PreReviewReportView>(`/api/prereview/${sessionId}`);
  },
  regenerateReview(sessionId: string, additionalContext: string, attachments: UploadedFileRef[] = []) {
    return request<{ sessionId: string; status: string }>(`/api/prereview/${sessionId}/regenerate`, {
      method: 'POST',
      body: JSON.stringify({ additionalContext, attachments: attachments.map((f) => ({ fileId: f.fileId })) })
    });
  },
  getHistory(query: HistoryQuery) {
    const params = new URLSearchParams();
    if (query.keyword) params.set('keyword', query.keyword);
    if (query.capabilityStatus) params.set('capabilityStatus', query.capabilityStatus);
    params.set('page', String(query.page));
    params.set('pageSize', String(query.pageSize));
    return request<HistoryListResponse>(`/api/history?${params.toString()}`);
  },
  async uploadFile(file: File): Promise<UploadedFileRef> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/api/files/upload`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${API_TOKEN}`
      },
      body: formData
    });

    if (!response.ok) {
      let detail: ApiError | undefined;
      try {
        const body = await response.json();
        detail = body?.detail;
      } catch {
        // ignore parse errors and fallback to generic error message
      }
      throw new Error(detail?.message ?? 'File upload failed');
    }

    return (await response.json()) as UploadedFileRef;
  }
};
