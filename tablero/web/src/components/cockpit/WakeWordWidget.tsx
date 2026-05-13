import { Mic, MicOff } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { WidgetCard } from './WidgetCard';
import type { UseWebSocketReturn } from '../../hooks/useWebSocket';

interface WakePayload {
  state: 'idle' | 'listening' | 'processing';
  last_wake_ts: number;
  voice_service_active: boolean;
}

const stateLabel: Record<WakePayload['state'], string> = {
  idle: 'ESPERANDO WAKE',
  listening: 'ESCUCHANDO',
  processing: 'PROCESANDO',
};

const stateColor: Record<WakePayload['state'], string> = {
  idle: 'text-cockpit-textDim',
  listening: 'text-accent-amber',
  processing: 'text-accent-violet',
};

function Waveform({ active }: { active: boolean }) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const dpr = window.devicePixelRatio || 1;
    const W = canvas.clientWidth * dpr;
    const H = canvas.clientHeight * dpr;
    canvas.width = W;
    canvas.height = H;
    let raf = 0;
    let t0 = performance.now();
    const draw = (now: number) => {
      const dt = (now - t0) / 1000;
      ctx.clearRect(0, 0, W, H);
      const bars = 32;
      const bw = W / bars;
      for (let i = 0; i < bars; i++) {
        const phase = i * 0.4 + dt * 4;
        const amp = active ? (Math.sin(phase) * 0.5 + 0.5) : 0.05 + Math.random() * 0.02;
        const h = amp * H * 0.9;
        const y = (H - h) / 2;
        ctx.fillStyle = active ? '#fbbf24' : '#3f3f46';
        ctx.fillRect(i * bw + 1 * dpr, y, bw - 2 * dpr, h);
      }
      raf = requestAnimationFrame(draw);
    };
    raf = requestAnimationFrame(draw);
    return () => cancelAnimationFrame(raf);
  }, [active]);
  return <canvas ref={canvasRef} className="w-full h-12" />;
}

function fmtRel(ts: number): string {
  if (!ts) return 'nunca';
  const d = Date.now() / 1000 - ts;
  if (d < 60) return `${Math.floor(d)}s`;
  if (d < 3600) return `${Math.floor(d / 60)}m`;
  if (d < 86400) return `${Math.floor(d / 3600)}h`;
  return `${Math.floor(d / 86400)}d`;
}

export function WakeWordWidget({ ws, index }: { ws: UseWebSocketReturn; index: number }) {
  const [data, setData] = useState<WakePayload | null>(null);

  useEffect(() => ws.subscribe('wake', (p) => setData(p as WakePayload)), [ws]);

  const state = data?.state ?? 'idle';
  const active = data?.voice_service_active ?? false;

  return (
    <WidgetCard
      title="Wake Word"
      icon={active ? <Mic size={14} /> : <MicOff size={14} />}
      accent={active ? 'amber' : 'violet'}
      index={index}
    >
      <div className="flex flex-col h-full justify-between">
        <div>
          <div className={`cockpit-mono text-base font-bold ${stateColor[state]}`}>
            {active ? stateLabel[state] : 'OFFLINE'}
          </div>
          <div className="cockpit-mono text-[10px] text-cockpit-textDim mt-1">
            últ. wake hace {fmtRel(data?.last_wake_ts ?? 0)}
          </div>
        </div>
        <Waveform active={state !== 'idle' && active} />
        <div className="cockpit-mono text-[9px] uppercase tracking-wider text-cockpit-textDim">
          nosvers-voice · {active ? 'active' : 'down'}
        </div>
      </div>
    </WidgetCard>
  );
}
