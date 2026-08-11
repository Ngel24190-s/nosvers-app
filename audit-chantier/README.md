# Audit Chantier QSE — D.I. Environnement

Application d'audit de chantier (type Kizeo Forms) construite d'après le cahier des charges
*Maquette · Application d'Audit Chantier QSE V2*. Elle fusionne la grille d'inspection
Environnement / Logistique (ELV) et les audits amiante spécifiques (processus 18-14-M1,
bilan aéraulique NF X 46-010).

**Le livrable est un fichier unique : [`build/Audit-Chantier-QSE.html`](build/Audit-Chantier-QSE.html).**
Un seul fichier, aucune installation, aucun compte, fonctionne hors connexion.

---

## Pour l'utiliser sur le terrain

1. Télécharger `build/Audit-Chantier-QSE.html` et l'envoyer aux auditeurs (WhatsApp, e-mail…).
2. Sur le téléphone : ouvrir le fichier — il s'ouvre dans le navigateur.
3. Remplir les 7 écrans. Le brouillon est enregistré automatiquement à chaque saisie.
4. Écran **Clôture** → **Générer et envoyer le rapport**.
   - Sur téléphone, la feuille de partage s'ouvre avec le **PDF déjà joint** (Gmail, WhatsApp…).
   - Sur ordinateur, le PDF est téléchargé et le message est préparé pour le service QSE —
     il reste à joindre le PDF téléchargé.

### Points de vigilance

- **Aucune donnée ne quitte le téléphone** tant que l'auditeur n'envoie pas le rapport.
- Si le navigateur refuse l'enregistrement local (cas possible sur iPhone en `file://`), un
  bandeau **« Mode sans sauvegarde »** s'affiche : l'audit doit alors être terminé en une
  fois, ou exporté en JSON depuis l'écran Clôture.
- Les vidéos (test de fumée) restent dans l'application : un PDF ne peut pas les contenir.
  Le rapport le signale, elles sont à transmettre séparément.

### Variante hébergée (optionnelle)

Le même fichier peut être déposé sur le serveur et servi en HTTPS (par ex.
`public_html/audit/index.html`). Dans ce cas l'enregistrement local, le GPS et le partage
natif fonctionnent sans aucune restriction, et une mise à jour se propage à tout le monde
sans avoir à renvoyer le fichier.

---

## Les 7 écrans

| # | Écran | Réf. grille | Contenu |
|---|---|---|---|
| 1 | Informations générales | — | Chantier, lieu + GPS, auditeur, conducteur, arrêt de travail, processus amiante |
| 2 | Situation générale, procédures et organisation | A & B | 9 points de contrôle |
| 3 | Hygiène, santé et base vie | C | 4 points (dont propreté des SAS, amiante) |
| 4 | Identification des risques | D | 8 points |
| 5 | Environnement de travail et véhicules | F & G | 6 points + immatriculation |
| 6 | Confinement et bilan aéraulique | NF X 46-010 | **Amiante uniquement** — vitesse d'air, dépression, test de fumée |
| 7 | Clôture | — | Commentaires, actions immédiates, 2 signatures tactiles |

**Rendu conditionnel :** l'écran 6, le niveau d'empoussièrement et la propreté des SAS
n'apparaissent que si un processus amiante est sélectionné à l'écran 1.

**Règles métier bloquantes :** vitesse d'air SAS < 0,5 m/s et dépression < 10 Pa déclenchent
une alerte rouge qui empêche la clôture de l'audit tant qu'elle n'est pas traitée.

---

## Modifier le formulaire

Tout le formulaire est décrit dans **`src/schema/audit-schema.ts`**. Aucun composant à
toucher : le moteur de rendu, la progression, la validation et le PDF suivent automatiquement.

### Ajouter un point de contrôle (C / Améliorable / NA)

```ts
// dans l'écran voulu, tableau `fields`
ctrl('extincteurs', 'Extincteurs accessibles et vérifiés', 'Contrôle annuel à jour.'),
```

