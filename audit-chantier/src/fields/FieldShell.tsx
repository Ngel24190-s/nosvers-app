import type { ReactNode } from 'react';
import type { Field } from '../schema/types';

/** Habillage commun : libellé, astérisque d'obligation, aide, message d'alerte. */
export function FieldShell({
  champ,
  children,
  alerte,
  manquant,
}: {
  champ: Field;
  children: ReactNode;
  alerte?: string | null;
  manquant?: boolean;
}) {
  return (
    <div
      id={`champ-${champ.id}`}
      className={`border-l-4 py-4 pl-3 ${
        manquant ? 'border-di bg-di-light/40' : 'border-transparent'
      }`}
    >
      <label htmlFor={champ.id} className="di-label">
        {champ.label}
        {champ.required && <span className="ml-1 text-di">*</span>}
      </label>
      {champ.hint && <p className="mt-1 text-[13px] leading-snug text-muted">{champ.hint}</p>}
      <div className="mt-2">{children}</div>
      {alerte && (
        <p
          role="alert"
          className="mt-2 border-2 border-di bg-di-light px-3 py-2 text-[13px] font-bold uppercase tracking-di text-di-dark"
        >
          {alerte}
        </p>
      )}
    </div>
  );
}
