"""
Tests para agents.agt07_diario.Agt07Diario (T036).

Cubre:
- día con notas → archivo resumen creado con frontmatter correcto.
- día vacío → no genera archivo y loguea "sin actividad".
- opt-in Telegram → llama a `notify()` (mockeado).
- conteo por autor / etiqueta presentes en el cuerpo si modelo no los añade.
- semana vacía → no genera archivo.
- semana con notas → archivo `YYYY-Www.md` correcto.
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def agt07(monkeypatch, vault_temporal):
    """Instancia Agt07Diario y redirige RESUMENES_DIR + prompts al vault temporal."""
    # Re-importar para captar paths del vault_temporal.
    from agents.agt07_diario import agt07_diario as mod

    monkeypatch.setattr(mod, "RESUMENES_DIR", vault_temporal.resumenes)

    # Prompts placeholders dentro del vault temporal.
    prompts_dir = vault_temporal.base / "prompts_agt07"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    (prompts_dir / "resumen_dia.md").write_text(
        "Sintetiza el día.", encoding="utf-8"
    )
    (prompts_dir / "resumen_semana.md").write_text(
        "Sintetiza la semana.", encoding="utf-8"
    )
    monkeypatch.setattr(mod, "PROMPT_DIR", prompts_dir)

    # Evitar dependencias de logging/Telegram del NosVersAgent base.
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    instance = mod.Agt07Diario()
    return instance, mod


def _escribir_notas_dia(vault, fecha: date, notas: list[dict]) -> None:
    """Helper: escribe `dia/YYYY-MM-DD.md` con varias notas."""
    from voz.vault_io import Nota, escribir_nota
    for n in notas:
        nota = Nota(
            ts=n["ts"],
            autor=n.get("autor", "angel"),
            etiqueta=n.get("etiqueta", "otro"),
            origen=n.get("origen", "voz_movil"),
            audio=None,
            clasificador_confianza=0.9,
            clasificador_modelo="test",
            texto=n["texto"],
        )
        escribir_nota(nota, fecha)


def test_resumen_dia_con_notas_crea_archivo(agt07, vault_temporal):
    agt, mod = agt07
    fecha = date(2026, 5, 13)
    _escribir_notas_dia(vault_temporal, fecha, [
        {"ts": "2026-05-13T08:00:00+02:00", "autor": "angel", "etiqueta": "nosvers",
         "texto": "Probar pack engrais."},
        {"ts": "2026-05-13T10:00:00+02:00", "autor": "angel", "etiqueta": "trabajo",
         "texto": "Cita con el cliente del desamiantage."},
        {"ts": "2026-05-13T18:00:00+02:00", "autor": "africa", "etiqueta": "familia",
         "texto": "Compra fruta para la nena."},
    ])

    with patch.object(mod.Agt07Diario, "_llamar_anthropic",
                      return_value="## Síntesis\n\n- Tres notas hoy.") as mock_api:
        fp = agt.resumen_dia(fecha)

    assert fp is not None
    assert fp.exists()
    contenido = fp.read_text(encoding="utf-8")
    assert "fecha: 2026-05-13" in contenido
    assert "notas_procesadas: 3" in contenido
    assert "notas_angel: 2" in contenido
    assert "notas_africa: 1" in contenido
    assert "Conteo por autor" in contenido           # se añade si modelo no lo trae
    assert "Distribución de etiquetas" in contenido  # ídem
    assert mock_api.call_count == 1


def test_resumen_dia_vacio_no_crea_archivo(agt07, vault_temporal, caplog):
    agt, mod = agt07
    fecha = date(2026, 5, 12)
    with caplog.at_level("INFO"):
        fp = agt.resumen_dia(fecha)
    assert fp is None
    assert not (vault_temporal.resumenes / f"{fecha.isoformat()}.md").exists()
    # No llamamos al modelo cuando el día está vacío
    assert "sin actividad" in caplog.text.lower() or any(
        "sin actividad" in r.message.lower() for r in caplog.records
    )


def test_resumen_dia_modelo_dice_sin_actividad(agt07, vault_temporal):
    agt, mod = agt07
    fecha = date(2026, 5, 11)
    _escribir_notas_dia(vault_temporal, fecha, [
        {"ts": "2026-05-11T20:00:00+02:00", "texto": "ruido"},
    ])
    with patch.object(mod.Agt07Diario, "_llamar_anthropic",
                      return_value="SIN_ACTIVIDAD"):
        fp = agt.resumen_dia(fecha)
    assert fp is None


def test_resumen_dia_notifica_telegram_opt_in(agt07, vault_temporal):
    agt, mod = agt07
    fecha = date(2026, 5, 10)
    _escribir_notas_dia(vault_temporal, fecha, [
        {"ts": "2026-05-10T09:00:00+02:00", "texto": "Hola"},
    ])
    with patch.object(mod.Agt07Diario, "_llamar_anthropic",
                      return_value="## Sintesis\n\nUna nota."), \
         patch.object(mod.Agt07Diario, "notify") as mock_notify:
        agt.resumen_dia(fecha, notificar_telegram=True)
    assert mock_notify.called
    assert "2026-05-10" in mock_notify.call_args.args[0]


def test_resumen_dia_sin_telegram_no_notifica(agt07, vault_temporal):
    agt, mod = agt07
    fecha = date(2026, 5, 9)
    _escribir_notas_dia(vault_temporal, fecha, [
        {"ts": "2026-05-09T09:00:00+02:00", "texto": "Hola"},
    ])
    with patch.object(mod.Agt07Diario, "_llamar_anthropic",
                      return_value="Resumen ok."), \
         patch.object(mod.Agt07Diario, "notify") as mock_notify:
        agt.resumen_dia(fecha, notificar_telegram=False)
    mock_notify.assert_not_called()


def test_resumen_semana_vacia_no_crea_archivo(agt07, vault_temporal):
    agt, _ = agt07
    fecha_fin = date(2026, 5, 13)
    fp = agt.resumen_semana(fecha_fin)
    assert fp is None


def test_resumen_semana_con_notas_genera_iso_week(agt07, vault_temporal):
    agt, mod = agt07
    # 2026-05-13 es miércoles → ISO week 20 del año 2026.
    fecha_fin = date(2026, 5, 13)
    _escribir_notas_dia(vault_temporal, fecha_fin, [
        {"ts": "2026-05-13T09:00:00+02:00", "texto": "Día x"},
    ])
    _escribir_notas_dia(vault_temporal, date(2026, 5, 12), [
        {"ts": "2026-05-12T09:00:00+02:00", "texto": "Día y"},
    ])
    with patch.object(mod.Agt07Diario, "_llamar_anthropic",
                      return_value="## Resumen semanal\n\nDos días."):
        fp = agt.resumen_semana(fecha_fin)
    assert fp is not None
    assert fp.name == "2026-W20.md"
    contenido = fp.read_text(encoding="utf-8")
    assert "semana_iso: 2026-W20" in contenido
    assert "dias_con_actividad: 2" in contenido
