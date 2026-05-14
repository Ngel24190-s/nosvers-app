import { useCallback, useEffect, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { Mic, MicOff, Square } from 'lucide-react';
import type { Context } from '../lib/auth';
import { startRecording, type RecordingHandle } from '../lib/audio';
import { apiFetch } from '../lib/api';
import type { DictadoResponse } from '../lib/api-types';
import Waveform from './Waveform';
import NeuralGraph from './NeuralGraph';

type Phase = 'idle' | 'recording' | 'sending' | 'thinking' | 'speaking';

interface Props {
  context: Context;
}

// Mapa color FAB / acento por contexto. Trabajo usa rojo DI + borde negro
// (FR-I-Tra-6); Casa/NosVers usan var(--primary) del tema.
function fabClasses(context: Context): string {
  if (context === 'trabajo') {
    return 'bg-[#D62828] border-4 border-black text-white';
  }
  return 'bg-primary border-2 border-on-primary text-on-primary';
}

function accentColor(context: Context): string {
  if (context === 'trabajo') return '#D62828';
  if (context === 'nosvers') return '#10b981';
  return '#5A7A2E';
}

const HOLD_MS = 200;
const CANCEL_DY = -80;
const DOUBLE_TAP_MS = 300;

export default function PTTOverlay({ context }: Props) {
  const [phase, setPhase] = useState<Phase>('idle');
  const [hint, setHint] = useState('');
  const [timer, setTimer] = useState(0);
  const [response, setResponse] = useState<DictadoResponse | null>(null);
  const recRef = useRef<RecordingHandle | null>(null);
  const startedAtRef = useRef<number>(0);
  const pointerStartY = useRef<number | null>(null);
  const cancelArmed = useRef(false);
  const lastTapRef = useRef<number>(0);
  const conversationModeRef = useRef(false);
  const timerInterval = useRef<number>();

  const accent = accentColor(context);

  const stopRecording = useCallback(
    async (cancelled: boolean) => {
      if (timerInterval.current) {
        window.clearInterval(timerInterval.current);
        timerInterval.current = undefined;
      }
      const rec = recRef.current;
      recRef.current = null;
      if (!rec) {
        setPhase('idle');
        return;
      }
      if (cancelled) {
        rec.cancel();
        setPhase('idle');
        return;
      }
      setPhase('sending');
      try {
        const blob = await rec.stop();
        // Si el audio es muy corto, descartamos
        if (blob.size < 1200) {
          setPhase('idle');
          return;
        }
        // El backend acepta transcript ya hecho; cliente hace STT local
        // futuro. Por ahora enviamos audio multipart al endpoint
        // /voz/api/capturar (que ya hace STT + dia_capturar). Para
        // dictado-procesar necesitamos un transcript previo.
        // Estrategia: usamos /voz/api/capturar para tener transcript +
        // luego /voz/api/dictado-procesar con el transcript.
        const fd = new FormData();
        fd.append('audio', blob, 'ptt.webm');
        fd.append(
          'meta',
          JSON.stringify({
            origen: `claudio-pwa:${context}`,
            etiqueta: 'voz',
            ts_iso: new Date().toISOString(),
          })
        );
        const cap = await apiFetch('/voz/api/capturar', {
          method: 'POST',
          body: fd,
        });
        const capJson = await cap.json().catch(() => ({}));
        const transcript: string = capJson?.transcripcion || capJson?.texto || '';
        if (!transcript.trim()) {
          setResponse({
            ok: false,
            voice_response: { text: 'No te he oído. Inténtalo otra vez.' },
          });
          setPhase('speaking');
          window.setTimeout(() => setPhase('idle'), 1800);
          return;
        }

        setPhase('thinking');
        const res = await apiFetch('/voz/api/dictado-procesar', {
          method: 'POST',
          context,
          body: JSON.stringify({ transcript }),
        });
        const data = (await res.json()) as DictadoResponse;
        setResponse(data);
        setPhase('speaking');
        // audio_url opcional — si viene, reproducir
        const url = data.voice_response?.audio_url;
        if (url) {
          try {
            const a = new Audio(url);
            a.play().catch(() => {});
            a.onended = () => setPhase('idle');
          } catch {
            window.setTimeout(() => setPhase('idle'), 2500);
          }
        } else {
          window.setTimeout(() => setPhase('idle'), 2500);
        }
      } catch (e) {
        setResponse({ ok: false, voice_response: { text: 'Error de red.' } });
        setPhase('speaking');
        window.setTimeout(() => setPhase('idle'), 1800);
      }
    },
    [context]
  );

  const beginRecording = useCallback(async () => {
    const r = await startRecording();
    if (!r) {
      setResponse({
        ok: false,
        voice_response: { text: 'Sin permiso de micrófono.' },
      });
      setPhase('speaking');
      window.setTimeout(() => setPhase('idle'), 1800);
      return;
    }
    recRef.current = r;
    startedAtRef.current = Date.now();
    setTimer(0);
    timerInterval.current = window.setInterval(() => {
      setTimer((Date.now() - startedAtRef.current) / 1000);
    }, 200);
    setPhase('recording');
    setHint('');
  }, []);

  // Gestos del FAB
  const onPointerDown = (e: React.PointerEvent) => {
    pointerStartY.current = e.clientY;
    cancelArmed.current = false;

    const now = Date.now();
    if (now - lastTapRef.current < DOUBLE_TAP_MS) {
      // double-tap → conversación 30s
      conversationModeRef.current = true;
      beginRecording();
      window.setTimeout(() => {
        if (recRef.current) {
          stopRecording(false);
          conversationModeRef.current = false;
        }
      }, 30000);
      lastTapRef.current = 0;
      return;
    }
    lastTapRef.current = now;

    // Hold detection
    window.setTimeout(() => {
      if (pointerStartY.current !== null && phase === 'idle' && !recRef.current) {
        beginRecording();
      }
    }, HOLD_MS);
  };

  const onPointerMove = (e: React.PointerEvent) => {
    if (pointerStartY.current === null) return;
    const dy = e.clientY - pointerStartY.current;
    if (dy < CANCEL_DY) {
      if (!cancelArmed.current) {
        cancelArmed.current = true;
        setHint('SUELTA PARA CANCELAR');
      }
    } else if (cancelArmed.current) {
      cancelArmed.current = false;
      setHint('');
    }
  };

  const onPointerUp = () => {
    const wasArmed = cancelArmed.current;
    pointerStartY.current = null;
    cancelArmed.current = false;
    if (phase === 'recording' && !conversationModeRef.current) {
      stopRecording(wasArmed);
    }
  };

  const onPointerCancel = () => {
    pointerStartY.current = null;
    cancelArmed.current = false;
    if (phase === 'recording') stopRecording(true);
  };

  useEffect(() => () => {
    if (timerInterval.current) window.clearInterval(timerInterval.current);
    if (recRef.current) recRef.current.cancel();
  }, []);

  return (
    <>
      {/* FAB siempre visible mientras hay contexto */}
      <button
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerCancel={onPointerCancel}
        className={`fixed bottom-20 right-5 w-16 h-16 rounded-full shadow-lg z-40
                    flex items-center justify-center active:scale-95 transition-transform
                    ${fabClasses(context)}`}
        aria-label="Pulsa para hablar"
      >
        {phase === 'idle' ? (
          <Mic size={26} strokeWidth={2.5} />
        ) : phase === 'recording' ? (
          <Square size={22} strokeWidth={2.5} />
        ) : (
          <Mic size={26} strokeWidth={2.5} />
        )}
      </button>

      <AnimatePresence>
        {phase !== 'idle' && (
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 30 }}
            transition={{ duration: 0.15 }}
            className="fixed inset-0 z-50 flex items-end justify-center bg-black/60 backdrop-blur-sm pb-32"
          >
            <div className="bg-white text-black rounded-2xl p-5 mx-4 max-w-md w-full shadow-2xl"
                 style={{ borderColor: accent, borderWidth: context === 'trabajo' ? 2 : 0, borderStyle: 'solid' }}>
              {phase === 'recording' && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="di-title text-xs" style={{ color: accent }}>
                      Te escucho
                    </span>
                    <span className="font-mono text-lg" style={{ color: accent }}>
                      {timer.toFixed(1)}s
                    </span>
                  </div>
                  <Waveform analyser={recRef.current?.analyser ?? null} color={accent} />
                  <div className="text-[10px] text-neutral-600 uppercase tracking-tight text-center">
                    {hint || 'desliza arriba para cancelar'}
                  </div>
                </div>
              )}

              {phase === 'sending' && (
                <div className="flex items-center justify-center py-4 text-sm text-neutral-700">
                  Enviando…
                </div>
              )}

              {phase === 'thinking' && (
                <div className="flex flex-col items-center py-2">
                  <NeuralGraph color={accent} />
                  <div className="text-xs text-neutral-700 mt-2">Pensando…</div>
                </div>
              )}

              {phase === 'speaking' && response && (
                <div className="space-y-2">
                  {response.voice_response?.text ? (
                    <p className="text-sm">{response.voice_response.text}</p>
                  ) : response.tool_result ? (
                    <p className="text-sm">{response.tool_result}</p>
                  ) : (
                    <p className="text-sm text-neutral-700">Hecho.</p>
                  )}
                  {response.intent?.tool && (
                    <p className="text-[10px] text-neutral-500 di-title">
                      tool: {response.intent.tool}
                      {response.intent.fallback ? ' (fallback)' : ''}
                    </p>
                  )}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

// Marker para tests / linter inutilizado
export const _MicOff = MicOff;