Avec photo attendue :

```ts
ctrl('extincteurs', 'Extincteurs', 'Photo de l’étiquette de contrôle.', { photoRequise: true }),
```

### Ajouter un champ classique

```ts
{ id: 'meteo', type: 'text', label: 'Conditions météo' },
{ id: 'temperature', type: 'number', unit: '°C', label: 'Température relevée' },
```

Types disponibles : `text` · `textarea` · `datetime` · `number` · `checkbox` · `radio` ·
`select` · `multiselect` · `media` · `geoloc` · `signature` · `control`.

### Rendre un champ conditionnel

```ts
{ id: 'detail_incident', type: 'textarea', label: 'Détail de l’incident',
  visibleIf: (a) => a.incident === 'OUI' },
```

`estAmiante` est déjà fourni pour les champs spécifiques désamiantage :

```ts
visibleIf: estAmiante,
```

### Ajouter une règle d'alerte bloquante

```ts
{ id: 'ph_eau', type: 'number', unit: 'pH', label: 'pH de l’eau de rinçage', required: true,
  alert: (v) => (v < 6 || v > 9 ? 'ALERTE — pH hors tolérance.' : null) },
```

### Ajouter un écran

Copier un bloc complet dans `SCREENS` :

```ts
{
  id: 'mon_ecran',
  short: 'Mon écran',          // libellé court dans la barre de navigation
  title: 'Titre complet',
  ref: 'H',                    // facultatif — référence de la grille DIER-QSE
  intro: 'Phrase d’introduction.',
  fields: [ /* … */ ],
}
```

### Mettre à jour les listes de personnes

`src/schema/options.ts` — auditeurs, conducteurs de travaux, processus amiante.
Une ligne par entrée. Les listes acceptent aussi une saisie libre « Autre… ».

### Changer les couleurs

`src/theme/tokens.css` — c'est le seul endroit où la charte est définie.
Valeurs actuelles : rouge `#D62828`, rouge foncé `#A91D1D`, noir, blanc.

### Changer le destinataire du rapport

`src/config.ts` → `EMAIL_QSE` (et `EMAIL_CC`). Y figurent aussi le nom de l'agence,
la version affichée et les réglages de compression des photos.

> ⚠️ Ne jamais changer l'`id` d'un champ déjà diffusé : c'est la clé de sauvegarde des
> brouillons en cours sur les téléphones.

---

## Reconstruire le fichier

```bash
cd audit-chantier
npm install
npm run build                       # produit dist/index.html (un seul fichier)
cp dist/index.html build/Audit-Chantier-QSE.html
```

Autres commandes : `npm run dev` (serveur local, port 5180), `npm run typecheck`.

Après une modification visible par les utilisateurs, incrémenter `VERSION` dans
`src/config.ts` — le numéro s'affiche en pied de page et dans le PDF, ce qui permet de
savoir qui utilise encore une ancienne version du fichier.

---

## Architecture

```
src/
├── schema/
│   ├── audit-schema.ts   ★ les 7 écrans et tous les champs
│   ├── options.ts        ★ listes déroulantes
│   └── types.ts            contrat des champs
├── fields/                 un composant par type de champ
│   ├── FieldRenderer.tsx   aiguillage unique sur field.type
│   ├── ControlPoint.tsx    le bloc C / Améliorable / NA
│   ├── SignaturePad.tsx    signature tactile (canvas natif)
│   └── MediaInput.tsx      photos, avec compression
├── lib/validation.ts       visibilité, complétude, alertes, non-conformités
├── report/                 génération PDF (jsPDF) et envoi
├── storage/                brouillon local + détection de stockage
├── theme/tokens.css      ★ charte D.I. Environnement
└── config.ts             ★ destinataire QSE, version, réglages
```

Stack : Vite 5 · React 18 · TypeScript · Tailwind 3 · jsPDF —
`vite-plugin-singlefile` inline tout dans un `index.html` unique (~950 Ko).
