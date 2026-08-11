import { useState } from 'react';
import type {
  AuditData,
  ChoiceField,
  ControlValue,
  Field,
  Media,
  NumberField,
  Option,
  TextField,
} from '../schema/types';
import { ControlPoint } from './ControlPoint';
import { FieldShell } from './FieldShell';
import { MediaInput } from './MediaInput';
import { SignaturePad } from './SignaturePad';

const AUTRE = '__autre__';

/** Aiguillage unique : ajouter un type de champ = ajouter un `case` ici et une
 *  entrée dans `FieldType`. Aucun autre fichier n'a besoin de changer. */
export function FieldRenderer({
  champ,
  data,
  onChange,
  manquant,
  photoManquante,
}: {
  champ: Field;
  data: AuditData;
  onChange: (id: string, valeur: unknown) => void;
  manquant?: boolean;
  photoManquante?: boolean;
}) {
  const valeur = data[champ.id];
  const set = (v: unknown) => onChange(champ.id, v);

  switch (champ.type) {
    case 'control':
      return (
        <FieldShell champ={champ} manquant={manquant}>
          <ControlPoint
            champ={champ}
            valeur={(valeur as ControlValue) ?? {}}
            onChange={set}
            photoManquante={photoManquante}
          />
        </FieldShell>
      );

    case 'datetime':
      return (
        <FieldShell champ={champ} manquant={manquant}>
          <input
            id={champ.id}
            type="datetime-local"
            className="di-input"
            value={(valeur as string) ?? ''}
            onChange={(e) => set(e.target.value)}
          />
        </FieldShell>
      );

    case 'text':
      return (
        <FieldShell champ={champ} manquant={manquant}>
          <input
            id={champ.id}
            type="text"
            className="di-input"
            placeholder={(champ as TextField).placeholder}
            value={(valeur as string) ?? ''}
            onChange={(e) => set(e.target.value)}
          />
        </FieldShell>
      );

    case 'textarea':
      return (
        <FieldShell champ={champ} manquant={manquant}>
          <textarea
            id={champ.id}
            rows={(champ as TextField).rows ?? 3}
            className="di-input"
            placeholder={(champ as TextField).placeholder}
            value={(valeur as string) ?? ''}
            onChange={(e) => set(e.target.value)}
          />
        </FieldShell>
      );

    case 'geoloc':
      return (
        <FieldShell champ={champ} manquant={manquant}>
          <GeolocInput valeur={(valeur as string) ?? ''} onChange={set} id={champ.id} />
        </FieldShell>
      );

    case 'number': {
      const n = champ as NumberField;
      const num = typeof valeur === 'number' ? valeur : undefined;
      const alerte = typeof num === 'number' ? (n.alert?.(num) ?? null) : null;
      return (
        <FieldShell champ={champ} manquant={manquant} alerte={alerte}>
          <div className="flex items-stretch">
            <input
              id={champ.id}
              type="number"
              inputMode="decimal"
              step={n.step}
              min={n.min}
              max={n.max}
              className={`di-input ${alerte ? '!border-di' : ''}`}
              value={num ?? ''}
              onChange={(e) => set(e.target.value === '' ? undefined : Number(e.target.value))}
            />
            {n.unit && (
              <span className="flex items-center border-2 border-l-0 border-line bg-[#fafafa] px-3 text-sm font-bold">
                {n.unit}
              </span>
            )}
          </div>
        </FieldShell>
      );
    }

    case 'checkbox':
      return (
        <div id={`champ-${champ.id}`} className="py-4 pl-3">
          <label className="flex items-start gap-3">
            <input
              id={champ.id}
              type="checkbox"
              className="mt-0.5 h-6 w-6 accent-[var(--di-red)]"
              checked={valeur === true}
              onChange={(e) => set(e.target.checked)}
            />
            <span>
              <span className="di-label">
                {champ.label}
                {champ.required && <span className="ml-1 text-di">*</span>}
              </span>
              {champ.hint && <span className="mt-1 block text-[13px] text-muted">{champ.hint}</span>}
            </span>
          </label>
        </div>
      );

    case 'radio': {
      const c = champ as ChoiceField;
      return (
        <FieldShell champ={champ} manquant={manquant}>
          <div className={c.inline ? 'flex flex-wrap gap-2' : 'grid gap-2'}>
            {c.options.map((o) => {
              const actif = valeur === o.value;
              return (
                <button
                  key={o.value}
                  type="button"
                  aria-pressed={actif}
                  className={
                    actif
                      ? 'di-btn border-di bg-di text-white'
                      : 'di-btn border-line bg-paper text-muted'
                  }
                  onClick={() => set(actif ? undefined : o.value)}
                >
                  {o.label}
                </button>
              );
            })}
          </div>
        </FieldShell>
      );
    }

    case 'select':
      return (
        <FieldShell champ={champ} manquant={manquant}>
          <SelectInput champ={champ as ChoiceField} valeur={(valeur as string) ?? ''} onChange={set} />
        </FieldShell>
      );

    case 'multiselect':
      return (
        <FieldShell champ={champ} manquant={manquant}>
          <MultiSelectInput
            champ={champ as ChoiceField}
            valeurs={(valeur as string[]) ?? []}
            onChange={set}
          />
        </FieldShell>
      );

    case 'media':
      return (
        <FieldShell champ={champ} manquant={manquant}>
          <MediaInput
            medias={(valeur as Media[]) ?? []}
            onChange={set}
            video={champ.video}
            maxSeconds={champ.maxSeconds}
            multiple={champ.multiple ?? true}
          />
        </FieldShell>
      );

    case 'signature':
      return (
        <FieldShell champ={champ} manquant={manquant}>
          <SignaturePad value={valeur as string | undefined} onChange={set} />
        </FieldShell>
      );
  }
}

