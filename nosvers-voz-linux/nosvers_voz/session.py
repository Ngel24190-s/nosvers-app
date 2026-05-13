"""State machine de la sesión voz.

Estados:
    IDLE       — esperando wake word.
    DESPIERTA  — wake detectado, grabando lo que dice Angel.
    ACTIVA     — turno conversacional abierto. Si pasan 8s sin habla → IDLE.
                 Si pasan 5min totales → IDLE.

Comandos por voz reconocidos:
    "habla más rápido"     → +20% velocidad TTS
    "habla más despacio"   → -20% velocidad TTS
    "cambia a francés"     → idioma = "fr"
    "cambia a castellano"  → idioma = "es"
    "cierra sesión"        → vuelta a IDLE inmediato

Si lo dicho empieza por "captura" o "anota", se envía a `dia_capturar`.
El resto va a Claude como conversación.

Durante el playback TTS, el wake detector se silencia para que la propia
respuesta no dispare un nuevo wake (suprime acceptance scenario 2 del US3).
"""

from __future__ import annotations

import asyncio
import logging
import os
import queue
import threading
import time
from dataclasses import dataclass
from enum import Enum

import numpy as np
import sounddevice as sd

from .commands import parse_comando
from .config import Config, load_config
from .mcp_client import MCPClient, MCPClientError
from .stt_local import STTLocal
from .tts_local import TTSLocal
from .wake import WakeDetector

log = logging.getLogger(__name__)

CHUNK_SAMPLES_REC = 1600           # 100 ms @ 16 kHz
RMS_SILENCE_THRESHOLD = 0.008      # nivel por debajo del cual consideramos silencio
SILENCE_TO_END_REC_S = 1.5         # silencio para cerrar grabación de un turno
MAX_REC_S = 30.0                   # tope duro por turno


class Estado(str, Enum):
    IDLE = "idle"
    DESPIERTA = "despierta"
    ACTIVA = "activa"


@dataclass
class TurnoResultado:
    texto: str
    duracion_s: float


# ----------------- recorder con silence detection -----------------

class TurnRecorder:
    """Graba un turno de audio del usuario hasta silencio o tope."""

    def __init__(self, cfg: Config) -> None:
        self.cfg = cfg

    def grabar(self) -> tuple[np.ndarray, float]:
        """Bloqueante. Devuelve (audio float32 16k mono, duracion_s)."""
        sr = self.cfg.input_samplerate
        q: queue.Queue[np.ndarray] = queue.Queue()
        stop_evt = threading.Event()

        def cb(indata, frames, time_info, status):
            if status:
                log.warning("rec status %s", status)
            q.put(indata[:, 0].copy())

        device = self.cfg.input_device or None
        chunks: list[np.ndarray] = []
        t0 = time.monotonic()
        silence_since: float | None = None
        had_voice = False

        with sd.InputStream(
            samplerate=sr,
            blocksize=CHUNK_SAMPLES_REC,
            channels=1,
            dtype="float32",
            callback=cb,
            device=device,
        ):
            while not stop_evt.is_set():
                if time.monotonic() - t0 > MAX_REC_S:
                    log.info("recorder MAX_REC_S alcanzado")
                    break
                try:
                    chunk = q.get(timeout=0.2)
                except queue.Empty:
                    continue
                chunks.append(chunk)
                rms = float(np.sqrt(np.mean(chunk * chunk) + 1e-12))
                now = time.monotonic()
                if rms > RMS_SILENCE_THRESHOLD:
                    had_voice = True
                    silence_since = None
                else:
                    if had_voice:
                        if silence_since is None:
                            silence_since = now
                        elif now - silence_since >= SILENCE_TO_END_REC_S:
                            break

        if not chunks:
            return np.zeros(0, dtype=np.float32), 0.0
        audio = np.concatenate(chunks)
        return audio, time.monotonic() - t0


# ----------------- sesión -----------------

