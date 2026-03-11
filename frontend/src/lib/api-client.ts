import {
  CapabilityStatus,
  CreatePreReviewForm,
  HistoryItem,
  HistoryListResponse,
  HistoryQuery,
  PreReviewReportView,
  ReviewViewStatus,
  SessionStatus,
  UploadedFileRef
} from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://127.0.0.1:8000';
const API_TOKEN = process.env.NEXT_PUBLIC_API_TOKEN ?? 'dev-token';

type ApiError = {
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

export function getApiErrorMessage(error: unknown, fallback = '请求失败，请稍后重试') {
  if (isApiClientError(error)) {
    if (error.httpStatus === 401) return '鉴权失败，请检查 API Token。';
    if (error.httpStatus === 404 || error.status === 'NOT_FOUND') return '资源不存在或已被删除。';
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
const CONFIDENCE_SET = new Set(['high', 'medium', 'low']);

function asArray(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

function asString(value: unknown, fallback = ''): string {
  return typeof value === 'string' ? value : fallback;
}

function asNumber(value: unknown, fallback = 0): number {
  return typeof value === 'number' && Number.isFinite(value) ? value : fallback;
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

function normalizeConfidence(value: unknown): 'high' | 'medium' | 'low' | null {
  const text = asString(value).toLowerCase();
  if (CONFIDENCE_SET.has(text)) {
    return text as 'high' | 'medium' | 'low';
  }
  return null;
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
      detail = body?.detail ?? body;
    } catch {
      // ignore parse errors and fallback to generic error message
    }
    const message = detail?.message ?? `Request failed: ${response.status}`;
    throw new ApiClientError(message, {
      httpStatus: response.status,
      code: detail?.error_code,
      status: detail?.status
    });
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
  async getReviewDetail(sessionId: string) {
    const raw = await request<unknown>(`/api/prereview/${sessionId}`);
    return normalizeReviewDetail(raw);
  },
  regenerateReview(sessionId: string, additionalContext: string, attachments: UploadedFileRef[] = []) {
    return request<{ sessionId: string; status: string }>(`/api/prereview/${sessionId}/regenerate`, {
      method: 'POST',
      body: JSON.stringify({ additionalContext, attachments: attachments.map((f) => ({ fileId: f.fileId })) })
    });
  },
  async getHistory(query: HistoryQuery) {
    const params = new URLSearchParams();
    if (query.keyword) params.set('keyword', query.keyword);
    if (query.capabilityStatus) params.set('capabilityStatus', query.capabilityStatus);
    params.set('page', String(query.page));
    params.set('pageSize', String(query.pageSize));
    const raw = await request<unknown>(`/api/history?${params.toString()}`);
    return normalizeHistoryResponse(raw);
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
        detail = body?.detail ?? body;
      } catch {
        // ignore parse errors and fallback to generic error message
      }
      throw new ApiClientError(detail?.message ?? 'File upload failed', {
        httpStatus: response.status,
        code: detail?.error_code,
        status: detail?.status
      });
    }

    return (await response.json()) as UploadedFileRef;
  }
};
