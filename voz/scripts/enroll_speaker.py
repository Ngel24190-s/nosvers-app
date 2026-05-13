#!/usr/bin/env python3
"""CLI de enrollment de voz para Angel/África (BRIEF §14.1).

Uso:
    python3 enroll_speaker.py --autor angel --audio /path/to/muestra.wav
    python3 enroll_speaker.py --autor africa --audio /path/to/muestra.opus
    python3 enroll_speaker.py --listar

La muestra ideal son 30s+ de voz natural en un entorno silencioso.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from dotenv import load_dotenv
load_dotenv("/home/nosvers/.env")

from voz.speaker_id import enroll, listar_enrolled


def main() -> int:
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--autor", choices=["angel", "africa"], help="Usuario a enrollar")
    g.add_argument("--listar", action="store_true", help="Listar enrollments existentes")
    p.add_argument("--audio", type=str, help="Path al WAV/Opus de muestra (30s+ recomendado)")
    args = p.parse_args()

    if args.listar:
        items = listar_enrolled()
        if not items:
            print("Sin enrollments. Ejecuta con --autor X --audio Y.")
            return 0
        for it in items:
            print(f"  {it['autor']:6}  {it['path']}  ({it['tamano_bytes']} bytes)")
        return 0

    if not args.audio:
        p.error("--audio es requerido cuando se especifica --autor")
    audio_path = Path(args.audio)
    if not audio_path.exists():
        print(f"ERROR: no existe {audio_path}", file=sys.stderr)
        return 2
    res = enroll(args.autor, audio_path)
    print(f"OK enrollment {res['autor']}: dim={res['dim']} guardado en {res['path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
