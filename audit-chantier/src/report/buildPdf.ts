/* ============================================================================
   RAPPORT PDF — grille DIER-QSE
   ----------------------------------------------------------------------------
   Le rapport est entièrement dérivé du schéma : tout champ ajouté dans
   `audit-schema.ts` apparaît automatiquement dans le PDF, au bon écran.
   ========================================================================== */

import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';

import { AGENCE, ENTITE, VERSION } from '../config';
import { SCREENS } from '../schema/audit-schema';
import type { AuditData, ControlValue, Media, Screen } from '../schema/types';
import { bilan, champsVisibles, ecransVisibles, estControl, nonConformites } from '../lib/validation';
import { formaterDate, formaterJour, valeurTexte } from './format';

const ROUGE: [number, number, number] = [214, 40, 40];
const NOIR: [number, number, number] = [0, 0, 0];
const VERT: [number, number, number] = [26, 127, 55];
const GRIS: [number, number, number] = [107, 107, 107];
const GRIS_CLAIR: [number, number, number] = [242, 242, 242];

const MARGE = 12;

const LIBELLE_EVAL: Record<string, string> = {
  C: 'C',
  A: 'AMÉLIORABLE',
  NA: 'NA',
};

/** jsPDF a besoin du format exact ; le déduire évite qu'un PNG transparent
 *  soit stocké en bitmap brut et fasse exploser le poids du rapport. */
const formatImage = (dataUrl: string): 'PNG' | 'JPEG' =>
  dataUrl.startsWith('data:image/png') ? 'PNG' : 'JPEG';

const couleurEval = (e?: string): [number, number, number] =>
  e === 'C' ? VERT : e === 'A' ? ROUGE : GRIS;

/** Dimensions réelles d'une image encodée en base64. */
function taillesImage(dataUrl: string): Promise<{ w: number; h: number }> {
  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () => resolve({ w: img.naturalWidth, h: img.naturalHeight });
    img.onerror = () => resolve({ w: 4, h: 3 });
    img.src = dataUrl;
  });
}

/** Toutes les photos de l'audit, avec le point de contrôle d'origine. */
function photosAudit(a: AuditData): { legende: string; media: Media }[] {
  const sortie: { legende: string; media: Media }[] = [];
  for (const ecran of ecransVisibles(a)) {
    for (const champ of champsVisibles(ecran, a)) {
      if (champ.type === 'control') {
        const v = a[champ.id];
        if (estControl(v)) {
          for (const m of v.medias ?? []) sortie.push({ legende: champ.label, media: m });
        }
      } else if (champ.type === 'media') {
        for (const m of (a[champ.id] as Media[]) ?? []) {
          sortie.push({ legende: champ.label, media: m });
        }
      }
    }
  }
  return sortie;
}

/** Position verticale disponible après le dernier tableau dessiné. */
const apres = (doc: jsPDF): number =>
  // `lastAutoTable` est renseigné par jspdf-autotable après chaque appel.
  ((doc as unknown as { lastAutoTable?: { finalY: number } }).lastAutoTable?.finalY ?? MARGE) + 8;

function titreSection(doc: jsPDF, texte: string, y: number): number {
  const largeur = doc.internal.pageSize.getWidth();
  if (y > doc.internal.pageSize.getHeight() - 30) {
    doc.addPage();
    y = MARGE;
  }
  doc.setFillColor(...NOIR);
  doc.rect(MARGE, y, largeur - MARGE * 2, 7, 'F');
  doc.setTextColor(255, 255, 255);
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(9);
  doc.text(texte.toUpperCase(), MARGE + 2, y + 4.8);
  doc.setTextColor(...NOIR);
  return y + 11;
}

