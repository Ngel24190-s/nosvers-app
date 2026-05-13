/**
 * CaptureModal — modal de captura de nota (US1).
 *
 * Atajo global Ctrl+N abre el modal. Borrador persistido en localStorage.
 * Autor inferido del JWT por el backend.
 */
import { useEffect, useId, useRef, useState } from 'react';
import { ApiError, capturarNota } from '../lib/api';
import { type Etiqueta, ETIQUETAS } from '../lib/types';
import { useDraftPersist } from '../hooks/useDraftPersist';
import { TagChip } from './TagChip';

interface Props {
  open: boolean;
  onClose: () => void;
  onCaptured?: (path: string) => void;
}

export function CaptureModal({ open, onClose, onCaptured }: Props) {
  const { draft, update, clear, setEtiquetas } = useDraftPersist();
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const tituloId = useId();
  const cuerpoId = useId();

  // Focus al cuerpo al abrir
  useEffect(() => {
    if (open) {
      setError(null);
      // Pequeño delay para asegurar que el modal está montado
      setTimeout(() => textareaRef.current?.focus(), 30);
    }
  }, [open]);

  // Esc cierra
  useEffect(() => {
    if (!open) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape' && !enviando) {
        e.preventDefault();
        onClose();
      }
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, enviando, onClose]);

  if (!open) return null;

  function toggleEtiqueta(et: Etiqueta) {
    if (draft.etiquetas.includes(et)) {
      setEtiquetas(draft.etiquetas.filter((e) => e !== et));
    } else {
      setEtiquetas([...draft.etiquetas, et]);
    }
  }

  async function submit() {
    if (!draft.cuerpo.trim()) {
      setError('El cuerpo no puede estar vacío.');
      return;
    }
    setEnviando(true);
    setError(null);
    try {
      const res = await capturarNota({
        titulo: draft.titulo.trim() || undefined,
        cuerpo: draft.cuerpo.trim(),
        etiquetas: draft.etiquetas,
      });
      clear();
      onCaptured?.(res.path);
      onClose();
    } catch (e) {
      if (e instanceof ApiError) {
        setError(e.detalle ?? e.code);
      } else {
        setError(String(e));
      }
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center bg-black/40 p-4 sm:items-center"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="capture-modal-title"
    >
      <div
        className="w-full max-w-2xl rounded-lg bg-white p-6 shadow-xl dark:bg-zinc-900"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 id="capture-modal-title" className="mb-4 text-lg font-semibold">
          Nueva nota
        </h2>

        <div className="mb-3">
          <label htmlFor={tituloId} className="mb-1 block text-sm text-zinc-600 dark:text-zinc-400">
            Título (opcional)
          </label>
          <input
            id={tituloId}
            type="text"
            value={draft.titulo}
            onChange={(e) => update({ titulo: e.target.value })}
            placeholder="Idea sobre…"
            disabled={enviando}
            className="w-full rounded border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-800"
          />
        </div>

        <div className="mb-3">
          <label htmlFor={cuerpoId} className="mb-1 block text-sm text-zinc-600 dark:text-zinc-400">
            Cuerpo (markdown)
          </label>
          <textarea
            id={cuerpoId}
            ref={textareaRef}
            value={draft.cuerpo}
            onChange={(e) => update({ cuerpo: e.target.value })}
            rows={8}
            placeholder="Lo que tengas en la cabeza. Soporta wiki-links [[nota]]."
            disabled={enviando}
            className="w-full rounded border border-zinc-300 bg-white px-3 py-2 font-mono text-sm dark:border-zinc-700 dark:bg-zinc-800"
          />
        </div>

        <div className="mb-4">
          <span className="mb-2 block text-sm text-zinc-600 dark:text-zinc-400">Etiquetas</span>
          <div className="flex flex-wrap gap-2">
            {ETIQUETAS.map((et) => (
              <button
                key={et}
                type="button"
                onClick={() => toggleEtiqueta(et)}
                disabled={enviando}
                className={`rounded-full px-3 py-1 text-xs transition ${
                  draft.etiquetas.includes(et)
                    ? 'bg-emerald-600 text-white'
                    : 'bg-zinc-200 text-zinc-700 hover:bg-zinc-300 dark:bg-zinc-700 dark:text-zinc-300'
                }`}
                aria-pressed={draft.etiquetas.includes(et)}
              >
                {et}
              </button>
            ))}
          </div>
        </div>

        {error && (
          <div className="mb-3 rounded border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-700 dark:bg-red-950/30 dark:text-red-300">
            {error}
          </div>
        )}

        <div className="flex justify-end gap-2">
          <button
            type="button"
            onClick={onClose}
            disabled={enviando}
            className="rounded border border-zinc-300 px-4 py-2 text-sm hover:bg-zinc-100 dark:border-zinc-700 dark:hover:bg-zinc-800"
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={submit}
            disabled={enviando || !draft.cuerpo.trim()}
            className="rounded bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {enviando ? 'Guardando…' : 'Guardar (Ctrl+Enter)'}
          </button>
        </div>

        <p className="mt-3 text-xs text-zinc-500 dark:text-zinc-500">
          Esc cierra · El borrador se guarda automáticamente
        </p>
      </div>
    </div>
  );
}
