// Context state — qué contexto activo, persistencia + sincronización
// con `data-context` en <html>.

import {
  createContext,
  useContext as useReactContext,
  useEffect,
  useState,
} from 'react';
import type { Context } from './auth';
import { getAvailableContexts } from './auth';

const CTX_KEY = 'claudio.context';

interface ClaudioContextState {
  current: Context | null;
  available: Context[];
  setContext: (c: Context | null) => void;
}

export const ClaudioContextContext = createContext<ClaudioContextState>({
  current: null,
  available: ['casa', 'nosvers'],
  setContext: () => {},
});

export function useClaudioContext(): ClaudioContextState {
  return useReactContext(ClaudioContextContext);
}

export function useContextState(): ClaudioContextState {
  const [current, setCurrentRaw] = useState<Context | null>(() => {
    try {
      const v = localStorage.getItem(CTX_KEY) as Context | null;
      return v && ['casa', 'nosvers', 'trabajo'].includes(v) ? v : null;
    } catch {
      return null;
    }
  });
  const available = getAvailableContexts();

  const setContext = (c: Context | null) => {
    setCurrentRaw(c);
    try {
      if (c) localStorage.setItem(CTX_KEY, c);
      else localStorage.removeItem(CTX_KEY);
    } catch {
      /* ignore */
    }
  };

  useEffect(() => {
    const root = document.documentElement;
    if (current) {
      root.dataset.context = current;
    } else {
      // Sin contexto activo (Home): default visual Casa.
      root.dataset.context = 'casa';
    }
  }, [current]);

  // Si el contexto persistido no está disponible para este usuario,
  // limpiar.
  useEffect(() => {
    if (current && !available.includes(current)) {
      setContext(null);
    }
  }, [current, available]);

  return { current, available, setContext };
}
