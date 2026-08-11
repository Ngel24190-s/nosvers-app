import { useEffect, useRef } from 'react';
import type { AuditData, Screen } from '../schema/types';
import { progressionEcran } from '../lib/validation';

export function ScreenNav({
  ecrans,
  index,
  data,
  onSelect,
}: {
  ecrans: Screen[];
  index: number;
  data: AuditData;
  onSelect: (i: number) => void;
}) {
  const refs = useRef<(HTMLButtonElement | null)[]>([]);

  // L'onglet courant reste visible quand on avance avec « Suivant ».
  useEffect(() => {
    refs.current[index]?.scrollIntoView({ block: 'nearest', inline: 'center' });
  }, [index]);

  return (
    <nav className="no-print sticky top-[68px] z-10 border-b-2 border-ink bg-paper">
      <ol className="flex overflow-x-auto">
        {ecrans.map((e, i) => {
          const pct = progressionEcran(e, data);
          const actif = i === index;
          return (
            <li key={e.id} className="shrink-0">
              <button
                ref={(el) => {
                  refs.current[i] = el;
                }}
                type="button"
                aria-current={actif ? 'step' : undefined}
                className={`flex items-center gap-2 border-r border-line px-3 py-2.5 text-[12px] font-bold uppercase tracking-di ${
                  actif ? 'bg-ink text-paper' : 'bg-paper text-muted'
                }`}
                onClick={() => onSelect(i)}
              >
                <span
                  className={`inline-block h-2 w-2 rounded-full ${
                    pct === 100 ? 'bg-ok' : pct > 0 ? 'bg-di' : 'bg-line'
                  }`}
                />
                {i + 1}. {e.short}
              </button>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
