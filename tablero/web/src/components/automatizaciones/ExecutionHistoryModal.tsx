import { useEffect, useState } from 'react';
import { X } from 'lucide-react';
import { apiAutomations, type ExecutionLog } from './lib/apiAutomations';

interface Props {
  automationId: string;
  onClose: () => void;
}

const STATUS_COLORS: Record<string, string> = {
  ok: 'text-accent-green',
  partial: 'text-accent-orange',
  error: 'text-accent-orange',
  interrupted: 'text-cockpit-textDim',
};

export function ExecutionHistoryModal({ automationId, onClose }: Props) {
  const today = new Date().toISOString().slice(0, 10);
  const [date, setDate] = useState(today);
  const [items, setItems] = useState<ExecutionLog[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    apiAutomations
      .logs(automationId, date)
      .then((r) => setItems(r.items))
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, [automationId, date]);

  return (
    <div className="fixed inset-0 z-[60] bg-black/60 flex items-center justify-center p-4">
      <div className="bg-cockpit-panel border border-cockpit-border rounded-lg max-w-3xl w-full max-h-[90vh] flex flex-col">
        <header className="flex items-center justify-between px-4 py-2 border-b border-cockpit-border">
          <div className="cockpit-mono text-xs text-cockpit-text">HISTORIAL — {automationId}</div>
          <div className="flex items-center gap-2">
            <input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              className="bg-cockpit-bg border border-cockpit-border rounded px-2 py-1 text-xs text-cockpit-text"
            />
            <button onClick={onClose} className="text-cockpit-textDim hover:text-accent-orange p-1">
              <X size={16} />
            </button>
          </div>
        </header>
        <div className="p-4 overflow-y-auto">
          {loading && <div className="text-[11px] cockpit-mono text-cockpit-textDim">cargando...</div>}
          {!loading && items.length === 0 && (
            <div className="text-[11px] cockpit-mono text-cockpit-textDim">Sin ejecuciones para esta fecha.</div>
          )}
          <ul className="space-y-2">
            {items.map((it) => (
              <li key={it.execution_id} className="px-3 py-2 border border-cockpit-border rounded bg-cockpit-bg/40">
                <div className="flex items-center justify-between">
                  <div className="cockpit-mono text-[11px] text-cockpit-text">
                    {it.started_at.slice(11, 19)} · {it.trigger.tipo} · {it.steps.length} pasos · {it.duration_ms}ms
                  </div>
                  <div className={`cockpit-mono text-[11px] ${STATUS_COLORS[it.status] || ''}`}>{it.status}</div>
                </div>
                <details className="mt-1">
                  <summary className="text-[10px] text-cockpit-textDim cursor-pointer">detalles</summary>
                  <pre className="text-[10px] text-cockpit-textDim mt-1 whitespace-pre-wrap overflow-x-auto">
                    {JSON.stringify(it, null, 2)}
                  </pre>
                </details>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
