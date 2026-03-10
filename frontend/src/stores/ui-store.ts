'use client';

import { create } from 'zustand';

type UiState = {
  isEvidenceDrawerOpen: boolean;
  isRegenerateDialogOpen: boolean;
  openEvidenceDrawer: () => void;
  closeEvidenceDrawer: () => void;
  openRegenerateDialog: () => void;
  closeRegenerateDialog: () => void;
};

export const useUiStore = create<UiState>((set) => ({
  isEvidenceDrawerOpen: false,
  isRegenerateDialogOpen: false,
  openEvidenceDrawer: () => set({ isEvidenceDrawerOpen: true }),
  closeEvidenceDrawer: () => set({ isEvidenceDrawerOpen: false }),
  openRegenerateDialog: () => set({ isRegenerateDialogOpen: true }),
  closeRegenerateDialog: () => set({ isRegenerateDialogOpen: false })
}));
