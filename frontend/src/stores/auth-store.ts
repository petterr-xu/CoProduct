'use client';

import { create } from 'zustand';

import { AuthContextResponse, AuthUserView, Role } from '@/types';

type AuthState = {
  accessToken: string | null;
  user: AuthUserView | null;
  authContext: AuthContextResponse | null;
  isBootstrapping: boolean;
  hasBootstrapped: boolean;
  setSession: (payload: { accessToken: string; user: AuthUserView }) => void;
  setAuthContext: (payload: AuthContextResponse | null) => void;
  clearSession: () => void;
  setBootstrapping: (value: boolean) => void;
  markBootstrapped: () => void;
};

const initialState = {
  accessToken: null,
  user: null,
  authContext: null,
  isBootstrapping: true,
  hasBootstrapped: false
};

export const useAuthStore = create<AuthState>((set) => ({
  ...initialState,
  setSession: ({ accessToken, user }) =>
    set({
      accessToken,
      user
    }),
  setAuthContext: (payload) =>
    set({
      authContext: payload
    }),
  clearSession: () =>
    set({
      accessToken: null,
      user: null,
      authContext: null
    }),
  setBootstrapping: (value) => set({ isBootstrapping: value }),
  markBootstrapped: () => set({ hasBootstrapped: true, isBootstrapping: false })
}));

export function buildFallbackAuthContext(user: AuthUserView): AuthContextResponse {
  const fallbackOrg = user.orgId
    ? {
        orgId: user.orgId,
        orgName: user.orgId
      }
    : null;
  return {
    user,
    activeOrg: fallbackOrg,
    availableOrgs: fallbackOrg ? [fallbackOrg] : [],
    scopeMode: 'ORG_SCOPED'
  };
}

export function isWriteRole(role: Role | null | undefined): boolean {
  return role === 'OWNER' || role === 'ADMIN' || role === 'MEMBER';
}

export function isAdminRole(role: Role | null | undefined): boolean {
  return role === 'OWNER' || role === 'ADMIN';
}
