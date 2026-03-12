'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { apiClient, isApiClientError } from '@/lib/api-client';
import { QUERY_KEYS } from '@/lib/constants';
import {
  CreateFunctionalRoleRequest,
  CreateUserRequest,
  IssueApiKeyRequest,
  ListFunctionalRolesQuery,
  ListMembersQuery,
  ListMemberOptionsQuery,
  ListApiKeysQuery,
  ListAuditLogsQuery,
  ListUsersQuery,
  UpdateFunctionalRoleStatusRequest,
  UpdateMemberFunctionalRoleRequest,
  UpdateMemberRoleRequest,
  UpdateMemberStatusRequest,
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
      await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.adminMembersRoot });
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
      await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.adminMembersRoot });
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
      await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.adminMembersRoot });
      await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.adminAuditLogsRoot });
    }
  });
}

export function useAdminMembers(query: ListMembersQuery) {
  return useQuery({
    queryKey: QUERY_KEYS.adminMembers(
      query.query ?? '',
      query.permissionRole ?? '',
      query.memberStatus ?? '',
      query.functionalRoleId ?? '',
      query.page,
      query.pageSize
    ),
    queryFn: () => apiClient.listMembers(query),
    retry: (failureCount, error) => {
      if (isApiClientError(error) && error.code === 'VALIDATION_ERROR') {
        return false;
      }
      return failureCount < 2;
    },
    placeholderData: (previous) => previous
  });
}

export function useAdminUpdateMemberRole() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: { memberId: string; body: UpdateMemberRoleRequest }) =>
      apiClient.updateMemberRole(payload.memberId, payload.body),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.adminMembersRoot });
      await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.adminUsersRoot });
      await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.adminAuditLogsRoot });
    }
  });
}

export function useAdminUpdateMemberStatus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: { memberId: string; body: UpdateMemberStatusRequest }) =>
      apiClient.updateMemberStatus(payload.memberId, payload.body),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.adminMembersRoot });
      await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.adminUsersRoot });
      await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.adminApiKeysRoot });
      await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.adminAuditLogsRoot });
    }
  });
}

export function useAdminUpdateMemberFunctionalRole() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: { memberId: string; body: UpdateMemberFunctionalRoleRequest }) =>
      apiClient.updateMemberFunctionalRole(payload.memberId, payload.body),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.adminMembersRoot });
      await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.adminFunctionalRolesRoot });
      await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.adminAuditLogsRoot });
    }
  });
}

export function useAdminFunctionalRoles(query: ListFunctionalRolesQuery) {
  return useQuery({
    queryKey: QUERY_KEYS.adminFunctionalRoles(
      typeof query.isActive === 'boolean' ? String(query.isActive) : '',
      query.page,
      query.pageSize
    ),
    queryFn: () => apiClient.listFunctionalRoles(query),
    retry: (failureCount, error) => {
      if (isApiClientError(error) && error.code === 'VALIDATION_ERROR') {
        return false;
      }
      return failureCount < 2;
    },
    placeholderData: (previous) => previous
  });
}

export function useAdminCreateFunctionalRole() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateFunctionalRoleRequest) => apiClient.createFunctionalRole(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.adminFunctionalRolesRoot });
      await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.adminMembersRoot });
      await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.adminAuditLogsRoot });
    }
  });
}

export function useAdminUpdateFunctionalRoleStatus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: { roleId: string; body: UpdateFunctionalRoleStatusRequest }) =>
      apiClient.updateFunctionalRoleStatus(payload.roleId, payload.body),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.adminFunctionalRolesRoot });
      await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.adminMembersRoot });
      await queryClient.invalidateQueries({ queryKey: QUERY_KEYS.adminAuditLogsRoot });
    }
  });
}

export function useAdminApiKeys(query: ListApiKeysQuery) {
  return useQuery({
    queryKey: QUERY_KEYS.adminApiKeys(query.userId ?? '', query.orgId ?? '', query.status ?? '', query.page, query.pageSize),
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

export function useAdminMemberOptions(
  query: ListMemberOptionsQuery,
  options?: {
    enabled?: boolean;
  }
) {
  const enabled = options?.enabled ?? true;
  const normalizedQuery = query.query.trim();
  const normalizedLimit = query.limit ?? 20;
  return useQuery({
    queryKey: QUERY_KEYS.adminMemberOptions(query.orgId ?? '', normalizedQuery, normalizedLimit),
    queryFn: ({ signal }) =>
      apiClient.listMemberOptions(
        {
          ...query,
          query: normalizedQuery,
          limit: normalizedLimit
        },
        { signal }
      ),
    enabled: enabled && normalizedQuery.length >= 2,
    retry: (failureCount, error) => {
      if (error instanceof DOMException && error.name === 'AbortError') {
        return false;
      }
      if (isApiClientError(error) && error.code === 'VALIDATION_ERROR') {
        return false;
      }
      return failureCount < 2;
    }
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
