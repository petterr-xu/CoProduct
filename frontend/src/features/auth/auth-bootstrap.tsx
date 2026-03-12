'use client';

import { useEffect, useRef } from 'react';

import { authClient } from '@/lib/auth-client';
import { useAuthStore } from '@/stores/auth-store';

export function AuthBootstrap() {
  const bootstrappedRef = useRef(false);

  useEffect(() => {
    if (bootstrappedRef.current) return;
    bootstrappedRef.current = true;

    let cancelled = false;
    const store = useAuthStore.getState();

    const bootstrap = async () => {
      store.setBootstrapping(true);
      try {
        const current = useAuthStore.getState();
        if (current.accessToken) {
          const user = await authClient.getMe(current.accessToken);
          if (cancelled) return;
          store.setSession({ accessToken: current.accessToken, user });
          return;
        }

        const refreshed = await authClient.refresh();
        const user = await authClient.getMe(refreshed.accessToken);
        if (cancelled) return;
        store.setSession({ accessToken: refreshed.accessToken, user });
      } catch {
        if (!cancelled) {
          store.clearSession();
        }
      } finally {
        if (!cancelled) {
          store.markBootstrapped();
        }
      }
    };

    void bootstrap();

    return () => {
      cancelled = true;
    };
  }, []);

  return null;
}

