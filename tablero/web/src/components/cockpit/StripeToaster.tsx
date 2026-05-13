import { useEffect, useRef } from 'react';
import { toast } from 'sonner';
import { Euro } from 'lucide-react';
import type { UseWebSocketReturn } from '../../hooks/useWebSocket';

function beepFallback() {
  try {
    const AC = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
    const ac = new AC();
    const o = ac.createOscillator();
    const g = ac.createGain();
    o.connect(g);
    g.connect(ac.destination);
    o.frequency.value = 880;
    g.gain.value = 0.08;
    o.start();
    setTimeout(() => {
      o.stop();
      ac.close();
    }, 180);
  } catch {
    /* ignore */
  }
}

interface RevenuePayload {
  day_eur: number;
  month_eur: number;
  target_eur: number;
  blocked: boolean;
  last_payment: { amount_eur: number; desc: string; ts: number } | null;
}

/**
 * StripeToaster — escucha canal `revenue` y dispara toast cuando entra un pago nuevo.
 * No renderiza nada en el DOM; el toaster se monta una vez en Cockpit.tsx.
 */
export function StripeToaster({ ws }: { ws: UseWebSocketReturn }) {
  const lastTsRef = useRef<number>(0);

  useEffect(() => {
    return ws.subscribe('revenue', (p) => {
      const payload = p as RevenuePayload;
      if (payload.blocked || !payload.last_payment) return;
      const ts = payload.last_payment.ts;
      if (ts > 0 && ts !== lastTsRef.current) {
        if (lastTsRef.current !== 0) {
          // sólo notifica de pagos nuevos (no del estado inicial)
          toast(
            <div className="flex items-center gap-3">
              <div className="cockpit-glass !shadow-none p-2 rounded-md">
                <Euro size={16} className="text-accent-green" />
              </div>
              <div>
                <div className="cockpit-mono text-sm font-bold text-accent-green">
                  +€{payload.last_payment.amount_eur.toFixed(2)}
                </div>
                <div className="text-[11px] text-cockpit-textDim">
                  {payload.last_payment.desc}
                </div>
              </div>
            </div>,
            { duration: 8000 },
          );
          if (localStorage.getItem('cockpit_sound') === 'on') {
            // Si existe un asset cha-ching.mp3, usarlo; si no, fallback a beep WebAudio.
            try {
              const audio = new Audio('/sounds/cha-ching.mp3');
              audio.volume = 0.4;
              audio.play().catch(() => beepFallback());
            } catch {
              beepFallback();
            }
          }
        }
        lastTsRef.current = ts;
      }
    });
  }, [ws]);

  return null;
}
