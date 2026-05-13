import { Terminal } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { WidgetCard } from './WidgetCard';
import type { UseWebSocketReturn } from '../../hooks/useWebSocket';

interface ActivityLine {
  ts: number;
  unit: string;
  level: string;
  msg: string;
}

function fmtTime(ts: number): string {
  if (!ts) return '         ';
  const d = new Date(ts * 1000);
  return d.toTimeString().slice(0, 8);
}

export function ActivityStreamWidget({ ws, index }: { ws: UseWebSocketReturn; index: number }) {
  const [lines, setLines] = useState<ActivityLine[]>([]);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  useEffect(
    () =>
      ws.subscribe('activity', (p) => {
        const payload = p as { lines: ActivityLine[] };
        setLines(payload.lines ?? []);
      }),
    [ws],
  );

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [lines]);

  return (
    <WidgetCard
      title="Activity Stream"
      icon={<Terminal size={14} />}
      accent="cyan"
      index={index}
      headerExtra={
        <span className="cockpit-mono text-[10px] text-cockpit-textDim">{lines.length} líneas</span>
      }
    >
      <div ref={scrollRef} className="cockpit-scrollbar h-full overflow-y-auto pr-1">
        {lines.length === 0 && (
          <div className="cockpit-mono text-[11px] text-cockpit-textDim italic">
            esperando eventos del journald…
          </div>
        )}
        {lines.map((l, i) => (
          <div key={`${l.ts}-${i}`} className="cockpit-activity-line" data-level={l.level}>
            <span className="text-cockpit-dim">{fmtTime(l.ts)}</span>{' '}
            <span className="text-accent-violet">{l.unit}</span>{' '}
            <span className="opacity-70">[{l.level}]</span> {l.msg}
          </div>
        ))}
      </div>
    </WidgetCard>
  );
}
