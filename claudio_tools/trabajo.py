"""Tools MCP del contexto Trabajo (DI Environnement) — Fase 007.

10 tools que operan sobre `vault/trabajo/`:
- chantier_listar / crear / evento / estado / documento_listar
- equipe_listar / anotar
- devis_anotar
- ppsps_crear
- documento_trabajo_archivar

Convenciones (heredadas de claudio_tools.common):
- Todas síncronas, devuelven `str` para TTS-friendly.
- `autor` siempre llega del JWT (server-side), nunca del body.
- Loguean en `claudio/logs/YYYY-MM-DD.jsonl`.
- Validación de scope `context=trabajo` la hace el wrapper en
  `voz/rest.py` (FR-G-2). Aquí asumimos llamada autorizada.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from .common import (
    atomic_append,
    atomic_write,
    dump_frontmatter,
    ensure_dir,
    log_call,
    normalize_author,
    parse_frontmatter,
    slugify,
    today_iso,
    ts_human,
    vault,
)


# ── Paths ────────────────────────────────────────────────────────────

def _trabajo_root() -> Path:
    return vault() / "trabajo"


def _ensure_skeleton() -> None:
    """Idempotente. Crea estructura mínima si falta."""
    root = _trabajo_root()
    for sub in (
        "chantiers",
        "equipe/formations",
        "documents/ppsps",
        "documents/plans-retrait",
        "documents/devis",
        "documents/certificats",
        "documents/diag-amiante",
        "clients",
        "materiel/mantenimiento",
        "normes",
        "formations",
    ):
        ensure_dir(root / sub)
    idx = root / "chantiers" / "INDEX.md"
    if not idx.exists():
        atomic_write(idx, "# Chantiers — DI Environnement\n\n## Activos\n\n_(vacío)_\n")


def _chantier_dir(slug: str) -> Path:
    return _trabajo_root() / "chantiers" / slug


def _resolve_chantier_slug(raw: str) -> str | None:
    """Devuelve el slug exacto matching para `raw`. Tolera:
    - slug exacto: 'bordeaux-nord-rehabilitation'.
    - prefijo: 'bordeaux-nord' → encuentra el primero que empieza así.
    - keyword: 'bordeaux' → idem.
    Si hay 0 o ≥2 matches, devuelve None."""
    if not raw:
        return None
    candidate = slugify(raw)
    raiz = _trabajo_root() / "chantiers"
    if not raiz.exists():
        return None
    # Match exacto primero
    if (raiz / candidate).is_dir() and not candidate.startswith("_"):
        return candidate
    # Prefijo / keyword
    matches = [d.name for d in raiz.iterdir()
               if d.is_dir() and not d.name.startswith("_")
               and candidate in d.name]
    if len(matches) == 1:
        return matches[0]
    return None


# ── chantier_listar ──────────────────────────────────────────────────

def chantier_listar(estado: str = "activos") -> str:
    """Lista chantiers. `estado` ∈ activos | archivados | urgentes | todos."""
    _ensure_skeleton()
    estado = (estado or "activos").strip().lower()
    if estado not in {"activos", "archivados", "urgentes", "todos"}:
        log_call("chantier_listar", "system", {"estado": estado}, False)
        return f"❌ estado inválido: {estado}"

    raiz = _trabajo_root() / "chantiers"
    encontrados: list[dict] = []
    for sub in sorted(raiz.iterdir()):
        if not sub.is_dir() or sub.name.startswith("_"):
            continue
        idx = sub / "INDEX.md"
        if not idx.exists():
            continue
        meta, _ = parse_frontmatter(idx.read_text(encoding="utf-8"))
        meta["__slug"] = sub.name
        encontrados.append(meta)

    if estado != "todos":
        encontrados = [m for m in encontrados
                       if (m.get("estado") or "activo") == estado.rstrip("s")
                       or (estado == "activos" and (m.get("estado") or "activo") == "activo")
                       or (estado == "archivados" and m.get("estado") == "archivado")
                       or (estado == "urgentes" and m.get("estado") == "urgente")]

    log_call("chantier_listar", "system",
             {"estado": estado, "n": len(encontrados)}, True)
    if not encontrados:
        return f"Sin chantiers {estado}."

    lines = [f"{len(encontrados)} chantier(s) {estado}:"]
    for m in encontrados:
        nom = m.get("nombre") or m.get("__slug")
        cli = m.get("cliente") or "—"
        dev = m.get("devis_eur") or 0
        lines.append(f"• {m['__slug']} · {nom} · {cli} · {dev}€")
    return "\n".join(lines)


# ── chantier_crear ───────────────────────────────────────────────────

def chantier_crear(
    nombre: str,
    direccion: str,
    cliente: str,
    devis_eur: float,
    equipe_ids: str,
    fecha_inicio: str,
    fecha_fin_prev: str,
    autor: str = "angel",
) -> str:
    """Crea un nuevo chantier. equipe_ids puede ser CSV o lista YAML inline."""
    _ensure_skeleton()
    autor = normalize_author(autor, allow_bris=False)
    if not nombre.strip():
        return "❌ nombre obligatorio"
    if not cliente.strip():
        return "❌ cliente obligatorio"

    slug = slugify(nombre)
    cdir = _chantier_dir(slug)
    if cdir.exists():
        log_call("chantier_crear", autor, {"slug": slug}, False,
                 {"motivo": "ya_existe"})
        return f"❌ chantier ya existe: {slug}"

    ensure_dir(cdir / "journal")

    equipe_list = [e.strip() for e in str(equipe_ids).replace("[", "")
                   .replace("]", "").split(",") if e.strip()]

    meta: dict[str, Any] = {
        "slug": slug,
        "nombre": nombre.strip(),
        "direccion": direccion.strip(),
        "cliente": cliente.strip(),
        "devis_eur": float(devis_eur),
        "equipe_ids": equipe_list,
        "fecha_inicio": fecha_inicio.strip() or today_iso(),
        "fecha_fin_prev": fecha_fin_prev.strip(),
        "estado": "activo",
        "creado": today_iso(),
        "creado_por": autor,
    }
    body = (
        f"\n# {nombre.strip()}\n\n"
        f"**Cliente**: {cliente.strip()}\n\n"
        f"**Dirección**: {direccion.strip()}\n\n"
        f"**Devis**: {float(devis_eur):,.2f} €\n\n"
        f"**Equipo asignado**: {', '.join(equipe_list) or '—'}\n\n"
        f"## Journal\n\nVer carpeta `journal/`.\n"
    )
    atomic_write(cdir / "INDEX.md", dump_frontmatter(meta, body))

    # Append a la lista maestra
    idx_master = _trabajo_root() / "chantiers" / "INDEX.md"
    line = (f"- [{slug}](./{slug}/INDEX.md) · {nombre.strip()} · "
            f"{cliente.strip()} · {float(devis_eur):,.0f}€ · "
            f"creado {today_iso()}\n")
    atomic_append(idx_master, line)

    log_call("chantier_crear", autor, {"slug": slug, "cliente": cliente},
             True)
    return f"✅ Chantier creado: {slug}. Equipe: {', '.join(equipe_list) or '—'}."


# ── chantier_evento ──────────────────────────────────────────────────

_EVENTO_TIPOS = {"avance", "incidente", "seguridad", "journal", "otro"}


def chantier_evento(
    chantier_id: str,
    tipo: str,
    descripcion: str,
    autor: str = "angel",
) -> str:
    """Append a journal del chantier."""
    _ensure_skeleton()
    autor = normalize_author(autor, allow_bris=False)
    slug = _resolve_chantier_slug(chantier_id) or ""
    cdir = _chantier_dir(slug) if slug else None
    if not cdir or not cdir.exists():
        log_call("chantier_evento", autor, {"chantier_id": chantier_id},
                 False, {"motivo": "no_resuelto"})
        return f"❌ chantier no encontrado: {chantier_id!r}"

    tipo = (tipo or "journal").strip().lower()
    if tipo not in _EVENTO_TIPOS:
        tipo = "otro"
    desc = descripcion.strip()
    if not desc:
        return "❌ descripción vacía"

    fecha = today_iso()
    journal_file = cdir / "journal" / f"{fecha}.md"
    icon = {
        "avance": "🚀",
        "incidente": "⚠️",
        "seguridad": "🛡️",
        "journal": "📝",
        "otro": "•",
    }[tipo]
    chunk = f"\n## {ts_human()} · {icon} {tipo}\n\n{desc}\n\n— *{autor}*\n"
    atomic_append(journal_file, chunk)

    log_call("chantier_evento", autor,
             {"slug": slug, "tipo": tipo, "len": len(desc)}, True)
    return f"✅ {icon} Anotado en {slug} (journal {fecha})."


# ── chantier_estado ──────────────────────────────────────────────────

def chantier_estado(chantier_id: str) -> str:
    """Snapshot del chantier."""
    _ensure_skeleton()
    slug = _resolve_chantier_slug(chantier_id) or ""
    cdir = _chantier_dir(slug) if slug else None
    if not cdir or not cdir.exists():
        return f"❌ chantier no encontrado: {chantier_id!r}"

    idx = cdir / "INDEX.md"
    meta: dict[str, Any] = {}
    if idx.exists():
        meta, _ = parse_frontmatter(idx.read_text(encoding="utf-8"))

    journals = sorted((cdir / "journal").glob("*.md"))
    n_eventos = 0
    ultimo_dia = ""
    ultimo_extracto = ""
    if journals:
        ultimo_dia = journals[-1].stem
        last_text = journals[-1].read_text(encoding="utf-8")
        n_eventos = sum(1 for _ in journals) + last_text.count("\n## ") - 1
        # Última línea no vacía como extracto
        for line in reversed(last_text.splitlines()):
            line = line.strip()
            if line and not line.startswith("—"):
                ultimo_extracto = line[:80]
                break

    estado = meta.get("estado", "activo")
    cliente = meta.get("cliente", "—")
    devis = meta.get("devis_eur", 0)
    equipe = meta.get("equipe_ids", []) or []
    equipe_str = ", ".join(equipe) if isinstance(equipe, list) else str(equipe)

    log_call("chantier_estado", "system", {"slug": slug}, True)
    lines = [
        f"📋 Chantier {slug} · estado: {estado}",
        f"Cliente: {cliente} · Devis: {devis}€",
        f"Equipe: {equipe_str or '—'}",
        f"Inicio: {meta.get('fecha_inicio', '—')} · Fin prev: {meta.get('fecha_fin_prev', '—')}",
    ]
    if ultimo_dia:
        lines.append(f"Último journal: {ultimo_dia} ({n_eventos} eventos totales)")
        if ultimo_extracto:
            lines.append(f"   └ {ultimo_extracto}")
    else:
        lines.append("Sin entradas de journal.")
    return "\n".join(lines)


# ── chantier_documento_listar ────────────────────────────────────────

_DOC_TIPOS = {"todos", "ppsps", "plans-retrait", "devis",
              "certificats", "diag-amiante"}


def chantier_documento_listar(chantier_id: str, tipo: str = "todos") -> str:
    """Documentos asociados a un chantier (por convención de naming
    `{slug}.md` o `{slug}-*.md` en `documents/{tipo}/`)."""
    _ensure_skeleton()
    slug = _resolve_chantier_slug(chantier_id) or slugify(chantier_id or "")
    if not slug:
        return "❌ chantier_id vacío"
    tipo = (tipo or "todos").strip().lower()
    if tipo not in _DOC_TIPOS:
        return f"❌ tipo inválido: {tipo}"

    tipos = sorted(_DOC_TIPOS - {"todos"}) if tipo == "todos" else [tipo]
    encontrados: list[str] = []
    for t in tipos:
        d = _trabajo_root() / "documents" / t
        if not d.exists():
            continue
        for f in sorted(d.glob(f"{slug}*.md")):
            encontrados.append(f"• {t}/{f.name}")

    log_call("chantier_documento_listar", "system",
             {"slug": slug, "tipo": tipo, "n": len(encontrados)}, True)
    if not encontrados:
        return f"Sin documentos para {slug} (tipo: {tipo})."
    return f"{len(encontrados)} doc(s) para {slug}:\n" + "\n".join(encontrados)


# ── equipe_listar ────────────────────────────────────────────────────

def equipe_listar() -> str:
    """Lee `equipe/operateurs.yaml` y devuelve lista activa."""
    _ensure_skeleton()
    path = _trabajo_root() / "equipe" / "operateurs.yaml"
    if not path.exists():
        return "Sin operadores registrados."

    text = path.read_text(encoding="utf-8")
    # Parser ligero (no traemos PyYAML por dep): buscamos `- id: <x>` y
    # campos top-level dentro del bloque hasta el siguiente `-` o EOF.
    operateurs: list[dict] = []
    current: dict | None = None
    indent_block = False
    for line in text.splitlines():
        if line.startswith("operateurs:"):
            continue
        m = line.lstrip()
        if line.startswith("  - id:"):
            if current:
                operateurs.append(current)
            current = {"id": m.split(":", 1)[1].strip()}
            indent_block = True
            continue
        if indent_block and current is not None and line.startswith("    "):
            if ":" in m and not m.startswith("-"):
                k, _, v = m.partition(":")
                v = v.strip()
                if v:
                    current[k.strip()] = v
    if current:
        operateurs.append(current)

    activos = [o for o in operateurs
               if str(o.get("activo", "true")).lower() in ("true", "yes", "1")]

    log_call("equipe_listar", "system", {"n": len(activos)}, True)
    if not activos:
        return "Sin operadores activos."

    lines = [f"{len(activos)} operador(es) activo(s):"]
    for o in activos:
        lines.append(f"• {o.get('id')} · {o.get('nombre', '—')} · {o.get('rol', '—')}")
    return "\n".join(lines)


# ── equipe_anotar ────────────────────────────────────────────────────

def equipe_anotar(
    operario: str,
    evento: str,
    fecha: str = "hoy",
) -> str:
    """Append a `equipe/formations/{operario}/{año}.md`."""
    _ensure_skeleton()
    op_slug = slugify(operario)
    if not op_slug:
        return "❌ operario obligatorio"
    if not evento.strip():
        return "❌ evento vacío"
    fecha = (fecha or "hoy").strip()
    year = date.today().year
    if fecha != "hoy" and len(fecha) >= 4 and fecha[:4].isdigit():
        try:
            year = int(fecha[:4])
        except ValueError:
            pass
    target = _trabajo_root() / "equipe" / "formations" / op_slug / f"{year}.md"
    chunk = f"\n## {fecha} — {ts_human()}\n\n{evento.strip()}\n"
    atomic_append(target, chunk)

    log_call("equipe_anotar", "system",
             {"operario": op_slug, "year": year}, True)
    return f"✅ Anotado en formación de {op_slug} ({year})."


# ── devis_anotar ─────────────────────────────────────────────────────

def devis_anotar(
    cliente: str,
    monto_eur: float,
    chantier_ref: str = "",
) -> str:
    """Append a `documents/devis/{cliente}.md`."""
    _ensure_skeleton()
    cli_slug = slugify(cliente)
    if not cli_slug:
        return "❌ cliente obligatorio"
    target = _trabajo_root() / "documents" / "devis" / f"{cli_slug}.md"
    if not target.exists():
        atomic_write(
            target,
            f"# Devis — {cliente}\n\n_Histórico de devis emitidos._\n",
        )
    chunk = (f"\n## {ts_human()} · {float(monto_eur):,.2f} €\n"
             f"{f'Chantier ref: `{chantier_ref}`' if chantier_ref else ''}\n")
    atomic_append(target, chunk)
    log_call("devis_anotar", "system",
             {"cliente": cli_slug, "monto_eur": float(monto_eur),
              "chantier_ref": chantier_ref}, True)
    return f"✅ Devis {float(monto_eur):,.2f}€ anotado para {cliente}."


# ── ppsps_crear ──────────────────────────────────────────────────────

def ppsps_crear(
    chantier_id: str,
    version: str = "v1",
    observaciones: str = "",
) -> str:
    """Crea `documents/ppsps/{chantier}.md` con plantilla mínima."""
    _ensure_skeleton()
    slug = slugify(chantier_id) if chantier_id else ""
    if not slug:
        return "❌ chantier_id obligatorio"
    target = _trabajo_root() / "documents" / "ppsps" / f"{slug}-{version}.md"
    if target.exists():
        return f"⚠️  PPSPS {slug}-{version} ya existe."
    body = (
        f"---\nchantier: {slug}\nversion: {version}\n"
        f"creado: {today_iso()}\n---\n\n"
        f"# PPSPS — {slug} — {version}\n\n"
        "## 1. Objet\n\n_(décrire l'objet du chantier)_\n\n"
        "## 2. Évaluation des risques\n\n"
        "- Empoussièrement attendu: niveau ?\n"
        "- Sous-section: SS3 / SS4 ?\n"
        "- Encadrement habilité: oui / non\n\n"
        "## 3. Modes opératoires\n\n_(détail par phase)_\n\n"
        "## 4. EPI / EPC\n\n_(combinaisons, masques, filtres, SAS, ventilation)_\n\n"
        "## 5. Décontamination\n\n_(SAS personnel + matériel)_\n\n"
        "## 6. Gestion des déchets\n\n_(sacs, BSD, transporteur, exutoire)_\n\n"
        "## 7. Mesures empoussièrement\n\n_(plan de mesure, points)_\n\n"
        f"## Observations\n\n{observaciones.strip() or '_(à compléter)_'}\n"
    )
    atomic_write(target, body)
    log_call("ppsps_crear", "system",
             {"slug": slug, "version": version}, True)
    return f"✅ PPSPS creado: {slug}-{version}."


# ── documento_trabajo_archivar ───────────────────────────────────────

_DOC_ARCH_TIPOS = {
    "certificat": "certificats",
    "diag-amiante": "diag-amiante",
    "plan-retrait": "plans-retrait",
    "otro": "diag-amiante",  # cubo genérico hasta crear `otros/`
}


def documento_trabajo_archivar(
    tipo: str,
    contenido: str,
    chantier_ref: str = "",
) -> str:
    """Archiva contenido en `documents/{tipo}/{slug}-{stamp}.md`."""
    _ensure_skeleton()
    tipo_norm = (tipo or "otro").strip().lower()
    sub = _DOC_ARCH_TIPOS.get(tipo_norm, "diag-amiante")
    if not contenido.strip():
        return "❌ contenido vacío"
    base_slug = slugify(chantier_ref or tipo_norm)
    stamp = today_iso().replace("-", "")
    target = _trabajo_root() / "documents" / sub / f"{base_slug}-{stamp}.md"
    body = (
        f"---\ntipo: {tipo_norm}\nchantier_ref: {chantier_ref}\n"
        f"archivado: {ts_human()}\n---\n\n{contenido.strip()}\n"
    )
    # Si ya existe (mismo día + mismo slug), append con separador
    if target.exists():
        atomic_append(target, f"\n\n---\n\n{contenido.strip()}\n")
    else:
        atomic_write(target, body)
    log_call("documento_trabajo_archivar", "system",
             {"tipo": tipo_norm, "sub": sub, "chantier_ref": chantier_ref},
             True)
    return f"✅ Documento archivado en {sub}/{target.name}."
