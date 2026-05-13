#!/usr/bin/env python3
"""CLI para revocar un token por jti."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from dotenv import load_dotenv
load_dotenv("/home/nosvers/.env")

from voz.auth import revocar_token, listar_tokens


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--jti", help="JTI a revocar")
    p.add_argument("--listar", action="store_true", help="Listar tokens activos")
    p.add_argument("--todos", action="store_true", help="Incluir revocados al listar")
    args = p.parse_args()
    if args.listar:
        for t in listar_tokens(incluir_revocados=args.todos):
            estado = "REVOCADO" if t["revoked_at"] else "activo"
            print(f"{t['jti']}  {t['device_label']:20}  {t['expires_at']:25}  {estado}")
        return 0
    if not args.jti:
        print("error: --jti requerido (o usa --listar)", file=sys.stderr)
        return 2
    ok = revocar_token(args.jti)
    print("✓ revocado" if ok else "✗ no encontrado o ya revocado")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
