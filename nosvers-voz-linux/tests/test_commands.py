"""Tests del parser de comandos por voz. Sin deps de audio."""

import pytest

from nosvers_voz.commands import parse_comando


@pytest.mark.parametrize(
    "texto,tipo_esperado",
    [
        ("Habla más rápido por favor", "rapido"),
        ("habla rápido", "rapido"),
        ("Habla más despacio", "despacio"),
        ("habla más lento", "despacio"),
        ("cambia a francés", "fr"),
        ("a francés", "fr"),
        ("pasa a francés", "fr"),
        ("cambia a español", "es"),
        ("cambia a castellano", "es"),
        ("cierra sesión", "cierra"),
        ("cierra la sesión", "cierra"),
        ("termina la sesión", "cierra"),
        ("¿cómo está el clima?", "chat"),
        ("dime los pendientes", "chat"),
    ],
)
def test_parse_comando_tipo(texto: str, tipo_esperado: str) -> None:
    tipo, _ = parse_comando(texto)
    assert tipo == tipo_esperado


@pytest.mark.parametrize(
    "texto,payload_esperado",
    [
        ("captura: comprar bombillas led", "comprar bombillas led"),
        ("Captura comprar bombillas led", "comprar bombillas led"),
        ("anota llamar a África mañana", "llamar a África mañana"),
        ("toma nota pedir fotos a África", "pedir fotos a África"),
    ],
)
def test_parse_comando_captura_payload(texto: str, payload_esperado: str) -> None:
    tipo, payload = parse_comando(texto)
    assert tipo == "captura"
    assert payload == payload_esperado


def test_parse_comando_chat_payload() -> None:
    tipo, payload = parse_comando("  hola Claude   ")
    assert tipo == "chat"
    assert payload == "hola Claude"
