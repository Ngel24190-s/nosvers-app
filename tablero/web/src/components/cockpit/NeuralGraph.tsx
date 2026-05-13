import { useEffect, useRef } from 'react';

export type ClaudeState = 'offline' | 'listening' | 'thinking' | 'speaking' | 'online';

interface Node {
  x: number;
  y: number;
  vx: number;
  vy: number;
  r: number;
  /** phase offset 0..1 for individual pulse */
  phase: number;
  /** last individual pulse start time (ms) */
  lastPulse: number;
}

interface Edge {
  a: number;
  b: number;
  /** wave activation 0..1 for synapse highlight */
  act: number;
  actStart: number;
}

interface Palette {
  node: [number, number, number];
  edge: [number, number, number];
  glow: number;
  edgeAlpha: number;
}

const PALETTES: Record<ClaudeState, Palette> = {
  offline:   { node: [63,  63,  70], edge: [63,  63,  70], glow: 0,    edgeAlpha: 0.10 },
  online:    { node: [52, 211, 153], edge: [52, 211, 153], glow: 0.45, edgeAlpha: 0.22 },
  listening: { node: [52, 211, 153], edge: [52, 211, 153], glow: 0.75, edgeAlpha: 0.35 },
  thinking:  { node: [251, 146, 60], edge: [251, 146, 60], glow: 0.95, edgeAlpha: 0.50 },
  speaking:  { node: [167, 139, 250], edge: [167, 139, 250], glow: 1.0, edgeAlpha: 0.55 },
};

function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t;
}

function lerpColor(
  a: [number, number, number],
  b: [number, number, number],
  t: number,
): [number, number, number] {
  return [lerp(a[0], b[0], t), lerp(a[1], b[1], t), lerp(a[2], b[2], t)];
}

const NODE_COUNT = 10;
const TARGET_FPS_BY_STATE: Record<ClaudeState, number> = {
  offline: 15,
  online: 24,
  listening: 30,
  thinking: 60,
  speaking: 60,
};

interface Props {
  state: ClaudeState;
  /** when true, more nodes appear; signals heavy token usage today */
  alertExtraNode?: boolean;
  className?: string;
}

/**
 * NeuralGraph — Obsidian-style force-directed canvas.
 * Pure Canvas 2D, ~250 LOC. No d3 / Three.js.
 */
