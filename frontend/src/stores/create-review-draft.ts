'use client';

import { create } from 'zustand';

type CreateReviewDraftState = {
  requirementText: string;
  backgroundText: string;
  businessDomain: string;
  moduleHint: string;
  setDraft: (payload: Partial<Omit<CreateReviewDraftState, 'setDraft' | 'reset'>>) => void;
  reset: () => void;
};

const defaultState = {
  requirementText: '',
  backgroundText: '',
  businessDomain: '',
  moduleHint: ''
};

export const useCreateReviewDraftStore = create<CreateReviewDraftState>((set) => ({
  ...defaultState,
  setDraft: (payload) => set((state) => ({ ...state, ...payload })),
  reset: () => set(defaultState)
}));
