/**
 * useVistaPersist — persiste la vista activa del timeline en localStorage (FR-012).
 */
import { useEffect, useState } from 'react';
import { type Vista, VISTAS } from '../lib/types';

const KEY = 'tablero.vista';
const DEFAULT: Vista = 'lista';

function leerVistaInicial(): Vista {
  try {
    const raw = localStorage.getItem(KEY);
    if (raw && (VISTAS as readonly string[]).includes(raw)) {
      return raw as Vista;
    }
  } catch {
    // localStorage no disponible (SSR o privacidad)
  }
  return DEFAULT;
}

export function useVistaPersist(): [Vista, (v: Vista) => void] {
  const [vista, setVistaState] = useState<Vista>(leerVistaInicial);

  useEffect(() => {
    try {
      localStorage.setItem(KEY, vista);
    } catch {
      // ignore
    }
  }, [vista]);

  return [vista, setVistaState];
}
