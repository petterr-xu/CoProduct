'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { apiClient, isApiClientError } from '@/lib/api-client';
import { QUERY_KEYS } from '@/lib/constants';
import {
  CreateUserRequest,
  IssueApiKeyRequest,
  ListApiKeysQuery,
  ListAuditLogsQuery,
  ListUsersQuery,
  UpdateUserRoleRequest,
  UpdateUserStatusRequest
} from '@/types';

export function useAdminUsers(query: ListUsersQuery) {
  return useQuery({
    queryKey: QUERY_KEYS.adminUsers(query.query ?? '', query.role ?? '', query.status ?? '', query.page, query.pageSize),
    queryFn: () => apiClient.listUsers(query),
    retry: (failureCount, error) => {
      if (isApiClientError(error) && error.code === 'VALIDATION_ERROR') {
        return false;
      }
      return failureCount < 2;
    },
    placeholderData: (previous) => previous
  });
}

export function useAdminCreateUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateUserRequest) => apiClient.createUser(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.adminUsersRoot });
      await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.adminAuditLogsRoot });
    }
  });
}

export function useAdminUpdateUserStatus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: { userId: string; body: UpdateUserStatusRequest }) =>
      apiClient.updateUserStatus(payload.userId, payload.body),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.adminUsersRoot });
      await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.adminAuditLogsRoot });
    }
  });
}

export function useAdminUpdateUserRole() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: { userId: string; body: UpdateUserRoleRequest }) =>
      apiClient.updateUserRole(payload.userId, payload.body),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.adminUsersRoot });
      await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.adminAuditLogsRoot });
    }
  });
}

export function useAdminApiKeys(query: ListApiKeysQuery) {
  return useQuery({
    queryKey: QUERY_KEYS.adminApiKeys(query.userId ?? '', query.status ?? '', query.page, query.pageSize),
    queryFn: () => apiClient.listApiKeys(query),
    retry: (failureCount, error) => {
      if (isApiClientError(error) && error.code === 'VALIDATION_ERROR') {
        return false;
      }
      return failureCount < 2;
    },
    placeholderData: (previous) => previous
  });
}

export function useAdminIssueApiKey() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: IssueApiKeyRequest) => apiClient.issueApiKey(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.adminApiKeysRoot });
      await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.adminAuditLogsRoot });
    }
  });
}

export function useAdminRevokeApiKey() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (keyId: string) => apiClient.revokeApiKey(keyId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.adminApiKeysRoot });
      await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.adminAuditLogsRoot });
    }
  });
}

export function useAdminAuditLogs(query: ListAuditLogsQuery) {
  return useQuery({
    queryKey: QUERY_KEYS.adminAuditLogs(query.actorUserId ?? '', query.action ?? '', query.page, query.pageSize),
    queryFn: () => apiClient.listAuditLogs(query),
    retry: (failureCount, error) => {
      if (isApiClientError(error) && error.code === 'VALIDATION_ERROR') {
        return false;
      }
      return failureCount < 2;
    },
    placeholderData: (previous) => previous
  });
}