class SesionVoz:
    SYSTEM_PROMPT_ES = (
        "Eres Claudio, el asistente de voz personal de Angel, CEO de NosVers "
        "(ferme lombricole en Dordogne, Francia). Hablas castellano natural, "
        "directo, sin rodeos, frases cortas porque tu respuesta se sintetiza "
        "por TTS. Angel está manos-libres en casa — sé útil y conciso. Si te "
        "piden algo que requiere actuar en la finca o publicar contenido, "
        "responde con un plan claro de pasos, no actúes solo."
    )
    SYSTEM_PROMPT_FR = (
        "Tu es Claudio, l'assistant vocal personnel d'Angel, CEO de NosVers "
        "(ferme lombricole en Dordogne, France). Tu parles français naturel, "
        "direct, sans détours, phrases courtes parce que ta réponse est "
        "synthétisée par TTS. Angel est mains libres — sois utile et concis."
    )

    def __init__(self, cfg: Config | None = None) -> None:
        self.cfg = cfg or load_config()
        self.estado = Estado.IDLE
        self.recorder = TurnRecorder(self.cfg)
        self.stt = STTLocal(self.cfg)
        self.tts = TTSLocal(self.cfg)
        self.wake = WakeDetector(self.cfg, on_wake=self._on_wake)
        self._ts_inicio_sesion: float = 0.0
        self._claude = None  # lazy
        self._stop = threading.Event()

    # -------- API pública --------

    def arrancar(self) -> None:
        log.info("sesión voz arrancando")
        self.wake.start()
        try:
            while not self._stop.is_set():
                time.sleep(0.5)
        except KeyboardInterrupt:
            log.info("KeyboardInterrupt — saliendo")
        finally:
            self.wake.stop()

    def detener(self) -> None:
        self._stop.set()

    # -------- callbacks --------

    def _on_wake(self, confianza: float) -> None:
        if self.estado != Estado.IDLE:
            log.info("wake recibido pero estado=%s — ignorando", self.estado)
            return
        log.info("wake confianza=%.3f → DESPIERTA", confianza)
        threading.Thread(
            target=self._loop_sesion, daemon=True, name="nosvers-voz-session"
        ).start()

    # -------- loop principal de una sesión --------

    def _loop_sesion(self) -> None:
        self.estado = Estado.DESPIERTA
        self._ts_inicio_sesion = time.monotonic()
        try:
            self._hablar("Sí, dime.")
            self.estado = Estado.ACTIVA
            while self.estado == Estado.ACTIVA:
                if time.monotonic() - self._ts_inicio_sesion > self.cfg.timeout_total_sesion_s:
                    log.info("timeout total sesión")
                    self._hablar("Cierro sesión por timeout.")
                    break
                turno = self._capturar_turno()
                if turno is None:
                    log.info("sin habla en %ss — cierro sesión", self.cfg.auto_cierre_sin_habla_s)
                    break
                tipo, payload = parse_comando(turno.texto)
                if not self._procesar(tipo, payload, turno):
                    break
        finally:
            self.estado = Estado.IDLE
            log.info("sesión → IDLE")

    def _capturar_turno(self) -> TurnoResultado | None:
        """Graba y transcribe el turno actual. None si no hubo habla."""
        audio, dur = self.recorder.grabar()
        if audio.size == 0 or dur < 0.4:
            return None
        if dur < self.cfg.auto_cierre_sin_habla_s and float(np.sqrt(np.mean(audio * audio) + 1e-12)) < RMS_SILENCE_THRESHOLD:
            return None
        idioma = self.cfg.idioma_default
        texto = self.stt.transcribir(audio, idioma=idioma)
        if not texto:
            return None
        log.info("turno texto=%r dur=%.1fs", texto[:80], dur)
        return TurnoResultado(texto=texto, duracion_s=dur)

    # -------- procesar comando o chat --------

    def _procesar(self, tipo: str, payload: str | None, turno: TurnoResultado) -> bool:
        if tipo == "cierra":
            self._hablar("Vale, cierro." if self.cfg.idioma_default == "es" else "Très bien, je ferme.")
            return False
        if tipo == "rapido":
            self.cfg = self.cfg.with_velocidad(self.cfg.velocidad_tts * 1.2)
            self._hablar("Hablo más rápido.")
            return True
        if tipo == "despacio":
            self.cfg = self.cfg.with_velocidad(self.cfg.velocidad_tts / 1.2)
            self._hablar("Hablo más despacio.")
            return True
        if tipo == "fr":
            self.cfg = self.cfg.with_idioma("fr")
            self._hablar("Maintenant en français.", idioma="fr")
            return True
        if tipo == "es":
            self.cfg = self.cfg.with_idioma("es")
            self._hablar("Vuelvo al castellano.", idioma="es")
            return True
        if tipo == "captura":
            self._captura_via_mcp(payload or turno.texto)
            return True
        # chat con Claude
        respuesta = self._chat_con_claude(turno.texto)
        self._hablar(respuesta)
        return True

    def _captura_via_mcp(self, texto: str) -> None:
        async def run():
            async with MCPClient(self.cfg) as cli:
                return await cli.capturar(texto, origen="voz_linux", device_label="pc-casa-angel")
        try:
            res = asyncio.run(run())
            etiqueta = res.get("etiqueta_aplicada", "?")
            log.info("captura OK etiqueta=%s archivo=%s", etiqueta, res.get("archivo"))
            self._hablar(f"Anotado en {etiqueta}.")
        except MCPClientError as e:
            log.error("captura falló: %s", e)
            self._hablar("No he podido guardar la nota.")

    def _chat_con_claude(self, texto: str) -> str:
        try:
            if self._claude is None:
                from anthropic import Anthropic
                self._claude = Anthropic()  # usa ANTHROPIC_API_KEY
            system = (
                self.SYSTEM_PROMPT_ES
                if self.cfg.idioma_default == "es"
                else self.SYSTEM_PROMPT_FR
            )
            msg = self._claude.messages.create(
                model=self.cfg.modelo_chat,
                max_tokens=self.cfg.max_tokens_chat,
                system=system,
                messages=[{"role": "user", "content": texto}],
            )
            out = "".join(b.text for b in msg.content if hasattr(b, "text")).strip()
            return out or "No tengo respuesta."
        except Exception as e:
            log.exception("chat Claude falló")
            return f"Algo ha fallado al consultar a Claude."

    # -------- TTS con mute del wake --------

    def _hablar(self, texto: str, idioma: str | None = None) -> None:
        if not texto:
            return
        self.wake.mute()
        try:
            self.tts.decir(texto, idioma=idioma)
        finally:
            time.sleep(0.3)   # margen para que el eco se disipe
            self.wake.unmute()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    if not os.environ.get("ANTHROPIC_API_KEY"):
        log.warning("ANTHROPIC_API_KEY no está en env — el chat con Claude fallará")
    SesionVoz().arrancar()


if __name__ == "__main__":
    main()