function enTete(doc: jsPDF, a: AuditData) {
  const largeur = doc.internal.pageSize.getWidth();
  doc.setFillColor(...ROUGE);
  doc.rect(0, 0, largeur, 24, 'F');
  doc.setTextColor(255, 255, 255);
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(15);
  doc.text('AUDIT CHANTIER QSE', MARGE, 11);
  doc.setFontSize(8);
  doc.setFont('helvetica', 'normal');
  doc.text(`${ENTITE} — ${AGENCE}`, MARGE, 17.5);
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(9);
  doc.text(formaterDate(a.date_audit as string), largeur - MARGE, 11, { align: 'right' });
  doc.setFont('helvetica', 'normal');
  doc.setFontSize(8);
  doc.text(String(a.chantier ?? '').slice(0, 60), largeur - MARGE, 17.5, { align: 'right' });
  doc.setTextColor(...NOIR);
}

function piedsDePage(doc: jsPDF) {
  const pages = doc.getNumberOfPages();
  const largeur = doc.internal.pageSize.getWidth();
  const hauteur = doc.internal.pageSize.getHeight();
  for (let i = 1; i <= pages; i += 1) {
    doc.setPage(i);
    doc.setDrawColor(...GRIS);
    doc.setLineWidth(0.2);
    doc.line(MARGE, hauteur - 10, largeur - MARGE, hauteur - 10);
    doc.setFontSize(7);
    doc.setTextColor(...GRIS);
    doc.text(`${ENTITE} — Audit chantier QSE — v${VERSION}`, MARGE, hauteur - 6);
    doc.text(`Page ${i} / ${pages}`, largeur - MARGE, hauteur - 6, { align: 'right' });
  }
  doc.setTextColor(...NOIR);
}

/** Tableau des points de contrôle d'un écran. */
function tableauEcran(doc: jsPDF, ecran: Screen, a: AuditData, y: number): number {
  const controles = champsVisibles(ecran, a).filter((c) => c.type === 'control');
  const autres = champsVisibles(ecran, a).filter(
    (c) => c.type !== 'control' && c.type !== 'signature',
  );

  let curseur = y;

  if (autres.length > 0) {
    autoTable(doc, {
      startY: curseur,
      margin: { left: MARGE, right: MARGE },
      theme: 'grid',
      styles: { fontSize: 8, cellPadding: 1.8, lineColor: [200, 200, 200], lineWidth: 0.1 },
      columnStyles: {
        0: { cellWidth: 62, fontStyle: 'bold' },
        1: { cellWidth: 'auto' },
      },
      body: autres.map((c) => [c.label, valeurTexte(c, a)]),
    });
    curseur = apres(doc);
  }

  if (controles.length > 0) {
    autoTable(doc, {
      startY: curseur,
      margin: { left: MARGE, right: MARGE },
      theme: 'grid',
      headStyles: { fillColor: GRIS_CLAIR, textColor: NOIR, fontSize: 7.5, lineWidth: 0.1 },
      styles: { fontSize: 8, cellPadding: 1.8, lineColor: [200, 200, 200], lineWidth: 0.1 },
      columnStyles: {
        0: { cellWidth: 64 },
        1: { cellWidth: 24, halign: 'center', fontStyle: 'bold' },
        2: { cellWidth: 'auto' },
        3: { cellWidth: 26 },
        4: { cellWidth: 20, halign: 'center' },
      },
      head: [['Point de contrôle', 'Évaluation', 'Commentaire', 'Responsable', 'Délai']],
      body: controles.map((c) => {
        const v = (estControl(a[c.id]) ? (a[c.id] as ControlValue) : {}) as ControlValue;
        const photos = (v.medias ?? []).length;
        return [
          c.label + (photos ? `\n(${photos} photo${photos > 1 ? 's' : ''})` : ''),
          v.evaluation ? LIBELLE_EVAL[v.evaluation] : 'Non évalué',
          v.commentaire?.trim() || '—',
          v.responsable?.trim() || '—',
          v.delai ? formaterJour(v.delai) : '—',
        ];
      }),
      didParseCell: (donnees) => {
        if (donnees.section === 'body' && donnees.column.index === 1) {
          const controle = controles[donnees.row.index];
          const v = a[controle.id];
          const evaluation = estControl(v) ? (v as ControlValue).evaluation : undefined;
          donnees.cell.styles.textColor = evaluation ? couleurEval(evaluation) : GRIS;
        }
      },
    });
    curseur = apres(doc);
  }

  return curseur;
}

