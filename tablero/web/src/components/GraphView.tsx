/**
 * GraphView — grafo de conexiones de wiki-links (US12).
 *
 * Implementación pragmática:
 *   - SVG cuando N < 100 (hover preciso).
 *   - canvas + d3-force con sampling top-N para vaults grandes.
 * Aquí entregamos la versión SVG estable, suficiente para Angel y África
 * a corto plazo. Sampling automático para evitar bloquear el navegador.
 */
import { useEffect, useMemo, useRef, useState } from 'react';
import {
  forceCenter,
  forceLink,
  forceManyBody,
  forceSimulation,
  type Simulation,
  type SimulationLinkDatum,
  type SimulationNodeDatum,
} from 'd3-force';
import { getWikiIndex } from '../lib/api';

interface GraphNode extends SimulationNodeDatum {
  id: string;
  count: number; // backlinks recibidos
}

interface GraphLink extends SimulationLinkDatum<GraphNode> {}

const SAMPLING_LIMIT = 200; // FR-041

export function GraphView() {
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [links, setLinks] = useState<GraphLink[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [totalNodes, setTotalNodes] = useState(0);
  const [hover, setHover] = useState<GraphNode | null>(null);

  const svgRef = useRef<SVGSVGElement | null>(null);
  const simRef = useRef<Simulation<GraphNode, GraphLink> | null>(null);

  useEffect(() => {
    void (async () => {
      setLoading(true);
      try {
        const r = await getWikiIndex();
        const idx = r.index ?? {};
        const linkMap = new Map<string, Set<string>>();
        const counts = new Map<string, number>();
        for (const [target, backlinks] of Object.entries(idx)) {
          counts.set(target, (counts.get(target) ?? 0) + backlinks.length);
          for (const b of backlinks) {
            const src = b.source_slug;
            counts.set(src, counts.get(src) ?? 0);
            linkMap.set(src, linkMap.get(src) ?? new Set());
            linkMap.get(src)!.add(target);
          }
        }
        let allNodes: GraphNode[] = [...counts.entries()].map(([id, count]) => ({ id, count }));
        setTotalNodes(allNodes.length);
        // Sampling
        if (allNodes.length > SAMPLING_LIMIT) {
          allNodes = [...allNodes].sort((a, b) => b.count - a.count).slice(0, SAMPLING_LIMIT);
        }
        const allowedIds = new Set(allNodes.map((n) => n.id));
        const allLinks: GraphLink[] = [];
        linkMap.forEach((targets, src) => {
          if (!allowedIds.has(src)) return;
          targets.forEach((t) => {
            if (allowedIds.has(t)) {
              allLinks.push({ source: src, target: t });
            }
          });
        });
        setNodes(allNodes);
        setLinks(allLinks);
        setError(null);
      } catch (e) {
        setError(String(e));
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  useEffect(() => {
    if (nodes.length === 0) return;
    const width = 800;
    const height = 500;
    const sim = forceSimulation<GraphNode>(nodes)
      .force('link', forceLink<GraphNode, GraphLink>(links).distance(60).strength(0.5))
      .force('charge', forceManyBody().strength(-80))
      .force('center', forceCenter(width / 2, height / 2))
      .alphaDecay(0.05);
    simRef.current = sim;
    sim.on('tick', () => {
      // setNodes para re-render
      setNodes((prev) => [...prev]);
    });
    sim.on('end', () => setNodes((prev) => [...prev]));
    return () => {
      sim.stop();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodes.length, links.length]);

  const stats = useMemo(() => {
    return {
      visibles: nodes.length,
      total: totalNodes,
      links: links.length,
      sampled: totalNodes > SAMPLING_LIMIT,
    };
  }, [nodes, links, totalNodes]);

  if (loading) {
    return <p className="text-sm text-tinta/50">Construyendo grafo…</p>;
  }
  if (error) {
    return <p className="text-sm text-red-700">{error}</p>;
  }
  if (nodes.length < 2) {
    return (
      <p className="rounded border border-tinta/10 bg-cream/40 p-4 text-center text-sm text-tinta/50">
        Necesitas al menos 2 wiki-links para ver conexiones. Usa <code>[[nota]]</code> al editar notas.
      </p>
    );
  }

  return (
    <div className="rounded border border-tinta/10 bg-white p-3">
      <div className="mb-2 flex items-center justify-between text-xs text-tinta/60">
        <span>{stats.visibles} notas · {stats.links} enlaces</span>
        {stats.sampled && (
          <span className="text-amber-700">
            (mostrando top-{SAMPLING_LIMIT} de {stats.total} por conexiones)
          </span>
        )}
      </div>
      <svg
        ref={svgRef}
        viewBox="0 0 800 500"
        className="w-full bg-cream/40"
        style={{ height: 500 }}
      >
        {links.map((l, i) => {
          const s = l.source as GraphNode;
          const t = l.target as GraphNode;
          if (typeof s !== 'object' || typeof t !== 'object') return null;
          return (
            <line
              key={i}
              x1={s.x ?? 0}
              y1={s.y ?? 0}
              x2={t.x ?? 0}
              y2={t.y ?? 0}
              stroke="rgba(20,20,20,0.15)"
              strokeWidth={1}
            />
          );
        })}
        {nodes.map((n) => {
          const r = Math.max(4, 4 + Math.sqrt(n.count) * 2);
          return (
            <g key={n.id} transform={`translate(${n.x ?? 0}, ${n.y ?? 0})`}>
              <circle
                r={r}
                fill="#10b981"
                stroke="#fff"
                strokeWidth={1.5}
                onMouseEnter={() => setHover(n)}
                onMouseLeave={() => setHover((h) => (h?.id === n.id ? null : h))}
                style={{ cursor: 'pointer' }}
              />
              {hover?.id === n.id && (
                <text x={r + 4} y={4} className="text-[10px]" fill="#1c1510" pointerEvents="none">
                  {n.id} (×{n.count})
                </text>
              )}
            </g>
          );
        })}
      </svg>
    </div>
  );
}
