import { EVALUATIONS } from '../schema/types';
import type { ControlField, ControlValue, Evaluation, Media } from '../schema/types';
import { MediaInput } from './MediaInput';

const COULEURS: Record<Evaluation, string> = {
  C: 'border-ok bg-ok text-white',
  A: 'border-di bg-di text-white',
  NA: 'border-na bg-na text-white',
};

/** Point de contrôle : évaluation C / Améliorable / NA, puis commentaire,
 *  responsable, délai et photos. C'est le motif répété ~27 fois dans la grille. */
export function ControlPoint({
  champ,
  valeur,
  onChange,
  photoManquante,
}: {
  champ: ControlField;
  valeur: ControlValue;
  onChange: (v: ControlValue) => void;
  photoManquante?: boolean;
}) {
  const maj = (patch: Partial<ControlValue>) => onChange({ ...valeur, ...patch });
  const medias = (valeur.medias ?? []) as Media[];

  // Le détail ne s'ouvre pas pour un point conforme sans remarque : sur le
  // terrain, l'essentiel est d'enchaîner vite les points conformes.
  const detailOuvert =
    valeur.evaluation === 'A' ||
    !!valeur.commentaire ||
    !!valeur.responsable ||
    !!valeur.delai ||
    medias.length > 0 ||
    (champ.photoRequise && valeur.evaluation === 'C');

  return (
    <div>
      <div className="grid grid-cols-3 gap-2">
        {EVALUATIONS.map((e) => {
          const actif = valeur.evaluation === e.value;
          return (
            <button
              key={e.value}
              type="button"
              aria-pressed={actif}
              className={`di-btn !px-2 !py-3 ${
                actif ? COULEURS[e.value] : 'border-line bg-paper text-muted'
              }`}
              onClick={() => maj({ evaluation: actif ? undefined : e.value })}
            >
              {e.label}
            </button>
          );
        })}
      </div>

      {detailOuvert && (
        <div className="mt-3 space-y-3 border-2 border-line bg-[#fafafa] p-3">
          <div>
            <label className="di-label !text-[11px]" htmlFor={`${champ.id}-com`}>
              Commentaire / action requise
            </label>
            <textarea
              id={`${champ.id}-com`}
              rows={3}
              className="di-input mt-1"
              value={valeur.commentaire ?? ''}
              onChange={(e) => maj({ commentaire: e.target.value })}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="di-label !text-[11px]" htmlFor={`${champ.id}-resp`}>
                Responsable
              </label>
              <input
                id={`${champ.id}-resp`}
                type="text"
                className="di-input mt-1"
                value={valeur.responsable ?? ''}
                onChange={(e) => maj({ responsable: e.target.value })}
              />
            </div>
            <div>
              <label className="di-label !text-[11px]" htmlFor={`${champ.id}-delai`}>
                Délai
              </label>
              <input
                id={`${champ.id}-delai`}
                type="date"
                className="di-input mt-1"
                value={valeur.delai ?? ''}
                onChange={(e) => maj({ delai: e.target.value })}
              />
            </div>
          </div>

          <div>
            <span className="di-label !text-[11px]">
              Photos{champ.photoRequise && <span className="ml-1 text-di">— attendues</span>}
            </span>
            <div className="mt-1">
              <MediaInput compact medias={medias} onChange={(m) => maj({ medias: m })} />
            </div>
            {photoManquante && (
              <p className="mt-2 text-[12px] font-bold uppercase tracking-di text-di-dark">
                Photo attendue sur ce point de contrôle
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
