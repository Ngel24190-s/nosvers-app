# agt07_diario — Agente de resúmenes del cuaderno de Angel

Lee las notas dictadas y sintetiza:

- **Diario** (Haiku): cada noche 23:30 Europe/Paris.
- **Semanal** (Opus): cada domingo 22:00, mirando los 7 días previos.

## Uso

```bash
# Resumen del día de hoy
python3 /home/nosvers/agents/agt07_diario/agt07_diario.py --dia

# Día concreto (re-procesar histórico)
python3 .../agt07_diario.py --dia --fecha 2026-05-12

# Semanal (toma los 7 días hasta --fecha inclusive; default hoy)
python3 .../agt07_diario.py --semana

# Notificar a Angel por Telegram
python3 .../agt07_diario.py --dia --notificar-telegram
# (o exportar TELEGRAM_NOTIFY_RESUMENES=1 para el cron)
```

## Salida

- Diario → `knowledge_base/dia/resumenes/YYYY-MM-DD.md`
- Semanal → `knowledge_base/dia/resumenes/YYYY-Www.md` (ISO week)

Pool común multi-usuario (BRIEF §14): los resúmenes agrupan por autor
(Angel / África) y por etiqueta. Se generan a partir de
`knowledge_base/dia/YYYY-MM-DD.md` (mismo archivo para ambos).

Si no hay notas en el rango, NO crea archivo (per FR-022). El cron registra
el evento en `/home/nosvers/logs/agt07_diario.log`.

## Cron (instalado en `/etc/cron.d/nosvers-voz`)

```cron
30 23 * * *  nosvers  /usr/bin/python3 /home/nosvers/agents/agt07_diario/agt07_diario.py --dia
0  22 * * 0  nosvers  /usr/bin/python3 /home/nosvers/agents/agt07_diario/agt07_diario.py --semana
0   3 * * *  nosvers  /usr/bin/python3 /home/nosvers/voz/scripts/purge_audio.py
```

## Prompts

Editables en `prompts/`:
- `resumen_dia.md`
- `resumen_semana.md`

Cambios surten efecto sin redeploy (se cargan en cada ejecución).

## Troubleshooting

- **No genera salida**: revisar `logs/agt07_diario.log`. Causas típicas:
  `ANTHROPIC_API_KEY` ausente, prompt mal-formateado, día con 0 notas.
- **Notificación Telegram no llega**: `TELEGRAM_TOKEN` y `ANGEL_CHAT_ID`
  deben estar en `/home/nosvers/.env`.
- **Resumen incompleto / cortado**: bump `max_tokens` en `_llamar_anthropic`.