/** Construit le rapport et le renvoie sous forme de Blob. */
export async function construirePdf(a: AuditData): Promise<Blob> {
  const doc = new jsPDF({ unit: 'mm', format: 'a4' });
  const largeur = doc.internal.pageSize.getWidth();
  const utile = largeur - MARGE * 2;

  enTete(doc, a);
  let y = 32;

  /* ── Synthèse ─────────────────────────────────────────────────────── */
  const b = bilan(a);
  const nc = nonConformites(a);

  y = titreSection(doc, 'Synthèse de la visite', y);
  autoTable(doc, {
    startY: y,
    margin: { left: MARGE, right: MARGE },
    theme: 'grid',
    styles: { fontSize: 9, cellPadding: 2.5, halign: 'center', lineWidth: 0.1 },
    body: [
      [
        { content: `${b.C}\nConformes`, styles: { textColor: VERT, fontStyle: 'bold' } },
        { content: `${b.A}\nAméliorables`, styles: { textColor: ROUGE, fontStyle: 'bold' } },
        { content: `${b.NA}\nNon applicables`, styles: { textColor: GRIS } },
        { content: `${b.evalues}\nPoints évalués`, styles: { fontStyle: 'bold' } },
      ],
    ],
  });
  y = apres(doc);

  if (nc.length > 0) {
    y = titreSection(doc, `Points à améliorer — actions requises (${nc.length})`, y);
    autoTable(doc, {
      startY: y,
      margin: { left: MARGE, right: MARGE },
      theme: 'grid',
      headStyles: { fillColor: ROUGE, textColor: [255, 255, 255], fontSize: 7.5 },
      styles: { fontSize: 8, cellPadding: 1.8, lineWidth: 0.1 },
      columnStyles: {
        0: { cellWidth: 30 },
        1: { cellWidth: 52 },
        2: { cellWidth: 'auto' },
        3: { cellWidth: 26 },
        4: { cellWidth: 20, halign: 'center' },
      },
      head: [['Rubrique', 'Point de contrôle', 'Constat / action', 'Responsable', 'Délai']],
      body: nc.map((x) => [
        x.ref ? `${x.ecran} (${x.ref})` : x.ecran,
        x.label,
        x.commentaire,
        x.responsable,
        x.delai === '—' ? '—' : formaterJour(x.delai),
      ]),
    });
    y = apres(doc);
  }

  /* ── Un bloc par écran ────────────────────────────────────────────── */
  for (const ecran of ecransVisibles(a)) {
    if (ecran.id === 'cloture') continue;
    y = titreSection(doc, ecran.ref ? `${ecran.title} (${ecran.ref})` : ecran.title, y);
    y = tableauEcran(doc, ecran, a, y);
  }

  /* ── Clôture ──────────────────────────────────────────────────────── */
  const cloture = SCREENS.find((e) => e.id === 'cloture');
  if (cloture) {
    y = titreSection(doc, 'Clôture', y);
    autoTable(doc, {
      startY: y,
      margin: { left: MARGE, right: MARGE },
      theme: 'grid',
      styles: { fontSize: 8, cellPadding: 2, lineWidth: 0.1 },
      columnStyles: { 0: { cellWidth: 52, fontStyle: 'bold' }, 1: { cellWidth: 'auto' } },
      body: [
        ['Commentaires globaux', String(a.commentaires_globaux ?? '').trim() || '—'],
        ['Actions correctives immédiates', String(a.actions_immediates ?? '').trim() || '—'],
      ],
    });
    y = apres(doc);
  }

  /* ── Signatures ───────────────────────────────────────────────────── */
  const signatures: { titre: string; nom: string; data?: string }[] = [
    {
      titre: 'Auditeur',
      nom: String(a.auditeur ?? '').trim() || '—',
      data: a.signature_auditeur as string | undefined,
    },
    {
      titre: 'Chef de chantier / Responsable',
      nom: String(a.conducteur ?? '').trim() || '—',
      data: a.signature_responsable as string | undefined,
    },
  ];

  if (y > doc.internal.pageSize.getHeight() - 60) {
    doc.addPage();
    y = MARGE;
  }
  y = titreSection(doc, 'Signatures', y);
  const largeurSignature = (utile - 6) / 2;
  signatures.forEach((s, i) => {
    const x = MARGE + i * (largeurSignature + 6);
    doc.setDrawColor(...GRIS);
    doc.setLineWidth(0.2);
    doc.rect(x, y, largeurSignature, 34);
    doc.setFontSize(7.5);
    doc.setFont('helvetica', 'bold');
    doc.text(s.titre.toUpperCase(), x + 2, y + 5);
    doc.setFont('helvetica', 'normal');
    doc.text(s.nom, x + 2, y + 9.5);
    if (s.data) {
      try {
        doc.addImage(s.data, formatImage(s.data), x + 2, y + 12, largeurSignature - 4, 20);
      } catch {
        /* signature illisible : le cadre reste vide */
      }
    } else {
      doc.setTextColor(...GRIS);
      doc.text('Non signé', x + 2, y + 22);
      doc.setTextColor(...NOIR);
    }
  });
  y += 42;

  /* ── Annexe photos ────────────────────────────────────────────────── */
  const photos = photosAudit(a).filter((p) => p.media.kind === 'image');
  if (photos.length > 0) {
    doc.addPage();
    y = titreSection(doc, `Annexe photographique (${photos.length})`, MARGE);

    const colonnes = 2;
    const largeurCase = (utile - 6) / colonnes;
    let colonne = 0;
    let hauteurLigne = 0;

    for (const p of photos) {
      const { w, h } = await taillesImage(p.media.dataUrl);
      const hauteurImage = Math.min((largeurCase * h) / w, 65);
      const hauteurCase = hauteurImage + 8;

      if (colonne === 0 && y + hauteurCase > doc.internal.pageSize.getHeight() - 16) {
        doc.addPage();
        y = MARGE;
      }

      const x = MARGE + colonne * (largeurCase + 6);
      try {
        doc.addImage(
          p.media.dataUrl,
          formatImage(p.media.dataUrl),
          x,
          y,
          largeurCase,
          hauteurImage,
        );
      } catch {
        /* image illisible : on saute la vignette */
      }
      doc.setFontSize(7);
      doc.setTextColor(...GRIS);
      doc.text(doc.splitTextToSize(p.legende, largeurCase)[0] ?? '', x, y + hauteurImage + 4);
      doc.setTextColor(...NOIR);

      hauteurLigne = Math.max(hauteurLigne, hauteurCase);
      colonne += 1;
      if (colonne === colonnes) {
        colonne = 0;
        y += hauteurLigne + 4;
        hauteurLigne = 0;
      }
    }
  }

  /* Les vidéos ne peuvent pas être intégrées à un PDF : on les signale. */
  const videos = photosAudit(a).filter((p) => p.media.kind === 'video');
  if (videos.length > 0) {
    doc.setFontSize(8);
    doc.setTextColor(...ROUGE);
    doc.text(
      `${videos.length} vidéo(s) enregistrée(s) dans l'application — à transmettre séparément.`,
      MARGE,
      Math.min(y + 8, doc.internal.pageSize.getHeight() - 16),
    );
    doc.setTextColor(...NOIR);
  }

  piedsDePage(doc);
  return doc.output('blob');
}
