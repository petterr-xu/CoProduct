'use client';

import { useMutation, useQuery } from '@tanstack/react-query';

import { apiClient } from '@/lib/api-client';
import { QUERY_KEYS } from '@/lib/constants';
import { HistoryQuery } from '@/types';

export function useCreatePreReview() {
  return useMutation({
    mutationFn: apiClient.createPreReview
  });
}

export function useReviewDetail(sessionId: string) {
  return useQuery({
    queryKey: QUERY_KEYS.reviewDetail(sessionId),
    queryFn: () => apiClient.getReviewDetail(sessionId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === 'PROCESSING' ? 2000 : false;
    },
    enabled: Boolean(sessionId)
  });
}

export function useRegenerateReview(sessionId: string) {
  return useMutation({
    mutationFn: (payload: { additionalContext: string }) =>
      apiClient.regenerateReview(sessionId, payload.additionalContext)
  });
}

export function useHistoryList(query: HistoryQuery) {
  return useQuery({
    queryKey: QUERY_KEYS.history(query.keyword ?? '', query.capabilityStatus ?? '', query.page, query.pageSize),
    queryFn: () => apiClient.getHistory(query)
  });
}