/* ── Sous-composants ───────────────────────────────────────────────────── */

function GeolocInput({
  id,
  valeur,
  onChange,
}: {
  id: string;
  valeur: string;
  onChange: (v: string) => void;
}) {
  const [etat, setEtat] = useState<'repos' | 'recherche' | 'refus'>('repos');

  const localiser = () => {
    if (!navigator.geolocation) {
      setEtat('refus');
      return;
    }
    setEtat('recherche');
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const { latitude, longitude } = pos.coords;
        const gps = `${latitude.toFixed(5)}, ${longitude.toFixed(5)}`;
        onChange(valeur.trim() ? `${valeur.trim()} (GPS ${gps})` : `GPS ${gps}`);
        setEtat('repos');
      },
      () => setEtat('refus'),
      { enableHighAccuracy: true, timeout: 10_000 },
    );
  };

  return (
    <div>
      <input
        id={id}
        type="text"
        className="di-input"
        placeholder="Adresse ou description du site"
        value={valeur}
        onChange={(e) => onChange(e.target.value)}
      />
      <button
        type="button"
        className="di-btn-ghost mt-2 w-full !py-2 !text-xs"
        onClick={localiser}
        disabled={etat === 'recherche'}
      >
        {etat === 'recherche' ? 'Localisation…' : 'Relever la position GPS'}
      </button>
      {etat === 'refus' && (
        <p className="mt-1 text-[12px] text-muted">
          Position indisponible — saisir le lieu manuellement.
        </p>
      )}
    </div>
  );
}

function SelectInput({
  champ,
  valeur,
  onChange,
}: {
  champ: ChoiceField;
  valeur: string;
  onChange: (v: string) => void;
}) {
  const connu = champ.options.some((o: Option) => o.value === valeur);
  const modeAutre = champ.allowOther && valeur !== '' && !connu;

  return (
    <div className="space-y-2">
      <select
        id={champ.id}
        className="di-input"
        value={modeAutre ? AUTRE : valeur}
        onChange={(e) => onChange(e.target.value === AUTRE ? ' ' : e.target.value)}
      >
        <option value="">— Choisir —</option>
        {champ.options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
        {champ.allowOther && <option value={AUTRE}>Autre…</option>}
      </select>
      {modeAutre && (
        <input
          type="text"
          className="di-input"
          placeholder="Préciser"
          autoFocus
          value={valeur.trim()}
          onChange={(e) => onChange(e.target.value === '' ? ' ' : e.target.value)}
        />
      )}
    </div>
  );
}

function MultiSelectInput({
  champ,
  valeurs,
  onChange,
}: {
  champ: ChoiceField;
  valeurs: string[];
  onChange: (v: string[]) => void;
}) {
  const [autre, setAutre] = useState('');
  const connus = new Set(champ.options.map((o) => o.value));
  const libres = valeurs.filter((v) => !connus.has(v));

  const bascule = (v: string) =>
    onChange(valeurs.includes(v) ? valeurs.filter((x) => x !== v) : [...valeurs, v]);

  const ajouterAutre = () => {
    const v = autre.trim();
    if (v && !valeurs.includes(v)) onChange([...valeurs, v]);
    setAutre('');
  };

  return (
    <div className="space-y-2">
      {champ.options.map((o) => {
        const actif = valeurs.includes(o.value);
        return (
          <button
            key={o.value}
            type="button"
            aria-pressed={actif}
            className={`di-btn w-full !justify-start text-left !normal-case ${
              actif ? 'border-di bg-di text-white' : 'border-line bg-paper text-muted'
            }`}
            onClick={() => bascule(o.value)}
          >
            <span className="mr-2 font-mono">{actif ? '■' : '□'}</span>
            {o.label}
          </button>
        );
      })}

      {libres.map((v) => (
        <button
          key={v}
          type="button"
          className="di-btn w-full !justify-start border-di bg-di text-left !normal-case text-white"
          onClick={() => bascule(v)}
        >
          <span className="mr-2 font-mono">■</span>
          {v}
        </button>
      ))}

      {champ.allowOther && (
        <div className="flex gap-2">
          <input
            type="text"
            className="di-input"
            placeholder="Autre processus…"
            value={autre}
            onChange={(e) => setAutre(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault();
                ajouterAutre();
              }
            }}
          />
          <button type="button" className="di-btn-ghost shrink-0" onClick={ajouterAutre}>
            Ajouter
          </button>
        </div>
      )}
    </div>
  );
}
