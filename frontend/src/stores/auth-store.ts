'use client';

import { create } from 'zustand';

import { AuthUserView, Role } from '@/types';

type AuthState = {
  accessToken: string | null;
  user: AuthUserView | null;
  isBootstrapping: boolean;
  hasBootstrapped: boolean;
  setSession: (payload: { accessToken: string; user: AuthUserView }) => void;
  clearSession: () => void;
  setBootstrapping: (value: boolean) => void;
  markBootstrapped: () => void;
};

const initialState = {
  accessToken: null,
  user: null,
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
  clearSession: () =>
    set({
      accessToken: null,
      user: null
    }),
  setBootstrapping: (value) => set({ isBootstrapping: value }),
  markBootstrapped: () => set({ hasBootstrapped: true, isBootstrapping: false })
}));

export function isWriteRole(role: Role | null | undefined): boolean {
  return role === 'OWNER' || role === 'ADMIN' || role === 'MEMBER';
}

