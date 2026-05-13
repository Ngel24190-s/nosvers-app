/**
 * NoteEditor — editor split-pane markdown+preview (US2).
 *
 * Mitad izquierda: textarea con el cuerpo markdown.
 * Mitad derecha: render del mismo cuerpo con MarkdownBody (mismo renderer de Fase A).
 * Debounce 250ms entre cambios → preview se actualiza.
 *
 * Concurrencia optimista: usa `concurrency_token` que viene del backend
 * (modified_at si existe, sino ts inmutable). Tras 409, muestra resolución.
 */
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { ConcurrencyError, editarNota } from '../lib/api';
import { MarkdownBody } from '../lib/markdown';
import type { NoteFull } from '../lib/types';

interface Props {
  nota: NoteFull;
  /** El concurrency_token actual de la nota (modified_at o ts). */
  concurrencyToken: string;
  onSaved: (newToken: string) => void;
  onCancel: () => void;
}

function useDebounce<T>(value: T, ms: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), ms);
    return () => clearTimeout(t);
  }, [value, ms]);
  return debounced;
}

export function NoteEditor({ nota, concurrencyToken, onSaved, onCancel }: Props) {
  const [cuerpo, setCuerpo] = useState(nota.body_markdown);
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [conflicto, setConflicto] = useState<string | null>(null); // current_modified_at del conflicto
  const cuerpoInicial = useRef(nota.body_markdown);

  const hayCambios = cuerpo !== cuerpoInicial.current;
  const previewBody = useDebounce(cuerpo, 250);

  const cancelar = useCallback(() => {
    if (hayCambios) {
      const ok = window.confirm('¿Descartar cambios?');
      if (!ok) return;
    }
    onCancel();
  }, [hayCambios, onCancel]);

  // Esc cierra (con confirmación si hay cambios)
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape' && !enviando) {
        e.preventDefault();
        cancelar();
      }
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [enviando, cancelar]);

  async function guardar() {
    if (!hayCambios || enviando) return;
    setEnviando(true);
    setError(null);
    setConflicto(null);
    try {
      const res = await editarNota(
        { path: nota.path, cuerpo },
        concurrencyToken,
      );
      cuerpoInicial.current = cuerpo;
      onSaved(res.concurrency_token);
    } catch (e) {
      if (e instanceof ConcurrencyError) {
        setConflicto(e.currentModifiedAt);
      } else {
        setError(String(e));
      }
    } finally {
      setEnviando(false);
    }
  }

  // Helpers
  const titulo = useMemo(() => {
    const fm = nota.frontmatter;
    if (fm.autor && fm.ts) return `${fm.autor} · ${fm.ts.slice(0, 16)}`;
    return nota.path;
  }, [nota]);

  return (
    <div className="flex h-full flex-col">
      <header className="border-b border-tinta/10 bg-cream/95 px-4 py-2 backdrop-blur">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-medium text-tinta">{titulo}</h3>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={cancelar}
              disabled={enviando}
              className="rounded border border-tinta/20 px-3 py-1 text-sm text-tinta hover:bg-tinta/5"
            >
              Cancelar
            </button>
            <button
              type="button"
              onClick={guardar}
              disabled={!hayCambios || enviando}
              className="rounded bg-emerald-600 px-3 py-1 text-sm font-medium text-white hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {enviando ? 'Guardando…' : 'Guardar'}
            </button>
          </div>
        </div>
      </header>

      {conflicto && (
        <div className="border-b border-amber-300 bg-amber-50 px-4 py-2 text-sm text-amber-900 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-200">
          <strong>Conflicto:</strong> esta nota fue editada por otro autor.
          Versión actual en disco: <code>{conflicto}</code>.
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="ml-2 underline"
          >
            Recargar y volver a aplicar
          </button>
        </div>
      )}

      {error && (
        <div className="border-b border-red-300 bg-red-50 px-4 py-2 text-sm text-red-700 dark:border-red-700 dark:bg-red-950/30 dark:text-red-300">
          {error}
        </div>
      )}

      <div className="grid flex-1 grid-cols-1 overflow-hidden md:grid-cols-2">
        <textarea
          value={cuerpo}
          onChange={(e) => setCuerpo(e.target.value)}
          disabled={enviando}
          className="resize-none border-r border-tinta/10 bg-white p-4 font-mono text-sm focus:outline-none dark:bg-zinc-900"
          spellCheck={false}
          placeholder="Markdown…"
        />
        <div className="overflow-y-auto bg-cream/40 p-4">
          <MarkdownBody body={previewBody} attachments={nota.attachments} />
        </div>
      </div>
    </div>
  );
}
