/* ============================================================================
   TRANSMISSION DU RAPPORT
   ----------------------------------------------------------------------------
   Sur téléphone, `navigator.share` ouvre Gmail / WhatsApp avec le PDF déjà
   joint : c'est le seul chemin réellement utilisable sur un chantier.
   Partout ailleurs, on télécharge le PDF et on prépare l'e-mail (le PDF doit
   alors être joint à la main — aucun navigateur ne permet de le faire seul).
   ========================================================================== */

import { AGENCE, EMAIL_CC, EMAIL_QSE, ENTITE } from '../config';
import type { AuditData } from '../schema/types';
import { bilan, nonConformites } from '../lib/validation';
import { formaterDate, formaterJour, nomFichier } from './format';

export type ResultatEnvoi = 'partage' | 'telecharge' | 'annule';

export function objetEmail(a: AuditData): string {
  const chantier = String(a.chantier ?? 'Chantier').trim() || 'Chantier';
  const d = new Date(String(a.date_audit ?? Date.now()));
  const jour = Number.isNaN(d.getTime()) ? '' : ` — ${d.toLocaleDateString('fr-FR')}`;
  return `Audit chantier QSE — ${chantier}${jour}`;
}

export function corpsEmail(a: AuditData): string {
  const b = bilan(a);
  const nc = nonConformites(a);

  const lignes = [
    `Audit chantier QSE — ${ENTITE} ${AGENCE}`,
    '',
    `Chantier    : ${String(a.chantier ?? '—')}`,
    `Lieu        : ${String(a.lieu ?? '—')}`,
    `Date        : ${formaterDate(a.date_audit as string)}`,
    `Auditeur    : ${String(a.auditeur ?? '—').trim() || '—'}`,
    `Responsable : ${String(a.conducteur ?? '—').trim() || '—'}`,
    '',
    `Bilan : ${b.C} conforme(s) · ${b.A} améliorable(s) · ${b.NA} non applicable(s)`,
  ];

  if (Array.isArray(a.processus_amiante) && a.processus_amiante.length > 0) {
    lignes.push(`Processus amiante : ${(a.processus_amiante as string[]).join(', ')}`);
    if (a.vitesse_air_sas !== undefined) {
      lignes.push(`Vitesse d'air SAS : ${a.vitesse_air_sas} m/s`);
    }
    if (a.depression_zone !== undefined) {
      lignes.push(`Dépression zone   : ${a.depression_zone} Pa`);
    }
  }

  if (nc.length > 0) {
    lignes.push('', `POINTS À AMÉLIORER (${nc.length}) :`);
    nc.forEach((x, i) => {
      lignes.push(
        `${i + 1}. ${x.label} — ${x.commentaire}` +
          ` [resp. ${x.responsable}${x.delai === '—' ? '' : `, délai ${formaterJour(x.delai)}`}]`,
      );
    });
  } else {
    lignes.push('', 'Aucun point à améliorer relevé.');
  }

  const commentaires = String(a.commentaires_globaux ?? '').trim();
  if (commentaires) lignes.push('', 'Commentaires globaux :', commentaires);

  lignes.push('', 'Rapport complet en pièce jointe (PDF).');
  return lignes.join('\n');
}

function ouvrirMail(a: AuditData) {
  const params = new URLSearchParams({ subject: objetEmail(a), body: corpsEmail(a) });
  if (EMAIL_CC) params.set('cc', EMAIL_CC);
  window.location.href = `mailto:${EMAIL_QSE}?${params.toString().replace(/\+/g, '%20')}`;
}

function telecharger(blob: Blob, nom: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = nom;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 10_000);
}

export async function envoyerRapport(blob: Blob, a: AuditData): Promise<ResultatEnvoi> {
  const nom = `${nomFichier(a)}.pdf`;
  const fichier = new File([blob], nom, { type: 'application/pdf' });

  if (navigator.canShare?.({ files: [fichier] })) {
    try {
      await navigator.share({
        files: [fichier],
        title: objetEmail(a),
        text: corpsEmail(a),
      });
      return 'partage';
    } catch (e) {
      // L'utilisateur a fermé la feuille de partage : ne pas enchaîner sur un
      // téléchargement qu'il n'a pas demandé.
      if (e instanceof DOMException && e.name === 'AbortError') return 'annule';
    }
  }

  telecharger(blob, nom);
  ouvrirMail(a);
  return 'telecharge';
}

/** Téléchargement seul, sans ouvrir la messagerie. */
export function telechargerRapport(blob: Blob, a: AuditData): void {
  telecharger(blob, `${nomFichier(a)}.pdf`);
}
