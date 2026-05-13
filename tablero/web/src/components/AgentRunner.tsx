/**
 * AgentRunner — botones para lanzar agentes del catálogo (US11).
 *
 * Output del agente se muestra en panel expandible inline.
 */
import { useEffect, useState } from 'react';
import { Play, Loader2 } from 'lucide-react';
import { ejecutarAgente, getAgentesCatalogo, type AgenteCatalogo } from '../lib/api';

export function AgentRunner() {
  const [catalogo, setCatalogo] = useState<AgenteCatalogo[]>([]);
  const [output, setOutput] = useState<{ slug: string; text: string; duration_s: number } | null>(null);
  const [running, setRunning] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      try {
        const r = await getAgentesCatalogo();
        setCatalogo(r.agentes);
      } catch (e) {
        setError(String(e));
      }
    })();
  }, []);

  async function lanzar(slug: string) {
    setRunning(slug);
    setError(null);
    try {
      const r = await ejecutarAgente(slug);
      setOutput({ slug, text: r.output, duration_s: r.duration_s });
      if (!r.ok) setError(r.error ?? 'fallo');
    } catch (e) {
      setError(String(e));
    } finally {
      setRunning(null);
    }
  }

  return (
    <div className="space-y-1">
      {error && <p className="text-xs text-red-700">{error}</p>}
      {catalogo.map((a) => (
        <button
          key={a.slug}
          type="button"
          onClick={() => lanzar(a.slug)}
          disabled={running !== null}
          className="flex w-full items-center justify-between rounded border border-tinta/10 bg-white px-2 py-1 text-left text-xs hover:border-emerald-400 disabled:opacity-50"
        >
          <span>
            <span className="font-mono text-tinta">{a.slug}</span>
            <span className="ml-2 text-tinta/50">{a.label}</span>
          </span>
          {running === a.slug ? <Loader2 size={12} className="animate-spin" /> : <Play size={12} />}
        </button>
      ))}
      {output && (
        <div className="mt-2 rounded border border-tinta/10 bg-tinta/5 p-2">
          <p className="mb-1 text-[10px] uppercase text-tinta/50">
            {output.slug} · {output.duration_s.toFixed(1)}s
          </p>
          <pre className="max-h-40 overflow-y-auto whitespace-pre-wrap text-[10px] font-mono text-tinta">
            {output.text || '(vacío)'}
          </pre>
        </div>
      )}
    </div>
  );
}
