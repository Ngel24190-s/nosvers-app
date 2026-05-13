#!/usr/bin/env python3
"""
NosVers · Agente agt07_diario — resúmenes diario y semanal del diario común
de Angel + África (BRIEF §14).

Lee `knowledge_base/dia/YYYY-MM-DD.md`, sintetiza con Haiku (día) u
Opus (semana), y escribe a `dia/resumenes/`. Notifica Telegram opt-in.
Resúmenes agrupados por autor (Angel / África) + sección global.

Uso CLI:
    python3 agt07_diario.py --dia [--fecha YYYY-MM-DD] [--notificar-telegram]
    python3 agt07_diario.py --semana [--fecha YYYY-MM-DD] [--notificar-telegram]
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # /home/nosvers
from dotenv import load_dotenv
load_dotenv("/home/nosvers/.env")

from agents.agent_base import NosVersAgent
from voz.vault_io import RESUMENES_DIR, leer_dia, listar_dias, ETIQUETAS_VALIDAS

API_URL = "https://api.anthropic.com/v1/messages"
MODELO_DIA = "claude-haiku-4-5"
MODELO_SEMANA = "claude-opus-4-7"
PROMPT_DIR = Path(__file__).parent / "prompts"


class Agt07Diario(NosVersAgent):
    def __init__(self):
        super().__init__(name="agt07_diario", icon="📓",
                         personality="Sintetizador del diario de Angel. Tono directo, sin adornos.")

    # ── HELPERS ────────────────────────────────────────────
    def _llamar_anthropic(self, modelo: str, system: str, user: str, max_tokens: int = 1500) -> str:
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if not api_key:
            self.log.error("ANTHROPIC_API_KEY ausente")
            return ""
        try:
            r = requests.post(
                API_URL,
                headers={"x-api-key": api_key, "anthropic-version": "2023-06-01",
                         "Content-Type": "application/json"},
                json={"model": modelo, "max_tokens": max_tokens, "system": system,
                      "messages": [{"role": "user", "content": user}]},
                timeout=120,
            )
            if r.status_code != 200:
                self.log.warning(f"API status {r.status_code}: {r.text[:200]}")
                return ""
            return r.json()["content"][0]["text"].strip()
        except requests.RequestException as e:
            self.log.error(f"red error: {e}")
            return ""

    def _cargar_prompt(self, nombre: str) -> str:
        fp = PROMPT_DIR / nombre
        if not fp.exists():
            raise FileNotFoundError(fp)
        cont = fp.read_text(encoding="utf-8")
        # Quita frontmatter
        return re.sub(r"^---\n.*?\n---\n+", "", cont, count=1, flags=re.DOTALL).strip()

    def _grafico_etiquetas(self, notas: list) -> str:
        c = Counter(n.etiqueta for n in notas)
        lineas = []
        for et in ["trabajo", "nosvers", "familia", "mental", "idea", "otro"]:
            n = c.get(et, 0)
            bar = "▓" * n if n > 0 else "0"
            lineas.append(f"{et:8} {bar} {n if n > 0 else ''}".rstrip())
        return "```\n" + "\n".join(lineas) + "\n```"

    def _conteo_por_autor(self, notas: list) -> str:
        """Tabla compacta: cuántas notas por autor × etiqueta."""
        c: Counter = Counter((n.autor, n.etiqueta) for n in notas)
        autores = sorted({n.autor for n in notas})
        etiquetas = ["trabajo", "nosvers", "familia", "mental", "idea", "otro"]
        if not autores:
            return ""
        lineas = ["| autor  | " + " | ".join(etiquetas) + " | total |",
                  "|--------|" + "|".join(["--------"] * (len(etiquetas) + 1)) + "|"]
        for a in autores:
            row = [f"{c.get((a, et), 0)}" for et in etiquetas]
            total = sum(c.get((a, et), 0) for et in etiquetas)
            lineas.append(f"| {a:6} | " + " | ".join(row) + f" | {total} |")
        return "\n".join(lineas)

    def _formatear_notas_para_prompt(self, notas: list) -> str:
        if not notas:
            return ""
        return "\n".join(
            f"- [{n.autor}/{n.etiqueta}] {n.ts[11:19]} — {n.texto.strip()}"
            for n in notas
        )

    # ── RESUMEN DÍA ────────────────────────────────────────
    def resumen_dia(self, fecha: date, notificar_telegram: bool = False) -> Path | None:
        notas = leer_dia(fecha)
        if not notas:
            self.log.info(f"sin actividad para {fecha} — no genero resumen")
            return None
        system = self._cargar_prompt("resumen_dia.md")
        material = self._formatear_notas_para_prompt(notas)
        salida_modelo = self._llamar_anthropic(MODELO_DIA, system, material, max_tokens=1200)
        if salida_modelo.strip() == "SIN_ACTIVIDAD":
            self.log.info(f"modelo dijo SIN_ACTIVIDAD para {fecha}")
            return None
        if not salida_modelo:
            self.log.error(f"resumen_dia: respuesta vacía del modelo para {fecha}")
            return None

        n_angel = sum(1 for n in notas if n.autor == "angel")
        n_africa = sum(1 for n in notas if n.autor == "africa")
        cabecera = (
            f"---\n"
            f"fecha: {fecha.isoformat()}\n"
            f"tipo: dia\n"
            f"notas_procesadas: {len(notas)}\n"
            f"notas_angel: {n_angel}\n"
            f"notas_africa: {n_africa}\n"
            f"modelo: {MODELO_DIA}\n"
            f"generado_ts: {datetime.now().astimezone().isoformat()}\n"
            f"---\n\n"
            f"# Resumen del {fecha.isoformat()}\n\n"
        )
        cuerpo = salida_modelo
        if "Conteo por autor" not in cuerpo and self._conteo_por_autor(notas):
            cuerpo = cuerpo.rstrip() + "\n\n## Conteo por autor × etiqueta\n\n" + self._conteo_por_autor(notas) + "\n"
        if "Distribución de etiquetas" not in cuerpo:
            cuerpo = cuerpo.rstrip() + "\n\n## Distribución de etiquetas (global)\n\n" + self._grafico_etiquetas(notas) + "\n"

        RESUMENES_DIR.mkdir(parents=True, exist_ok=True)
        fp = RESUMENES_DIR / f"{fecha.isoformat()}.md"
        fp.write_text(cabecera + cuerpo + "\n", encoding="utf-8")
        self.log.info(f"resumen diario escrito en {fp} ({len(notas)} notas: angel={n_angel} africa={n_africa})")

        if notificar_telegram:
            self.notify(f"Resumen del {fecha.isoformat()}\n\n{cuerpo[:3500]}")
        return fp

    # ── RESUMEN SEMANA ─────────────────────────────────────
    def resumen_semana(self, fecha_fin: date, notificar_telegram: bool = False) -> Path | None:
        fecha_inicio = fecha_fin - timedelta(days=6)
        fechas = listar_dias(fecha_inicio, fecha_fin)
        if not fechas:
            self.log.info(f"sin actividad en la semana {fecha_inicio}..{fecha_fin}")
            return None
        bloques = []
        notas_totales = []
        for f in fechas:
            ns = leer_dia(f)
            if not ns:
                continue
            notas_totales.extend(ns)
            bloques.append(f"### {f.isoformat()}\n" + self._formatear_notas_para_prompt(ns))
        if not notas_totales:
            self.log.info("listar_dias devolvió fechas pero sin notas — no genero resumen")
            return None

        system = self._cargar_prompt("resumen_semana.md")
        material = "\n\n".join(bloques)
        salida = self._llamar_anthropic(MODELO_SEMANA, system, material, max_tokens=2500)
        if not salida or salida.strip() == "SIN_ACTIVIDAD":
            self.log.warning("modelo no produjo resumen semanal útil")
            return None

        # ISO week: YYYY-Www
        iso_year, iso_week, _ = fecha_fin.isocalendar()
        nombre = f"{iso_year}-W{iso_week:02d}.md"
        n_angel = sum(1 for n in notas_totales if n.autor == "angel")
        n_africa = sum(1 for n in notas_totales if n.autor == "africa")
        cabecera = (
            f"---\n"
            f"fecha_inicio: {fecha_inicio.isoformat()}\n"
            f"fecha_fin: {fecha_fin.isoformat()}\n"
            f"semana_iso: {iso_year}-W{iso_week:02d}\n"
            f"tipo: semana\n"
            f"dias_con_actividad: {len(fechas)}\n"
            f"notas_totales: {len(notas_totales)}\n"
            f"notas_angel: {n_angel}\n"
            f"notas_africa: {n_africa}\n"
            f"modelo: {MODELO_SEMANA}\n"
            f"generado_ts: {datetime.now().astimezone().isoformat()}\n"
            f"---\n\n"
            f"# Resumen semana {iso_year}-W{iso_week:02d} "
            f"({fecha_inicio.isoformat()} → {fecha_fin.isoformat()})\n\n"
        )
        cuerpo = salida
        if "Conteo por autor" not in cuerpo and self._conteo_por_autor(notas_totales):
            cuerpo = cuerpo.rstrip() + "\n\n## Conteo por autor × etiqueta\n\n" + self._conteo_por_autor(notas_totales) + "\n"
        if "Distribución de etiquetas" not in cuerpo:
            cuerpo = cuerpo.rstrip() + "\n\n## Distribución de etiquetas (acumulada)\n\n" + self._grafico_etiquetas(notas_totales) + "\n"

        RESUMENES_DIR.mkdir(parents=True, exist_ok=True)
        fp = RESUMENES_DIR / nombre
        fp.write_text(cabecera + cuerpo + "\n", encoding="utf-8")
        self.log.info(f"resumen semanal escrito en {fp} ({len(notas_totales)} notas en {len(fechas)} días)")

        if notificar_telegram:
            self.notify(f"Resumen semanal {iso_year}-W{iso_week:02d}\n\n{cuerpo[:3500]}")
        return fp


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--dia", action="store_true", help="Generar resumen diario")
    p.add_argument("--semana", action="store_true", help="Generar resumen semanal")
    p.add_argument("--fecha", type=str, default="", help="YYYY-MM-DD (default hoy)")
    p.add_argument("--notificar-telegram", action="store_true",
                   help="Empujar el resumen a Angel por Telegram")
    args = p.parse_args()
    if not (args.dia or args.semana):
        p.error("usa --dia o --semana")

    fecha = date.fromisoformat(args.fecha) if args.fecha else date.today()
    notif = args.notificar_telegram or os.getenv("TELEGRAM_NOTIFY_RESUMENES") == "1"

    a = Agt07Diario()
    if args.dia:
        fp = a.resumen_dia(fecha, notificar_telegram=notif)
        print(f"resumen diario: {fp if fp else 'no generado (sin actividad)'}")
    if args.semana:
        fp = a.resumen_semana(fecha, notificar_telegram=notif)
        print(f"resumen semanal: {fp if fp else 'no generado (sin actividad)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
