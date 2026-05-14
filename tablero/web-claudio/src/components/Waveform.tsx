import { useEffect, useRef } from 'react';
import { snapshotAmplitudes } from '../lib/audio';

interface Props {
  analyser: AnalyserNode | null;
  color: string;
}

export default function Waveform({ analyser, color }: Props) {
  const ref = useRef<HTMLCanvasElement>(null);
  const raf = useRef<number>();

  useEffect(() => {
    if (!analyser) return;
    const canvas = ref.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    const draw = () => {
      const w = canvas.width;
      const h = canvas.height;
      ctx.clearRect(0, 0, w, h);
      const bars = reduced ? 1 : 28;
      const amps = snapshotAmplitudes(analyser, bars);
      const gap = 4;
      const barW = (w - gap * (bars - 1)) / bars;
      ctx.fillStyle = color;
      for (let i = 0; i < bars; i++) {
        const a = Math.max(0.05, amps[i]);
        const bh = h * a;
        const x = i * (barW + gap);
        const y = (h - bh) / 2;
        ctx.fillRect(x, y, barW, bh);
      }
      if (!reduced) raf.current = requestAnimationFrame(draw);
    };
    draw();
    return () => {
      if (raf.current) cancelAnimationFrame(raf.current);
    };
  }, [analyser, color]);

  return <canvas ref={ref} width={320} height={64} className="w-full h-16" />;
}
