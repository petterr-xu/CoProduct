import { CapabilityStatus } from '@/types';

export const STATUS_COLOR_MAP: Record<CapabilityStatus, string> = {
  SUPPORTED: 'text-success bg-green-100 border-green-200',
  PARTIALLY_SUPPORTED: 'text-warning bg-amber-100 border-amber-200',
  NOT_SUPPORTED: 'text-danger bg-red-100 border-red-200',
  NEED_MORE_INFO: 'text-info bg-blue-100 border-blue-200'
};

export const QUERY_KEYS = {
  reviewDetail: (sessionId: string) => ['review-detail', sessionId] as const,
  history: (keyword: string, capabilityStatus: string, page: number, pageSize: number) =>
    ['history', keyword, capabilityStatus, page, pageSize] as const
};
