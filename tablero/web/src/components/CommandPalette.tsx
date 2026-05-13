/**
 * CommandPalette — `Ctrl+K` paleta estilo Notion (US5).
 *
 * Tres secciones: Notas, Acciones, Vistas. Fetcha resultados de `dia_buscar`
 * con debounce 200ms. Navegable solo con teclado.
 */
import { Command } from 'cmdk';
import { Search, Plus, List, Table, Trello, Calendar, Image, Loader2 } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { ApiError, getBuscar } from '../lib/api';
import type { SearchHit, Vista } from '../lib/types';

interface Props {
  open: boolean;
  onClose: () => void;
  onSelectHit: (h: SearchHit) => void;
  onAction: (action: 'capturar' | `vista:${Vista}`) => void;
}

const VISTAS_ICONS: Record<Vista, typeof List> = {
  lista: List,
  tabla: Table,
  kanban: Trello,
  calendario: Calendar,
  galeria: Image,
};

export function CommandPalette({ open, onClose, onSelectHit, onAction }: Props) {
  const [query, setQuery] = useState('');
  const [hits, setHits] = useState<SearchHit[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Reset al abrir
  useEffect(() => {
    if (open) {
      setQuery('');
      setHits([]);
      setError(null);
    }
  }, [open]);

  // Debounced search
  useEffect(() => {
    if (!open) return;
    const q = query.trim();
    if (q.length < 2) {
      setHits([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    const handle = setTimeout(async () => {
      try {
        const res = await getBuscar({ q, limite: 5 });
        setHits(res.resultados);
        setError(null);
      } catch (e) {
        if (e instanceof ApiError) {
          setError(e.detalle ?? e.code);
        } else {
          setError(String(e));
        }
        setHits([]);
      } finally {
        setLoading(false);
      }
    }, 200);
    return () => clearTimeout(handle);
  }, [query, open]);

  // Esc cierra
  useEffect(() => {
    if (!open) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') {
        e.preventDefault();
        onClose();
      }
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  const sinResultados = useMemo(() => {
    return query.trim().length >= 2 && !loading && hits.length === 0;
  }, [query, loading, hits.length]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center bg-black/30 p-4 pt-[15vh]"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label="Paleta de comandos"
    >
      <Command
        className="w-full max-w-xl overflow-hidden rounded-lg border border-tinta/20 bg-white shadow-2xl"
        onClick={(e) => e.stopPropagation()}
        label="Paleta de comandos"
      >
        <div className="flex items-center gap-2 border-b border-tinta/10 px-3 py-2">
          {loading ? <Loader2 size={16} className="animate-spin text-tinta/50" /> : <Search size={16} className="text-tinta/50" />}
          <Command.Input
            placeholder="Buscar notas, ejecutar acciones…"
            value={query}
            onValueChange={setQuery}
            autoFocus
            className="flex-1 bg-transparent text-sm text-tinta placeholder:text-tinta/40 focus:outline-none"
          />
          <kbd className="rounded border border-tinta/15 px-1.5 py-0.5 text-[10px] text-tinta/50">ESC</kbd>
        </div>

        <Command.List className="max-h-[60vh] overflow-y-auto p-2">
          {error && (
            <div className="px-3 py-2 text-sm text-red-700">Error: {error}</div>
          )}

          {sinResultados && (
            <Command.Empty className="px-3 py-6 text-center text-sm text-tinta/60">
              Sin resultados —{' '}
              <button
                type="button"
                onClick={() => {
                  onAction('capturar');
                  onClose();
                }}
                className="text-emerald-600 underline hover:text-emerald-700"
              >
                capturar nueva nota
              </button>
            </Command.Empty>
          )}

          {hits.length > 0 && (
            <Command.Group heading="Notas" className="text-xs uppercase text-tinta/50">
              {hits.map((h) => (
                <Command.Item
                  key={`${h.fecha}-${h.ts}`}
                  value={`nota-${h.fecha}-${h.ts}`}
                  onSelect={() => {
                    onSelectHit(h);
                    onClose();
                  }}
                  className="flex cursor-pointer items-start gap-3 rounded px-3 py-2 text-sm text-tinta data-[selected=true]:bg-emerald-100 data-[selected=true]:text-emerald-900"
                >
                  <Search size={14} className="mt-0.5 shrink-0 text-tinta/40" />
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2 text-xs text-tinta/60">
                      <span>{h.autor}</span>
                      <span>·</span>
                      <span>{h.fecha}</span>
                      <span>·</span>
                      <span>{h.etiqueta}</span>
                    </div>
                    <p className="truncate">{h.fragmento}</p>
                  </div>
                </Command.Item>
              ))}
            </Command.Group>
          )}

          <Command.Group heading="Acciones" className="text-xs uppercase text-tinta/50">
            <Command.Item
              value="action-capturar"
              onSelect={() => {
                onAction('capturar');
                onClose();
              }}
              className="flex cursor-pointer items-center gap-3 rounded px-3 py-2 text-sm text-tinta data-[selected=true]:bg-emerald-100 data-[selected=true]:text-emerald-900"
            >
              <Plus size={14} className="text-emerald-600" />
              <span>Capturar nueva nota</span>
              <kbd className="ml-auto rounded border border-tinta/15 px-1.5 py-0.5 text-[10px] text-tinta/50">Ctrl+N</kbd>
            </Command.Item>
          </Command.Group>

          <Command.Group heading="Cambiar vista" className="text-xs uppercase text-tinta/50">
            {(['lista', 'tabla', 'kanban', 'calendario', 'galeria'] as Vista[]).map((v) => {
              const Icon = VISTAS_ICONS[v];
              return (
                <Command.Item
                  key={v}
                  value={`vista-${v}`}
                  onSelect={() => {
                    onAction(`vista:${v}`);
                    onClose();
                  }}
                  className="flex cursor-pointer items-center gap-3 rounded px-3 py-2 text-sm text-tinta data-[selected=true]:bg-emerald-100 data-[selected=true]:text-emerald-900"
                >
                  <Icon size={14} className="text-tinta/50" />
                  <span className="capitalize">Vista {v}</span>
                </Command.Item>
              );
            })}
          </Command.Group>
        </Command.List>
      </Command>
    </div>
  );
}
