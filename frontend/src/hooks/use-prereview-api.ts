'use client';

import { useMutation, useQuery } from '@tanstack/react-query';

import { apiClient, isApiClientError } from '@/lib/api-client';
import { QUERY_KEYS } from '@/lib/constants';
import { HistoryQuery, RegeneratePreReviewPayload } from '@/types';

export function useCreatePrereview() {
  return useMutation({
    mutationFn: apiClient.createPrereview
  });
}

export function usePrereviewDetail(sessionId: string) {
  return useQuery({
    queryKey: QUERY_KEYS.prereviewDetail(sessionId),
    queryFn: () => apiClient.getPrereviewDetail(sessionId),
    retry: (failureCount, error) => {
      if (isApiClientError(error) && (error.status === 'NOT_FOUND' || error.httpStatus === 404)) {
        return false;
      }
      return failureCount < 2;
    },
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === 'PROCESSING' ? 2000 : false;
    },
    enabled: Boolean(sessionId)
  });
}

export function useRegeneratePrereview(sessionId: string) {
  return useMutation({
    mutationFn: (payload: RegeneratePreReviewPayload) => apiClient.regeneratePrereview(sessionId, payload)
  });
}

export function useHistoryList(query: HistoryQuery) {
  return useQuery({
    queryKey: QUERY_KEYS.history(query.keyword ?? '', query.capabilityStatus ?? '', query.page, query.pageSize),
    queryFn: () => apiClient.getHistory(query),
    retry: (failureCount, error) => {
      if (isApiClientError(error) && error.code === 'VALIDATION_ERROR') {
        return false;
      }
      return failureCount < 2;
    },
    placeholderData: (previous) => previous
  });
}
