"""
voz.compose_voice_response — Templates de respuesta hablada por tool.

Función pura, sin LLM, latencia < 5 ms. Recibe el tool ejecutado, sus args,
el resultado del tool (string crudo) y el autor; devuelve una frase
natural en español para TTS local.
"""
from __future__ import annotations

import re
from datetime import date, datetime, timedelta


# ─── Helpers ────────────────────────────────────────────────────

_MESES_ES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]


def _fecha_legible(s: str) -> str:
    """Convierte fecha en string a frase corta: 'hoy', 'mañana', '12 de mayo'."""
    if not s:
        return "hoy"
    s = s.strip().lower()
    if s in ("hoy",):
        return "hoy"
    if s in ("mañana", "manana"):
        return "mañana"
    # ISO
    try:
        f = datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        try:
            f = datetime.strptime(s, "%Y-%m-%d %H:%M").date()
        except ValueError:
            return s
    hoy = date.today()
    if f == hoy:
        return "hoy"
    if f == hoy + timedelta(days=1):
        return "mañana"
    return f"{f.day} de {_MESES_ES[f.month - 1]}"


def _monto_legible(monto) -> str:
    try:
        m = float(monto)
    except (TypeError, ValueError):
        return str(monto)
    if m == int(m):
        return f"{int(m)} euros"
    return f"{m:.2f} euros".replace(".", " con ")


def _extract_total(result: str) -> str | None:
    """Busca '… 123.45€' o 'Mes ...: 287.00€' en el output de un tool de gastos."""
    m = re.search(r"Mes\s+\d{4}-\d{2}:\s+([\d.]+)€", result or "")
    if m:
        return m.group(1)
    return None


def _extract_n_items(result: str) -> str | None:
    """Busca patrones tipo '7 items'."""
    m = re.search(r"(\d+)\s+items?", result or "")
    if m:
        return m.group(1)
    return None


# ─── Templates por tool ─────────────────────────────────────────

def _t_gasto_anotar(args: dict, result: str, autor: str) -> str:
    monto = _monto_legible(args.get("monto_eur", 0))
    concepto = str(args.get("concepto", "")).strip() or "gasto"
    total = _extract_total(result)
    if total:
        return f"Apuntado, {concepto} {monto}. Llevas {total} euros este mes."
    return f"Apuntado, {concepto} {monto}."


def _t_gastos_resumen(args: dict, result: str, autor: str) -> str:
    total = _extract_total(result) or ""
    if total:
        return f"En {args.get('periodo', 'mes actual')} llevas {total} euros."
    return "Aquí tienes el resumen."


def _t_recurrente_alertar(args: dict, result: str, autor: str) -> str:
    return "Te muestro los próximos cargos."


def _t_recordatorio_crear(args: dict, result: str, autor: str) -> str:
    fecha = _fecha_legible(str(args.get("fecha", "hoy")))
    texto = str(args.get("texto", "")).strip()
    if len(texto) > 40:
        texto = texto[:37] + "…"
    return f"Hecho, {fecha} te aviso de {texto}."


def _t_recordatorios_listar(args: dict, result: str, autor: str) -> str:
    return "Te leo los recordatorios."


def _t_recordatorio_completar(args: dict, result: str, autor: str) -> str:
    return "Recordatorio marcado como hecho."


def _t_familia_cumpleanos_listar(args: dict, result: str, autor: str) -> str:
    return "Te leo los próximos cumpleaños."


def _t_lista_compras_anadir(args: dict, result: str, autor: str) -> str:
    item = str(args.get("item", "")).strip() or "item"
    n = _extract_n_items(result)
    if n:
        return f"{item} añadido. Lista con {n} cosas."
    return f"{item} añadido a la lista."


def _t_lista_compras_ver(args: dict, result: str, autor: str) -> str:
    return "Aquí tienes la lista."


def _t_lista_compras_completar(args: dict, result: str, autor: str) -> str:
    item = str(args.get("item", "")).strip() or "Marcado"
    return f"Marcado: {item}."


def _t_despensa_estado(args: dict, result: str, autor: str) -> str:
    return "Te leo la despensa."


def _t_menu_sugerir(args: dict, result: str, autor: str) -> str:
    return "Aquí va el menú."


def _t_receta_guardar(args: dict, result: str, autor: str) -> str:
    nombre = str(args.get("nombre", "")).strip() or "la receta"
    return f"Receta guardada: {nombre}."


def _t_coche_estado(args: dict, result: str, autor: str) -> str:
    return "Te leo el estado del coche."


