#!/usr/bin/env python3
"""CLI para emitir tokens Bearer de la PWA. Uso:
    python3 issue_token.py --device movil-angel --autor angel [--ttl 365]
    python3 issue_token.py --device movil-africa --autor africa
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from dotenv import load_dotenv
load_dotenv("/home/nosvers/.env")

from voz.auth import emitir_token


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--device", required=True, help="Etiqueta del dispositivo (ej: movil-angel)")
    p.add_argument("--autor", required=True, choices=["angel", "africa"], help="Usuario asociado (BRIEF §14)")
    p.add_argument("--ttl", type=int, default=365, help="TTL en días (default 365)")
    args = p.parse_args()
    res = emitir_token(args.device, ttl_days=args.ttl, autor=args.autor)
    print(f"device: {res['device']}")
    print(f"autor:  {res['autor']}")
    print(f"jti:    {res['jti']}")
    print(f"expira: {res['expires_at']}")
    print()
    print("JWT (pegar en la PWA):")
    print(res["jwt"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
