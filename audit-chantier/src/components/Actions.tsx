import { useRef, useState } from 'react';
import type { AuditData } from '../schema/types';
import type { Anomalie } from '../lib/validation';
import { construirePdf } from '../report/buildPdf';
import { envoyerRapport, telechargerRapport } from '../report/share';
import { nomFichier } from '../report/format';
import { EMAIL_QSE } from '../config';
import { exporterBrouillon, importerBrouillon } from '../storage/storage';

/** Bloc de clôture : contrôles bloquants, envoi du rapport, brouillon. */
export function Actions({
  data,
  anomalies,
  onAller,
  onImport,
  onReinit,
}: {
  data: AuditData;
  anomalies: Anomalie[];
  onAller: (champId: string) => void;
  onImport: (d: AuditData) => void;
  onReinit: () => void;
}) {
  const [etat, setEtat] = useState<'repos' | 'generation'>('repos');
  const [message, setMessage] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const bloquants = anomalies.filter((x) => x.niveau === 'bloquant');
  const alertes = anomalies.filter((x) => x.niveau === 'alerte');

  const generer = async (envoyer: boolean) => {
    setEtat('generation');
    setMessage(null);
    try {
      const blob = await construirePdf(data);
      if (!envoyer) {
        telechargerRapport(blob, data);
        setMessage('Rapport téléchargé.');
      } else {
        const resultat = await envoyerRapport(blob, data);
        if (resultat === 'partage') setMessage('Rapport transmis.');
        else if (resultat === 'annule') setMessage('Envoi annulé.');
        else
          setMessage(
            `Rapport téléchargé et message préparé pour ${EMAIL_QSE} — joindre le PDF avant d'envoyer.`,
          );
      }
    } catch (e) {
      setMessage(`Échec de la génération : ${e instanceof Error ? e.message : 'erreur inconnue'}`);
    } finally {
      setEtat('repos');
    }
  };

  const importer = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const fichier = e.target.files?.[0];
    if (!fichier) return;
    try {
      onImport(await importerBrouillon(fichier));
      setMessage('Brouillon importé.');
    } catch {
      setMessage('Fichier illisible.');
    } finally {
      if (fileRef.current) fileRef.current.value = '';
    }
  };

  return (
    <div className="no-print mt-8 space-y-4 border-t-4 border-ink pt-6">
      {bloquants.length > 0 && (
        <div className="border-2 border-di bg-di-light p-3">
          <p className="text-[13px] font-bold uppercase tracking-di text-di-dark">
            {bloquants.length} point{bloquants.length > 1 ? 's' : ''} à traiter avant clôture
          </p>
          <ul className="mt-2 space-y-1">
            {bloquants.map((x) => (
              <li key={`${x.champId}-${x.message}`}>
                <button
                  type="button"
                  className="text-left text-[13px] underline decoration-di underline-offset-2"
                  onClick={() => onAller(x.champId)}
                >
                  <strong>{x.champLabel}</strong> — {x.message}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {alertes.length > 0 && (
        <div className="border-2 border-line p-3">
          <p className="text-[13px] font-bold uppercase tracking-di">
            Rappels ({alertes.length}) — non bloquants
          </p>
          <ul className="mt-2 space-y-1">
            {alertes.map((x) => (
              <li key={`${x.champId}-${x.message}`}>
                <button
                  type="button"
                  className="text-left text-[13px] text-muted underline underline-offset-2"
                  onClick={() => onAller(x.champId)}
                >
                  {x.champLabel} — {x.message}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      <button
        type="button"
        className="di-btn-primary w-full !py-4"
        disabled={bloquants.length > 0 || etat === 'generation'}
        onClick={() => generer(true)}
      >
        {etat === 'generation' ? 'Génération…' : 'Générer et envoyer le rapport'}
      </button>

      <button
        type="button"
        className="di-btn-ghost w-full"
        disabled={bloquants.length > 0 || etat === 'generation'}
        onClick={() => generer(false)}
      >
        Télécharger le PDF seulement
      </button>

      {message && (
        <p role="status" className="border-2 border-ink px-3 py-2 text-[13px]">
          {message}
        </p>
      )}

      <div className="grid grid-cols-2 gap-2 pt-2">
        <button
          type="button"
          className="di-btn-ghost !py-2 !text-xs"
          onClick={() => exporterBrouillon(data, nomFichier(data))}
        >
          Exporter le brouillon
        </button>
        <button
          type="button"
          className="di-btn-ghost !py-2 !text-xs"
          onClick={() => fileRef.current?.click()}
        >
          Importer un brouillon
        </button>
      </div>
      <input
        ref={fileRef}
        type="file"
        accept="application/json,.json"
        className="hidden"
        onChange={importer}
      />

      <button
        type="button"
        className="w-full py-2 text-[12px] uppercase tracking-di text-muted underline"
        onClick={() => {
          if (window.confirm("Effacer cet audit et en commencer un nouveau ?")) onReinit();
        }}
      >
        Nouvel audit
      </button>
    </div>
  );
}
