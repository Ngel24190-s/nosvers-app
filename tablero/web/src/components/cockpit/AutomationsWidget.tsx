import { Zap, ExternalLink } from 'lucide-react';
import { WidgetCard } from './WidgetCard';
import { useAutomationStream } from '../../hooks/useAutomationStream';
import type { UseWebSocketReturn } from '../../hooks/useWebSocket';

interface Props {
  ws: UseWebSocketReturn;
  index?: number;
  onOpenEditor?: () => void;
}

const STATUS_DOT: Record<string, string> = {
  ok: 'bg-accent-green',
  partial: 'bg-accent-orange',
  error: 'bg-accent-orange',
  interrupted: 'bg-cockpit-textDim',
};

export function AutomationsWidget({ ws, index = 12, onOpenEditor }: Props) {
  const { recent, hasSnapshot } = useAutomationStream(ws);
  const ordered = [...recent].reverse();

  const openEditor = () => {
    if (onOpenEditor) {
      onOpenEditor();
    } else if (typeof window !== 'undefined') {
      window.location.hash = '#cockpit/automatizaciones';
    }
  };

  return (
    <WidgetCard
      title="AUTOMATIZACIONES"
      icon={<Zap size={14} />}
      accent="violet"
      index={index}
      headerExtra={
        <button
          onClick={openEditor}
          className="cockpit-mono text-[10px] text-cockpit-textDim hover:text-accent-green flex items-center gap-1"
          aria-label="abrir editor"
        >
          <ExternalLink size={11} /> EDITOR
        </button>
      }
    >
      <div className="flex-1 px-3 pb-3 overflow-y-auto">
        {!hasSnapshot && (
          <>
            {[0, 1, 2].map((i) => (
              <div key={i} className="my-1.5 h-7 rounded skeleton" />
            ))}
          </>
        )}
        {hasSnapshot && ordered.length === 0 && (
          <div className="cockpit-mono text-[10px] text-cockpit-dim py-3 text-center">
            sin ejecuciones aún
          </div>
        )}
        {ordered.map((r) => (
          <div
            key={r.execution_id}
            className="flex items-center gap-2 py-1 border-b border-cockpit-border/30 last:border-b-0"
            title={`${r.automation_id}`}
          >
            <span
              className={`shrink-0 w-2 h-2 rounded-full ${
                r.in_progress
                  ? 'bg-accent-amber animate-pulse'
                  : STATUS_DOT[r.status] || 'bg-cockpit-textDim'
              }`}
            />
            <span className="cockpit-mono text-[10px] text-cockpit-textDim shrink-0">
              {r.ts.slice(11, 19)}
            </span>
            <span className="text-[11px] text-cockpit-text truncate flex-1">{r.automation_nombre}</span>
            <span className="cockpit-mono text-[9px] text-cockpit-dim shrink-0">{r.duration_ms}ms</span>
          </div>
        ))}
      </div>
    </WidgetCard>
  );
}
