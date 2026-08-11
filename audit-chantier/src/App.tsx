import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

import { Actions } from './components/Actions';
import { Header } from './components/Header';
import { ScreenNav } from './components/ScreenNav';
import { StorageBanner } from './components/StorageBanner';
import { FieldRenderer } from './fields/FieldRenderer';
import { VERSION } from './config';
import { anomalies, ecransVisibles, champsVisibles, progression } from './lib/validation';
import type { AuditData } from './schema/types';
import {
  initStorage,
  lireBrouillon,
  poidsBrouillon,
  sauverBrouillon,
  storageState,
  effacerBrouillon,
} from './storage/storage';
import type { StorageState } from './storage/storage';

/** `datetime-local` attend une heure locale, pas un ISO UTC. */
function maintenantLocal(): string {
  const d = new Date();
  d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
  return d.toISOString().slice(0, 16);
}

const auditVierge = (): AuditData => ({ date_audit: maintenantLocal() });

export default function App() {
  const [etatStockage, setEtatStockage] = useState<StorageState>('indisponible');
  const [data, setData] = useState<AuditData>(auditVierge);
  const [index, setIndex] = useState(0);
  const [pret, setPret] = useState(false);
  const hautRef = useRef<HTMLDivElement>(null);

  // Au démarrage : tester le stockage, puis reprendre le brouillon éventuel.
  useEffect(() => {
    setEtatStockage(initStorage());
    const brouillon = lireBrouillon();
    if (brouillon) setData(brouillon);
    setPret(true);
  }, []);

  // Sauvegarde à chaque modification (uniquement si le stockage répond).
  useEffect(() => {
    if (!pret) return;
    const ok = sauverBrouillon(data);
    if (!ok && storageState() !== etatStockage) setEtatStockage(storageState());
  }, [data, pret, etatStockage]);

  const ecrans = useMemo(() => ecransVisibles(data), [data]);
  const problemes = useMemo(() => anomalies(data), [data]);
  const pct = useMemo(() => progression(data), [data]);
  const poids = useMemo(() => poidsBrouillon(data), [data]);

  // L'écran 6 apparaît et disparaît selon les processus amiante : on garde
  // l'index dans les bornes plutôt que d'afficher une page vide.
  const indexSur = Math.min(index, ecrans.length - 1);
  const ecran = ecrans[indexSur];

  const setChamp = useCallback((id: string, valeur: unknown) => {
    setData((precedent) => {
      const suivant = { ...precedent, [id]: valeur };
      if (valeur === undefined || valeur === '') delete suivant[id];
      return suivant;
    });
  }, []);

  const aller = useCallback(
    (i: number) => {
      setIndex(i);
      hautRef.current?.scrollIntoView({ behavior: 'auto', block: 'start' });
    },
    [],
  );

  /** Saut vers un champ signalé depuis le bloc de clôture. */
  const allerAuChamp = useCallback(
    (champId: string) => {
      const cible = ecrans.findIndex((e) =>
        champsVisibles(e, data).some((c) => c.id === champId),
      );
      if (cible >= 0) {
        setIndex(cible);
        // Laisse React peindre l'écran avant de faire défiler jusqu'au champ.
        window.setTimeout(() => {
          document
            .getElementById(`champ-${champId}`)
            ?.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }, 50);
      }
    },
    [ecrans, data],
  );

  const reinitialiser = useCallback(() => {
    effacerBrouillon();
    setData(auditVierge());
    setIndex(0);
    hautRef.current?.scrollIntoView({ block: 'start' });
  }, []);

  const champsManquants = useMemo(
    () => new Set(problemes.filter((p) => p.niveau === 'bloquant').map((p) => p.champId)),
    [problemes],
  );
  const photosManquantes = useMemo(
    () => new Set(problemes.filter((p) => p.niveau === 'alerte').map((p) => p.champId)),
    [problemes],
  );

  if (!pret || !ecran) return null;

  const dernier = indexSur === ecrans.length - 1;

  return (
    <div ref={hautRef} className="mx-auto min-h-screen max-w-2xl pb-24">
      <Header progression={pct} />
      <StorageBanner etat={etatStockage} poids={poids} />
      <ScreenNav ecrans={ecrans} index={indexSur} data={data} onSelect={aller} />

      <main className="px-4 pt-5">
        <h2 className="text-xl font-extrabold uppercase tracking-di">
          {ecran.title}
          {ecran.ref && <span className="ml-2 text-base font-bold text-di">({ecran.ref})</span>}
        </h2>
        {ecran.intro && <p className="mt-1 text-[13px] leading-snug text-muted">{ecran.intro}</p>}

        <div className="mt-4 divide-y divide-line">
          {champsVisibles(ecran, data).map((champ) => (
            <FieldRenderer
              key={champ.id}
              champ={champ}
              data={data}
              onChange={setChamp}
              manquant={champsManquants.has(champ.id)}
              photoManquante={photosManquantes.has(champ.id)}
            />
          ))}
        </div>

        {dernier && (
          <Actions
            data={data}
            anomalies={problemes}
            onAller={allerAuChamp}
            onImport={(d) => {
              setData(d);
              setIndex(0);
            }}
            onReinit={reinitialiser}
          />
        )}

        <p className="py-6 text-center text-[11px] uppercase tracking-di text-muted">
          Audit chantier QSE · v{VERSION}
        </p>
      </main>

      <nav className="no-print fixed inset-x-0 bottom-0 z-20 mx-auto flex max-w-2xl gap-2 border-t-2 border-ink bg-paper p-3">
        <button
          type="button"
          className="di-btn-ghost flex-1"
          disabled={indexSur === 0}
          onClick={() => aller(indexSur - 1)}
        >
          Précédent
        </button>
        <button
          type="button"
          className="di-btn-primary flex-1"
          disabled={dernier}
          onClick={() => aller(indexSur + 1)}
        >
          Suivant
        </button>
      </nav>
    </div>
  );
}
