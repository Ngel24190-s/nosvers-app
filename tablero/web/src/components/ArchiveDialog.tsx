/**
 * ArchiveDialog — confirmación con razón opcional para archivar nota (US3).
 */
import { useState } from 'react';
import { archivarNota } from '../lib/api';

interface Props {
  open: boolean;
  notePath: string | null;
  concurrencyToken: string;
  onArchived: () => void;
  onCancel: () => void;
}

export function ArchiveDialog({ open, notePath, concurrencyToken, onArchived, onCancel }: Props) {
  const [reason, setReason] = useState('');
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!open || !notePath) return null;

  async function submit() {
    if (!notePath) return;
    setEnviando(true);
    setError(null);
    try {
      await archivarNota(notePath, concurrencyToken, reason.trim() || undefined);
      setReason('');
      onArchived();
    } catch (e) {
      setError(String(e));
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      onClick={onCancel}
      role="dialog"
      aria-modal="true"
    >
      <div
        className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="mb-2 text-lg font-semibold">Archivar nota</h2>
        <p className="mb-4 text-sm text-tinta/70">
          La nota se moverá a <code>dia/archivo/</code>. Podrás restaurarla desde la papelera.
        </p>
        <label className="mb-3 block">
          <span className="mb-1 block text-xs text-tinta/60">Razón (opcional)</span>
          <textarea
            rows={2}
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="duplicado de…, error de transcripción, etc."
            className="w-full rounded border border-tinta/20 bg-cream px-2 py-1 text-sm"
            disabled={enviando}
          />
        </label>
        {error && <div className="mb-3 text-sm text-red-700">{error}</div>}
        <div className="flex justify-end gap-2">
          <button
            type="button"
            onClick={onCancel}
            disabled={enviando}
            className="rounded border border-tinta/20 px-4 py-2 text-sm hover:bg-tinta/5"
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={submit}
            disabled={enviando}
            className="rounded bg-amber-600 px-4 py-2 text-sm font-medium text-white hover:bg-amber-700 disabled:opacity-50"
          >
            {enviando ? 'Archivando…' : 'Archivar'}
          </button>
        </div>
      </div>
    </div>
  );
}
