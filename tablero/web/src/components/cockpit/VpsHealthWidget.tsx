import { Cpu } from 'lucide-react';
import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { SparkAreaChart } from '@tremor/react';
import { WidgetCard } from './WidgetCard';
import type { UseWebSocketReturn } from '../../hooks/useWebSocket';

interface HealthPayload {
  cpu_pct: number;
  ram_pct: number;
  ram_used_mb: number;
  ram_total_mb: number;
  disk_pct: number;
  disk_used_gb: number;
  disk_total_gb: number;
  load_1: number;
  load_5: number;
  load_15: number;
  net_in_kbps: number;
  net_out_kbps: number;
  uptime_s: number;
  cpu_history?: number[];
}

function uptimeShort(s: number): string {
  if (!s) return '—';
  const d = Math.floor(s / 86400);
  const h = Math.floor((s % 86400) / 3600);
  if (d > 0) return `${d}d ${h}h`;
  const m = Math.floor((s % 3600) / 60);
  return `${h}h ${m}m`;
}

function gaugeColor(pct: number): string {
  if (pct >= 90) return '#ef4444';
  if (pct >= 70) return '#fb923c';
  return '#34d399';
}

function Gauge({ label, pct, tooltip }: { label: string; pct: number; tooltip?: string }) {
  const radius = 22;
  const circ = 2 * Math.PI * radius;
  const dashOffset = circ * (1 - pct / 100);
  const color = gaugeColor(pct);
  return (
    <div className="flex flex-col items-center" title={tooltip ?? `${label}: ${pct.toFixed(1)}%`}>
      <div className="relative">
        <svg width="56" height="56" viewBox="0 0 56 56">
          <circle cx="28" cy="28" r={radius} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="4" />
          <motion.circle
            cx="28"
            cy="28"
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth="4"
            strokeLinecap="round"
            strokeDasharray={circ}
            initial={{ strokeDashoffset: circ }}
            animate={{ strokeDashoffset: dashOffset }}
            transition={{ duration: 0.6, ease: 'easeOut' }}
            transform="rotate(-90 28 28)"
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="cockpit-mono text-xs font-bold" style={{ color }}>
            {Math.round(pct)}
          </span>
        </div>
      </div>
      <span className="cockpit-mono text-[9px] uppercase tracking-wider text-cockpit-textDim mt-1">
        {label}
      </span>
    </div>
  );
}

export function VpsHealthWidget({ ws, index }: { ws: UseWebSocketReturn; index: number }) {
  const [data, setData] = useState<HealthPayload | null>(null);

  useEffect(() => ws.subscribe('health', (p) => setData(p as HealthPayload)), [ws]);

  const cpu = data?.cpu_pct ?? 0;
  const ram = data?.ram_pct ?? 0;
  const disk = data?.disk_pct ?? 0;
  const load = data?.load_1 ?? 0;
  const loadPct = Math.min(load * 25, 100); // ~load 4 = 100%
  const history = data?.cpu_history ?? [];
  const chart = history.length
    ? history.map((v, i) => ({ x: i, y: v }))
    : Array.from({ length: 6 }, (_, i) => ({ x: i, y: 0 }));

  return (
    <WidgetCard
      title="VPS Health"
      icon={<Cpu size={14} />}
      accent="cyan"
      index={index}
      headerExtra={
        <span className="cockpit-mono text-[10px] text-cockpit-textDim">
          up {uptimeShort(data?.uptime_s ?? 0)}
        </span>
      }
    >
      <div className="flex flex-col h-full justify-between">
        {data === null ? (
          <div className="flex-1 flex flex-col gap-2 p-2">
            <div className="grid grid-cols-4 gap-1">
              {[0, 1, 2, 3].map((i) => (
                <div key={i} className="h-14 w-14 rounded-full skeleton mx-auto" />
              ))}
            </div>
            <div className="h-8 skeleton rounded" />
          </div>
        ) : (
          <>
            <div className="grid grid-cols-4 gap-1">
              <Gauge label="CPU" pct={cpu} tooltip={`CPU ${cpu.toFixed(1)}% · load ${load.toFixed(2)}`} />
              <Gauge label="RAM" pct={ram} tooltip={`RAM ${ram.toFixed(1)}% · ${(data.ram_used_mb / 1024).toFixed(1)}/${(data.ram_total_mb / 1024).toFixed(1)} GB`} />
              <Gauge label="DISK" pct={disk} tooltip={`DISK ${disk.toFixed(1)}% · ${data.disk_used_gb.toFixed(0)}/${data.disk_total_gb.toFixed(0)} GB`} />
              <Gauge label="LOAD" pct={loadPct} tooltip={`load1 ${data.load_1.toFixed(2)} · load5 ${data.load_5.toFixed(2)} · load15 ${data.load_15.toFixed(2)}`} />
            </div>
            <div className="mt-2">
              <div className="flex justify-between mb-1 cockpit-mono text-[9px] text-cockpit-textDim">
                <span>CPU 60min</span>
                <span title={`net in ${data.net_in_kbps.toFixed(1)} kbps / out ${data.net_out_kbps.toFixed(1)} kbps`}>
                  ↓{(data.net_in_kbps ?? 0).toFixed(0)}k ↑{(data.net_out_kbps ?? 0).toFixed(0)}k
                </span>
              </div>
              <div className="h-8" title={history.length ? `últimos ${history.length} ticks · max ${Math.max(...history).toFixed(1)}% · min ${Math.min(...history).toFixed(1)}%` : 'sin historial aún'}>
                <SparkAreaChart
                  data={chart}
                  categories={['y']}
                  index="x"
                  colors={['cyan']}
                  className="h-8 w-full"
                />
              </div>
            </div>
          </>
        )}
      </div>
    </WidgetCard>
  );
}
