import { useCallback, useEffect, useState } from 'react';
import type { LayoutItem } from 'react-grid-layout';

type Layout = LayoutItem[];

export type WidgetId =
  | 'claude'
  | 'vps'
  | 'revenue'
  | 'aegis'
  | 'activity'
  | 'wake'
  | 'vault'
  | 'agentes'
  | 'gmail'
  | 'calendar'
  | 'freqtrade'
  | 'stripe-toaster'; // floating; no en grid pero lo mantenemos por simetría

// Layout default — grid 12 col, rowHeight 80.
// Fila superior (h=4): claude(3) | vps(3) | revenue(3) | aegis(3)
// Fila media   (h=4): activity(6) | wake(3) | vault(3)
// Fila baja    (h=4): agentes(3) | gmail(3) | calendar(3) | freqtrade(3)
export const DEFAULT_LAYOUT: Layout = [
  { i: 'claude', x: 0, y: 0, w: 3, h: 4, minW: 2, minH: 3 },
  { i: 'vps', x: 3, y: 0, w: 3, h: 4, minW: 2, minH: 3 },
  { i: 'revenue', x: 6, y: 0, w: 3, h: 4, minW: 2, minH: 3 },
  { i: 'aegis', x: 9, y: 0, w: 3, h: 4, minW: 2, minH: 3 },
  { i: 'activity', x: 0, y: 4, w: 6, h: 5, minW: 3, minH: 3 },
  { i: 'wake', x: 6, y: 4, w: 3, h: 5, minW: 2, minH: 3 },
  { i: 'vault', x: 9, y: 4, w: 3, h: 5, minW: 2, minH: 3 },
  { i: 'agentes', x: 0, y: 9, w: 3, h: 4, minW: 2, minH: 3 },
  { i: 'gmail', x: 3, y: 9, w: 3, h: 4, minW: 2, minH: 3 },
  { i: 'calendar', x: 6, y: 9, w: 3, h: 4, minW: 2, minH: 3 },
  { i: 'freqtrade', x: 9, y: 9, w: 3, h: 4, minW: 2, minH: 3 },
];

function loadLayout(sub: string): Layout {
  if (typeof window === 'undefined') return DEFAULT_LAYOUT;
  try {
    const raw = localStorage.getItem(`cockpit_layout_${sub}`);
    if (!raw) return DEFAULT_LAYOUT;
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return DEFAULT_LAYOUT;
    // sanity: cada item debe tener i, x, y, w, h
    const valid = parsed.every(
      (p) =>
        typeof p === 'object' &&
        typeof p.i === 'string' &&
        typeof p.x === 'number' &&
        typeof p.y === 'number' &&
        typeof p.w === 'number' &&
        typeof p.h === 'number',
    );
    if (!valid) return DEFAULT_LAYOUT;
    // merge: si faltan widgets nuevos, añadirlos del default
    const ids = new Set(parsed.map((p) => p.i));
    const missing = DEFAULT_LAYOUT.filter((d) => !ids.has(d.i));
    return [...parsed, ...missing];
  } catch {
    return DEFAULT_LAYOUT;
  }
}

export function useCockpitLayout(sub: string) {
  const [layout, setLayout] = useState<Layout>(() => loadLayout(sub));

  useEffect(() => {
    setLayout(loadLayout(sub));
  }, [sub]);

  const onLayoutChange = useCallback(
    (newLayout: Layout) => {
      setLayout(newLayout);
      try {
        localStorage.setItem(`cockpit_layout_${sub}`, JSON.stringify(newLayout));
      } catch {
        /* ignore */
      }
    },
    [sub],
  );

  const reset = useCallback(() => {
    setLayout(DEFAULT_LAYOUT);
    try {
      localStorage.removeItem(`cockpit_layout_${sub}`);
    } catch {
      /* ignore */
    }
  }, [sub]);

  return { layout, onLayoutChange, reset };
}