export function NeuralGraph({ state, alertExtraNode = false, className }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const nodesRef = useRef<Node[]>([]);
  const edgesRef = useRef<Edge[]>([]);
  const stateRef = useRef<ClaudeState>(state);
  const stateTransitionRef = useRef({ from: state, to: state, startedAt: performance.now() });
  const lastFrameRef = useRef(0);
  const sizeRef = useRef({ w: 0, h: 0 });

  useEffect(() => {
    if (stateRef.current !== state) {
      stateTransitionRef.current = {
        from: stateRef.current,
        to: state,
        startedAt: performance.now(),
      };
      stateRef.current = state;
    }
  }, [state]);

  // init nodes + edges once
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const targetCount = NODE_COUNT + (alertExtraNode ? 1 : 0);
    if (nodesRef.current.length === targetCount) return;
    const cx = (canvas.width || 280) / (window.devicePixelRatio || 1) / 2;
    const cy = (canvas.height || 200) / (window.devicePixelRatio || 1) / 2;
    nodesRef.current = Array.from({ length: targetCount }, (_, i) => {
      const angle = (i / targetCount) * Math.PI * 2;
      const radius = 40 + Math.random() * 30;
      return {
        x: cx + Math.cos(angle) * radius,
        y: cy + Math.sin(angle) * radius,
        vx: (Math.random() - 0.5) * 0.2,
        vy: (Math.random() - 0.5) * 0.2,
        r: 3 + Math.random() * 1.5,
        phase: Math.random(),
        lastPulse: 0,
      };
    });
    // sparse random edges: average degree ~2.5
    const edges: Edge[] = [];
    for (let i = 0; i < targetCount; i++) {
      // each node connects to ~2 nearest neighbors
      const neighbors = Array.from({ length: targetCount }, (_, j) => j)
        .filter((j) => j !== i);
      neighbors.sort((a, b) => {
        const da = (nodesRef.current[a].x - nodesRef.current[i].x) ** 2 +
                   (nodesRef.current[a].y - nodesRef.current[i].y) ** 2;
        const db = (nodesRef.current[b].x - nodesRef.current[i].x) ** 2 +
                   (nodesRef.current[b].y - nodesRef.current[i].y) ** 2;
        return da - db;
      });
      for (const j of neighbors.slice(0, 2)) {
        if (i < j && !edges.find((e) => e.a === i && e.b === j)) {
          edges.push({ a: i, b: j, act: 0, actStart: 0 });
        }
      }
    }
    edgesRef.current = edges;
  }, [alertExtraNode]);

  // animation loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let raf = 0;
    let lastSpeakingWave = 0;

    const dpr = Math.min(window.devicePixelRatio || 1, 2);

    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      const w = Math.max(1, Math.floor(rect.width));
      const h = Math.max(1, Math.floor(rect.height));
      if (sizeRef.current.w === w && sizeRef.current.h === h) return;
      sizeRef.current = { w, h };
      canvas.width = w * dpr;
      canvas.height = h * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };
    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(canvas);

    const step = (t: number) => {
      raf = requestAnimationFrame(step);
      const fps = TARGET_FPS_BY_STATE[stateRef.current] ?? 30;
      if (t - lastFrameRef.current < 1000 / fps) return;
      lastFrameRef.current = t;

      const { w, h } = sizeRef.current;
      const nodes = nodesRef.current;
      const edges = edgesRef.current;
      const cx = w / 2;
      const cy = h / 2;

      // state palette transition
      const tr = stateTransitionRef.current;
      const tProg = Math.min(1, (performance.now() - tr.startedAt) / 800);
      const pFrom = PALETTES[tr.from];
      const pTo = PALETTES[tr.to];
      const nodeColor = lerpColor(pFrom.node, pTo.node, tProg);
      const edgeColor = lerpColor(pFrom.edge, pTo.edge, tProg);
      const glow = lerp(pFrom.glow, pTo.glow, tProg);
      const edgeAlpha = lerp(pFrom.edgeAlpha, pTo.edgeAlpha, tProg);
      const s = stateRef.current;

      // movement intensity by state
      const moveScale =
        s === 'offline' ? 0.05 :
        s === 'online' ? 0.25 :
        s === 'listening' ? 0.6 :
        s === 'thinking' ? 1.2 :
        1.4; // speaking

      // physics: spring along edges + center pull + light repulsion + damping
      for (const e of edges) {
        const a = nodes[e.a];
        const b = nodes[e.b];
        const dx = b.x - a.x;
        const dy = b.y - a.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 0.01;
        const rest = 55;
        const k = 0.0015 * moveScale;
        const f = (dist - rest) * k;
        const fx = (dx / dist) * f;
        const fy = (dy / dist) * f;
        a.vx += fx;
        a.vy += fy;
        b.vx -= fx;
        b.vy -= fy;
      }
      // light repulsion between any close nodes
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const dx = nodes[j].x - nodes[i].x;
          const dy = nodes[j].y - nodes[i].y;
          const d2 = dx * dx + dy * dy;
          if (d2 < 900) {
            const d = Math.sqrt(d2) || 0.01;
            const f = (900 - d2) * 0.00002 * moveScale;
            const fx = (dx / d) * f;
            const fy = (dy / d) * f;
            nodes[i].vx -= fx;
            nodes[i].vy -= fy;
            nodes[j].vx += fx;
            nodes[j].vy += fy;
          }
        }
      }
      // center pull
      for (const n of nodes) {
        n.vx += (cx - n.x) * 0.0012;
        n.vy += (cy - n.y) * 0.0012;
        // damping
        n.vx *= 0.93;
        n.vy *= 0.93;
        n.x += n.vx;
        n.y += n.vy;
        // clamp
        n.x = Math.max(8, Math.min(w - 8, n.x));
        n.y = Math.max(8, Math.min(h - 8, n.y));
      }

      // synaptic activations
      const now = t;
      if (s === 'thinking') {
        // burst random edge every ~150ms
        if (Math.random() < 0.18) {
          const e = edges[Math.floor(Math.random() * edges.length)];
          if (e) {
            e.act = 1;
            e.actStart = now;
          }
        }
      } else if (s === 'speaking') {
        // outward wave from center every ~600ms
        if (now - lastSpeakingWave > 600) {
          lastSpeakingWave = now;
          // light up edges whose midpoint is near center first
          edges.forEach((e) => {
            const a = nodes[e.a];
            const b = nodes[e.b];
            const mx = (a.x + b.x) / 2 - cx;
            const my = (a.y + b.y) / 2 - cy;
            const d = Math.sqrt(mx * mx + my * my);
            e.act = 1;
            e.actStart = now + d * 4; // delay by distance
          });
        }
      }
      // decay
      for (const e of edges) {
        const dt = (now - e.actStart) / 600;
        if (dt > 0) e.act = Math.max(0, 1 - dt);
        else e.act = 0;
      }

      // clear
      ctx.clearRect(0, 0, w, h);

      // edges
      const [er, eg, eb] = edgeColor;
      for (const e of edges) {
        const a = nodes[e.a];
        const b = nodes[e.b];
        const baseA = edgeAlpha;
        const act = e.act;
        ctx.strokeStyle = `rgba(${er|0},${eg|0},${eb|0},${baseA + act * 0.5})`;
        ctx.lineWidth = 1 + act * 1.3;
        ctx.beginPath();
        ctx.moveTo(a.x, a.y);
        ctx.lineTo(b.x, b.y);
        ctx.stroke();
      }

      // nodes
      const [nr, ng, nb] = nodeColor;
      for (const n of nodes) {
        // individual pulse: per-node
        let pulse = 0;
        if (s === 'listening') {
          pulse = 0.5 + 0.5 * Math.sin((t / 1500 + n.phase) * Math.PI * 2);
        } else if (s === 'online') {
          // rare brief flash
          if (now - n.lastPulse > 4000 + n.phase * 4000) {
            n.lastPulse = now;
          }
          const since = (now - n.lastPulse) / 300;
          pulse = since < 1 ? 1 - since : 0;
        } else if (s === 'thinking') {
          pulse = Math.random() < 0.3 ? Math.random() : pulse;
        } else if (s === 'speaking') {
          pulse = 0.6 + 0.4 * Math.sin((t / 220 + n.phase * 2) * Math.PI);
        }
        const radius = n.r + pulse * 1.4;
        const alpha = 0.65 + pulse * 0.35;
        if (glow > 0) {
          const g = ctx.createRadialGradient(n.x, n.y, 0, n.x, n.y, radius * 4);
          g.addColorStop(0, `rgba(${nr|0},${ng|0},${nb|0},${0.35 * glow * (0.6 + pulse * 0.4)})`);
          g.addColorStop(1, `rgba(${nr|0},${ng|0},${nb|0},0)`);
          ctx.fillStyle = g;
          ctx.beginPath();
          ctx.arc(n.x, n.y, radius * 4, 0, Math.PI * 2);
          ctx.fill();
        }
        ctx.fillStyle = `rgba(${nr|0},${ng|0},${nb|0},${alpha})`;
        ctx.beginPath();
        ctx.arc(n.x, n.y, radius, 0, Math.PI * 2);
        ctx.fill();
      }
    };

    raf = requestAnimationFrame(step);
    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className={className}
      style={{ width: '100%', height: '100%', display: 'block' }}
      title="Claude · NosVers"
    />
  );
}
