import { useEffect, useState } from 'react';
import type { Identity } from './types';

const TOKEN_KEY = 'tablero_token';

export function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setToken(jwt: string): void {
  try {
    localStorage.setItem(TOKEN_KEY, jwt.trim());
  } catch {
    /* localStorage disabled / private mode — ignore */
  }
}

export function clearToken(): void {
  try {
    localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* ignore */
  }
}

export function isExpired(exp: number): boolean {
  // 60-second early-warning so we redirect to login before the next request 401s.
  return Date.now() / 1000 >= exp - 60;
}

export function useIdentity(): { identity: Identity | null; loading: boolean; error: string | null } {
  const [identity, setIdentity] = useState<Identity | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function run() {
      const t = getToken();
      if (!t) {
        if (!cancelled) {
          setIdentity(null);
          setLoading(false);
        }
        return;
      }
      try {
        const mod = await import('./api');
        const r = await mod.getWhoami();
        if (!cancelled) {
          setIdentity(r.identidad);
          setLoading(false);
        }
      } catch (e) {
        if (!cancelled) {
          setIdentity(null);
          setError(String(e));
          setLoading(false);
        }
      }
    }
    void run();
    return () => {
      cancelled = true;
    };
  }, []);

  return { identity, loading, error };
}
