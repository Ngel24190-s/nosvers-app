import { AGENCE, ENTITE } from '../config';

export function Header({ progression }: { progression: number }) {
  return (
    <header className="sticky top-0 z-20 bg-di text-white">
      <div className="flex items-baseline justify-between px-4 pb-2 pt-3">
        <div>
          <p className="text-[11px] font-bold uppercase tracking-[0.18em] opacity-90">
            {ENTITE} · {AGENCE}
          </p>
          <h1 className="text-lg font-extrabold uppercase tracking-di">Audit chantier QSE</h1>
        </div>
        <span className="text-[11px] font-bold tabular-nums">{progression}%</span>
      </div>
      <div
        className="h-1 bg-white/30"
        role="progressbar"
        aria-valuenow={progression}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <div className="h-full bg-white transition-all" style={{ width: `${progression}%` }} />
      </div>
    </header>
  );
}
