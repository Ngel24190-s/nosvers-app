import { useEffect, useRef, useState } from 'react';

/** Pavé de signature tactile — canvas natif, sans dépendance.
 *  Rend un PNG en data-URL, repris tel quel dans le PDF. */
export function SignaturePad({
  value,
  onChange,
}: {
  value?: string;
  onChange: (dataUrl: string | undefined) => void;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const dessine = useRef(false);
  const [vide, setVide] = useState(!value);

  // Le canvas est dimensionné en pixels physiques pour rester net sur mobile.
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ratio = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * ratio;
    canvas.height = rect.height * ratio;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.scale(ratio, ratio);
    ctx.lineWidth = 2;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.strokeStyle = '#000000';
    if (value) {
      const img = new Image();
      img.onload = () => ctx.drawImage(img, 0, 0, rect.width, rect.height);
      img.src = value;
      setVide(false);
    }
    // Volontairement monté une seule fois : re-dimensionner effacerait le tracé.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const position = (e: React.PointerEvent<HTMLCanvasElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    return { x: e.clientX - rect.left, y: e.clientY - rect.top };
  };

  const debut = (e: React.PointerEvent<HTMLCanvasElement>) => {
    e.currentTarget.setPointerCapture(e.pointerId);
    const ctx = canvasRef.current?.getContext('2d');
    if (!ctx) return;
    const { x, y } = position(e);
    ctx.beginPath();
    ctx.moveTo(x, y);
    dessine.current = true;
  };

  const trace = (e: React.PointerEvent<HTMLCanvasElement>) => {
    if (!dessine.current) return;
    const ctx = canvasRef.current?.getContext('2d');
    if (!ctx) return;
    const { x, y } = position(e);
    ctx.lineTo(x, y);
    ctx.stroke();
    if (vide) setVide(false);
  };

  /** Le tracé est aplati sur fond blanc et exporté en JPEG : un PNG
   *  transparent est réencodé en bitmap brut par jsPDF et pèse à lui seul
   *  près d'un mégaoctet dans le rapport. */
  const exporter = (source: HTMLCanvasElement): string => {
    const largeur = Math.min(source.width, 600);
    const plat = document.createElement('canvas');
    plat.width = largeur;
    plat.height = Math.round((source.height * largeur) / source.width);
    const ctx = plat.getContext('2d');
    if (!ctx) return source.toDataURL('image/jpeg', 0.85);
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, plat.width, plat.height);
    ctx.drawImage(source, 0, 0, plat.width, plat.height);
    return plat.toDataURL('image/jpeg', 0.85);
  };

  const fin = () => {
    if (!dessine.current) return;
    dessine.current = false;
    const canvas = canvasRef.current;
    if (canvas) onChange(exporter(canvas));
  };

  const effacer = () => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext('2d');
    if (!canvas || !ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    setVide(true);
    onChange(undefined);
  };

  return (
    <div>
      <canvas
        ref={canvasRef}
        className="signature-canvas h-40 w-full border-2 border-line bg-white"
        onPointerDown={debut}
        onPointerMove={trace}
        onPointerUp={fin}
        onPointerLeave={fin}
        onPointerCancel={fin}
      />
      <div className="mt-2 flex items-center justify-between">
        <span className="text-[13px] text-muted">
          {vide ? 'Signer dans le cadre ci-dessus' : 'Signature enregistrée'}
        </span>
        <button type="button" className="di-btn-ghost !py-1.5 !text-xs" onClick={effacer}>
          Effacer
        </button>
      </div>
    </div>
  );
}
