'use client';

import { useEffect, useRef } from 'react';
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
  const processingSinceRef = useRef<number | null>(null);

  const query = useQuery({
    queryKey: QUERY_KEYS.prereviewDetail(sessionId),
    queryFn: () => apiClient.getPrereviewDetail(sessionId),
    retry: (failureCount, error) => {
      if (isApiClientError(error) && (error.status === 'NOT_FOUND' || error.httpStatus === 404)) {
        return false;
      }
      return failureCount < 2;
    },
    refetchInterval: () => {
      const since = processingSinceRef.current;
      if (since === null) return false;
      const elapsed = Date.now() - since;
      return elapsed < 60_000 ? 2_000 : 5_000;
    },
    enabled: Boolean(sessionId)
  });

  useEffect(() => {
    const status = query.data?.status;
    if (status === 'PROCESSING') {
      if (processingSinceRef.current === null) {
        processingSinceRef.current = Date.now();
      }
      return;
    }
    processingSinceRef.current = null;
  }, [query.data?.status]);

  return query;
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