def _t_coche_evento(args: dict, result: str, autor: str) -> str:
    tipo = str(args.get("tipo", "")).strip() or "evento"
    fecha = _fecha_legible(str(args.get("fecha", "hoy")))
    return f"{tipo.capitalize()} del coche apuntado, {fecha}."


def _t_documento_anotar(args: dict, result: str, autor: str) -> str:
    tipo = str(args.get("tipo", "documento"))
    fuente = str(args.get("fuente", "")).strip()
    fecha = _fecha_legible(str(args.get("fecha", "hoy")))
    if fuente:
        return f"{tipo.capitalize()} de {fuente} guardado, {fecha}."
    return f"{tipo.capitalize()} guardado, {fecha}."


def _t_documentos_buscar(args: dict, result: str, autor: str) -> str:
    return "Aquí tienes lo que encontré."


def _t_medicacion_recordar(args: dict, result: str, autor: str) -> str:
    # El tool ya devuelve algo legible; lo lee directamente
    if result and "sin medicación" in result.lower():
        return "Hoy no hay medicación pendiente."
    return "Te aviso de la medicación pendiente."


def _t_cita_medica_anotar(args: dict, result: str, autor: str) -> str:
    quien = str(args.get("quien", "")).strip()
    esp = str(args.get("especialista", "")).strip()
    fecha = _fecha_legible(str(args.get("fecha", "hoy")))
    if quien and esp:
        return f"Cita anotada: {quien} con {esp}, {fecha}."
    return f"Cita médica anotada para {fecha}."


def _t_casa_mantenimiento_anotar(args: dict, result: str, autor: str) -> str:
    tarea = str(args.get("tarea", "")).strip() or "la tarea"
    return f"Apuntado en la casa: {tarea}."


def _t_claudio_recordar(args: dict, result: str, autor: str) -> str:
    return "Vale, lo recuerdo."


def _t_claudio_contexto(args: dict, result: str, autor: str) -> str:
    return "Aquí tienes lo que sé."


def _t_dia_capturar(args: dict, result: str, autor: str) -> str:
    return "Apuntado en notas."


def _t_dia_buscar(args: dict, result: str, autor: str) -> str:
    return "Te leo lo que encontré."


def _t_claudio_conversar(args: dict, result: str, autor: str) -> str:
    """Para conversación libre: extrae el texto del resultado de Haiku."""
    if result.startswith("💬 "):
        return result[2:].strip()
    return result.strip() or "Hecho."


_TEMPLATES = {
    # finanzas
    "gasto_anotar": _t_gasto_anotar,
    "gastos_resumen": _t_gastos_resumen,
    "recurrente_alertar": _t_recurrente_alertar,
    # familia
    "recordatorio_crear": _t_recordatorio_crear,
    "recordatorios_listar": _t_recordatorios_listar,
    "recordatorio_completar": _t_recordatorio_completar,
    "familia_cumpleanos_listar": _t_familia_cumpleanos_listar,
    # compras
    "lista_compras_añadir": _t_lista_compras_anadir,
    "lista_compras_anadir": _t_lista_compras_anadir,
    "lista_compras_ver": _t_lista_compras_ver,
    "lista_compras_completar": _t_lista_compras_completar,
    "despensa_estado": _t_despensa_estado,
    # menús
    "menu_sugerir": _t_menu_sugerir,
    "receta_guardar": _t_receta_guardar,
    # coche
    "coche_estado": _t_coche_estado,
    "coche_evento": _t_coche_evento,
    # documentos
    "documento_anotar": _t_documento_anotar,
    "documentos_buscar": _t_documentos_buscar,
    # salud
    "medicacion_recordar": _t_medicacion_recordar,
    "cita_medica_anotar": _t_cita_medica_anotar,
    # casa
    "casa_mantenimiento_anotar": _t_casa_mantenimiento_anotar,
    # identidad
    "claudio_recordar": _t_claudio_recordar,
    "claudio_contexto": _t_claudio_contexto,
    # fallback
    "dia_capturar": _t_dia_capturar,
    "dia_buscar": _t_dia_buscar,
    "claudio_conversar": _t_claudio_conversar,
}


def compose_voice_response(
    tool: str,
    args: dict,
    result: str,
    autor: str = "",
) -> str:
    """Construye la frase hablada que Claudio devuelve al usuario.

    Si el tool ejecutó con error (`result` empieza con '❌'), responde
    con disculpa breve para que el usuario sepa que algo falló sin
    necesidad de leer un mensaje técnico.
    """
    if result and result.lstrip().startswith("❌"):
        return "No he podido apuntarlo, lo dejo como nota."
    fn = _TEMPLATES.get(tool)
    if fn is None:
        return "Hecho."
    try:
        return fn(args or {}, result or "", autor or "")
    except Exception:
        return "Hecho."
