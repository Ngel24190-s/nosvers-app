import { Bot } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { SparkAreaChart } from '@tremor/react';
import { WidgetCard } from './WidgetCard';
import { NeuralGraph, type ClaudeState } from './NeuralGraph';
import type { UseWebSocketReturn } from '../../hooks/useWebSocket';

interface ClaudePayload {
  state: ClaudeState;
  service_active: boolean;
  last_interaction_ts: number;
  tokens_today: number;
  tokens_history: number[];
}

function fmtRelTime(ts: number): string {
  if (!ts) return '—';
  const diff = Math.floor(Date.now() / 1000 - ts);
  if (diff < 60) return `${diff}s`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h`;
  return `${Math.floor(diff / 86400)}d`;
}

const stateLabel: Record<ClaudeState, string> = {
  online: 'ONLINE',
  listening: 'LISTENING',
  thinking: 'THINKING',
  speaking: 'SPEAKING',
  offline: 'OFFLINE',
};

const stateText: Record<ClaudeState, string> = {
  online: 'text-accent-green',
  listening: 'text-accent-green',
  thinking: 'text-accent-orange',
  speaking: 'text-accent-violet',
  offline: 'text-cockpit-textDim',
};

const TOKEN_ALERT_THRESHOLD = 200_000;

function normaliseState(raw: unknown): ClaudeState {
  const v = typeof raw === 'string' ? raw : '';
  if (v === 'online' || v === 'listening' || v === 'thinking' || v === 'speaking' || v === 'offline') {
    return v;
  }
  return 'offline';
}

export function ClaudeStatusWidget({ ws, index }: { ws: UseWebSocketReturn; index: number }) {
  const [data, setData] = useState<ClaudePayload | null>(null);

  useEffect(
    () =>
      ws.subscribe('claude', (p) => {
        const raw = p as Partial<ClaudePayload>;
        setData({
          state: normaliseState(raw.state),
          service_active: !!raw.service_active,
          last_interaction_ts: raw.last_interaction_ts ?? 0,
          tokens_today: raw.tokens_today ?? 0,
          tokens_history: Array.isArray(raw.tokens_history) ? raw.tokens_history : [],
        });
      }),
    [ws],
  );

  const state = data?.state ?? 'offline';
  const tokens = data?.tokens_today ?? 0;
  const history = data?.tokens_history ?? [];
  const chart = useMemo(
    () =>
      history.length
        ? history.map((v, i) => ({ x: i, y: v }))
        : Array.from({ length: 6 }, (_, i) => ({ x: i, y: 0 })),
    [history],
  );
  const alertExtra = tokens > TOKEN_ALERT_THRESHOLD;

  return (
    <WidgetCard title="Claude" icon={<Bot size={14} />} accent="green" index={index}>
      <div className="flex flex-col h-full gap-2">
        <div className="flex items-baseline justify-between">
          <div className={`cockpit-mono text-sm font-bold tracking-tight ${stateText[state]}`}>
            {stateLabel[state]}
          </div>
          <div className="cockpit-mono text-[10px] text-cockpit-textDim">
            últ. {fmtRelTime(data?.last_interaction_ts ?? 0)}
          </div>
        </div>

        <div className="flex-1 min-h-[110px] relative">
          <NeuralGraph state={state} alertExtraNode={alertExtra} />
        </div>

        <div>
          <div className="flex items-baseline justify-between mb-1">
            <span className="text-[10px] uppercase tracking-wider text-cockpit-textDim">
              tokens hoy
            </span>
            <span className="cockpit-mono text-base font-bold text-accent-green">
              {tokens.toLocaleString()}
            </span>
          </div>
          <div className="h-8">
            <SparkAreaChart
              data={chart}
              categories={['y']}
              index="x"
              colors={['emerald']}
              className="h-8 w-full"
            />
          </div>
        </div>
      </div>
    </WidgetCard>
  );
}
