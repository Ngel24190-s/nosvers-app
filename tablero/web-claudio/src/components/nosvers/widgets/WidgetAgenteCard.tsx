import { useState } from 'react';
import { Play, Loader2, Check, AlertTriangle } from 'lucide-react';
import { apiJson } from '../../../lib/api';
import type { AgenteEstado } from '../../../lib/api-types';

interface Props {
  nombre: string;
  estado: AgenteEstado | undefined;
}

const AVATAR: Record<string, string> = {
  orchestrator: '🎯',
  agt00_intelligence: '🧠',
  agt01_visual: '📸',
  agt02_instagram: '📱',
  agt04_seo: '🔍',
  agt05_africa: '🌍',
  agt06_infoproduct: '📦',
  agt07_diario: '📰',
  agt07_youtube: '🎥',
  agt08_facebook: '👥',
  agt_infra: '🔧',
  agt_eisenia: '🪱',
  agt_analyste: '📊',
  agt_directeur: '🎩',
};

const LABEL: Record<string, string> = {
  orchestrator: 'Orchestrator',
  agt00_intelligence: 'Intelligence',
  agt01_visual: 'Visual · IG',
  agt02_instagram: 'Instagram',
  agt04_seo: 'SEO blog',
  agt05_africa: 'África · emails',
  agt06_infoproduct: 'Infoproduct',
  agt07_diario: 'Diario',
  agt07_youtube: 'YouTube',
  agt08_facebook: 'Facebook',
  agt_infra: 'Infra',
  agt_eisenia: 'Eisenia · compost',
  agt_analyste: 'Analyste',
  agt_directeur: 'Directeur',
};

function relativeTime(ts: number): string {
  if (!ts || ts <= 0) return '—';
  const diff = Date.now() / 1000 - ts;
  if (diff < 60) return 'ahora';
  if (diff < 3600) return `${Math.floor(diff / 60)} min`;
  if (diff < 86400) return `${Math.floor(diff / 3600)} h`;
  return `${Math.floor(diff / 86400)} d`;
}

function badgeClasses(state: string | undefined): string {
  switch (state) {
    case 'running':
      return 'bg-emerald-100 text-emerald-800';
    case 'error':
      return 'bg-red-100 text-red-800';
    case 'missing':
      return 'bg-stone-200 text-stone-600';
    default:
      return 'bg-lime-50 text-lime-800';
  }
}

export default function WidgetAgenteCard({ nombre, estado }: Props) {
  const [busy, setBusy] = useState(false);
  const [flash, setFlash] = useState<'ok' | 'err' | null>(null);

  const avatar = AVATAR[nombre] ?? '🤖';
  const label = LABEL[nombre] ?? nombre;
  const state = estado?.state ?? 'idle';
  const lastRun = estado?.last_run_ts ?? 0;

  async function lanzar() {
    if (busy || state === 'missing') return;
    setBusy(true);
    setFlash(null);
    try {
      await apiJson('/tablero/api/v2/agente_ejecutar', {
        method: 'POST',
        body: JSON.stringify({ nombre }),
      });
      setFlash('ok');
    } catch {
      setFlash('err');
    } finally {
      setBusy(false);
      setTimeout(() => setFlash(null), 3000);
    }
  }

  return (
    <div className="flex items-center gap-3 p-3 rounded-xl bg-white border border-emerald-200/60">
      <div className="text-2xl select-none flex-shrink-0">{avatar}</div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-fg truncate">{label}</span>
          <span className={`text-[10px] uppercase tracking-wide px-1.5 py-0.5 rounded-full ${badgeClasses(state)}`}>
            {state}
          </span>
        </div>
        <div className="text-[11px] text-muted">
          {state === 'missing' ? 'script no instalado' : `última run: ${relativeTime(lastRun)}`}
          {estado?.last_status && state !== 'missing' && (
            <span className="ml-2 opacity-70">· {estado.last_status.slice(0, 40)}</span>
          )}
        </div>
      </div>
      <button
        onClick={lanzar}
        disabled={busy || state === 'missing'}
        className={`flex-shrink-0 w-9 h-9 rounded-full flex items-center justify-center transition-colors ${
          state === 'missing'
            ? 'bg-stone-100 text-stone-400 cursor-not-allowed'
            : flash === 'ok'
              ? 'bg-emerald-500 text-white'
              : flash === 'err'
                ? 'bg-red-500 text-white'
                : 'bg-emerald-600 hover:bg-emerald-700 text-white'
        }`}
        title={state === 'missing' ? 'Script no instalado' : `Ejecutar ${nombre}`}
        aria-label={`Ejecutar ${nombre}`}
      >
        {busy ? <Loader2 size={16} className="animate-spin" /> :
          flash === 'ok' ? <Check size={16} /> :
            flash === 'err' ? <AlertTriangle size={16} /> :
              <Play size={14} />}
      </button>
    </div>
  );
}
