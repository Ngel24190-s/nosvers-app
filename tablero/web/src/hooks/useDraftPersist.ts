/**
 * useDraftPersist — persiste el borrador de captura en localStorage (FR-003).
 *
 * El borrador sobrevive cierre accidental del modal hasta que el usuario
 * guarde (lo borra) o lo descarte explícitamente.
 */
import { useCallback, useEffect, useState } from 'react';
import type { BorradorCaptura, Etiqueta } from '../lib/types';

const KEY = 'tablero.draft';

const EMPTY: BorradorCaptura = {
  titulo: '',
  cuerpo: '',
  etiquetas: [],
  savedAt: '',
};

function leerInicial(): BorradorCaptura {
  try {
    const raw = localStorage.getItem(KEY);
    if (raw) return JSON.parse(raw) as BorradorCaptura;
  } catch {
    // ignore
  }
  return EMPTY;
}

export function useDraftPersist() {
  const [draft, setDraft] = useState<BorradorCaptura>(leerInicial);

  useEffect(() => {
    if (!draft.titulo && !draft.cuerpo && draft.etiquetas.length === 0) {
      try {
        localStorage.removeItem(KEY);
      } catch {
        // ignore
      }
      return;
    }
    try {
      localStorage.setItem(KEY, JSON.stringify({ ...draft, savedAt: new Date().toISOString() }));
    } catch {
      // ignore
    }
  }, [draft]);

  const update = useCallback((partial: Partial<BorradorCaptura>) => {
    setDraft((d) => ({ ...d, ...partial }));
  }, []);

  const clear = useCallback(() => {
    setDraft(EMPTY);
    try {
      localStorage.removeItem(KEY);
    } catch {
      // ignore
    }
  }, []);

  const setEtiquetas = useCallback((etiquetas: Etiqueta[]) => {
    setDraft((d) => ({ ...d, etiquetas }));
  }, []);

  return { draft, update, clear, setEtiquetas };
}
