/**
 * InfraSidebar — badges de estado de infra (US10).
 *
 * Polling 60s. Cada badge expandible para detalle/link.
 */
import { useCallback, useEffect, useState } from 'react';
import { ChevronDown, ChevronRight, ExternalLink } from 'lucide-react';
import { getInfraStatus, type InfraBadge } from '../lib/api';
import { AgentRunner } from './AgentRunner';

function colorClass(status: InfraBadge['status']): string {
  switch (status) {
    case 'ok': return 'bg-emerald-100 text-emerald-700';
    case 'warn': return 'bg-amber-100 text-amber-700';
    case 'error': return 'bg-red-100 text-red-700';
  }
}

function statusIcon(status: InfraBadge['status']): string {
  return status === 'ok' ? '✓' : status === 'warn' ? '⚠' : '✕';
}

export function InfraSidebar() {
  const [badges, setBadges] = useState<InfraBadge[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [collapsed, setCollapsed] = useState(false);

  const refrescar = useCallback(async () => {
    try {
      const r = await getInfraStatus();
      setBadges(r.badges);
      setError(null);
    } catch (e) {
      setError(String(e));
    }
  }, []);

  useEffect(() => {
    void refrescar();
    const handle = setInterval(refrescar, 60_000);
    return () => clearInterval(handle);
  }, [refrescar]);

  return (
    <section className="rounded border border-tinta/10 bg-cream/40 p-3">
      <header
        onClick={() => setCollapsed((v) => !v)}
        className="mb-2 flex cursor-pointer items-center justify-between text-xs font-medium uppercase text-tinta/60"
      >
        <span>Infra</span>
        {collapsed ? <ChevronRight size={12} /> : <ChevronDown size={12} />}
      </header>
      {!collapsed && (
        <>
          {error && <p className="text-xs text-red-700">{error}</p>}
          <ul className="space-y-1">
            {badges.map((b) => (
              <li key={b.id} className={`rounded px-2 py-1 text-xs ${colorClass(b.status)}`}>
                <button
                  type="button"
                  onClick={() => setExpanded((e) => (e === b.id ? null : b.id))}
                  className="flex w-full items-center justify-between"
                >
                  <span className="flex items-center gap-2">
                    <span className="font-mono">{statusIcon(b.status)}</span>
                    <span className="font-medium uppercase">{b.id}</span>
                  </span>
                  <span className="font-mono text-[10px]">{b.value ?? b.detail ?? ''}</span>
                </button>
                {expanded === b.id && (
                  <div className="mt-1 border-t border-current/20 pt-1 text-[10px] opacity-80">
                    {b.detail && <p>{b.detail}</p>}
                    {b.link && (
                      <a href={b.link} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 underline">
                        <ExternalLink size={10} /> abrir
                      </a>
                    )}
                    {b.crones && (
                      <ul className="mt-1 space-y-0.5">
                        {b.crones.map((c) => (
                          <li key={c.name} className="font-mono">
                            {statusIcon(c.status)} {c.name}: {c.last_run?.slice(0, 16) ?? c.detail ?? ''}
                          </li>
                        ))}
                      </ul>
                    )}
                    <p className="mt-1 text-tinta/40">check: {b.last_check?.slice(0, 19)}</p>
                  </div>
                )}
              </li>
            ))}
          </ul>

          <hr className="my-3 border-tinta/10" />
          <h4 className="mb-1 text-xs font-medium uppercase text-tinta/60">Agentes</h4>
          <AgentRunner />
        </>
      )}
    </section>
  );
}
