import { useRef, useState } from 'react';
import { fichierVersMedia } from '../storage/media';
import type { Media } from '../schema/types';

/** Prise de photo (ou vidéo courte) depuis le téléphone, avec compression. */
export function MediaInput({
  medias,
  onChange,
  video = false,
  maxSeconds,
  multiple = true,
  compact = false,
}: {
  medias: Media[];
  onChange: (m: Media[]) => void;
  video?: boolean;
  maxSeconds?: number;
  multiple?: boolean;
  compact?: boolean;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [occupe, setOccupe] = useState(false);

  const ajouter = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const fichiers = Array.from(e.target.files ?? []);
    if (fichiers.length === 0) return;
    setOccupe(true);
    try {
      const nouveaux = await Promise.all(fichiers.map(fichierVersMedia));
      onChange(multiple ? [...medias, ...nouveaux] : nouveaux.slice(0, 1));
    } finally {
      setOccupe(false);
      // Permet de reprendre deux fois la même photo à la suite.
      if (inputRef.current) inputRef.current.value = '';
    }
  };

  const retirer = (id: string) => onChange(medias.filter((m) => m.id !== id));

  return (
    <div>
      <input
        ref={inputRef}
        type="file"
        accept={video ? 'image/*,video/*' : 'image/*'}
        capture="environment"
        multiple={multiple}
        className="hidden"
        onChange={ajouter}
      />
      <button
        type="button"
        className={`di-btn-ghost w-full ${compact ? '!py-2 !text-xs' : ''}`}
        disabled={occupe}
        onClick={() => inputRef.current?.click()}
      >
        {occupe ? 'Traitement…' : video ? 'Photo ou vidéo' : 'Prendre une photo'}
      </button>
      {video && maxSeconds && (
        <p className="mt-1 text-[12px] text-muted">Vidéo : {maxSeconds} secondes maximum.</p>
      )}

      {medias.length > 0 && (
        <ul className="mt-3 grid grid-cols-3 gap-2">
          {medias.map((m) => (
            <li key={m.id} className="relative border-2 border-line">
              {m.kind === 'image' ? (
                <img src={m.dataUrl} alt="" className="h-24 w-full object-cover" />
              ) : (
                <video src={m.dataUrl} className="h-24 w-full object-cover" controls />
              )}
              <button
                type="button"
                aria-label="Supprimer"
                className="absolute right-0 top-0 bg-di px-2 py-0.5 text-xs font-bold text-white"
                onClick={() => retirer(m.id)}
              >
                ×
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
