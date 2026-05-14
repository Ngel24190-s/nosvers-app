# salud/

Citas médicas, medicación, síntomas, chequeos. Dominio sensible — Claudio nunca
diagnostica, solo recuerda y sugiere "hablar con médico".

## Subcarpetas

- `citas/` — un `.md` por cita: `YYYY-MM-DD-quien-especialista.md`.
- `sintomas/` — diario por mes: `sintomas/YYYY-MM.md`.

## Archivos raíz

- `medicacion.yaml` — pautas activas. Alimenta `medicacion_recordar()`.
- `chequeos.md` — historial de chequeos generales.

## Tools MCP

- `medicacion_recordar`, `cita_medica_anotar`

## Privacidad

**Máxima sensibilidad**. Tools requieren `autor` explícito, sin default.
No se indexa por `documentos_buscar`. No se loguea contenido en JSONL.
