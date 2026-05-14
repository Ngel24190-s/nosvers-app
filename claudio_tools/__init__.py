"""Claudio Jarvis · Fase 1 · subpackage de tools MCP familiares.

Cada módulo expone funciones síncronas que reciben argumentos primitivos
(str, int, float, bool) y devuelven `str` con resumen humano. Pensado para
envolverse en `@mcp.tool()` desde `mcp_server.py`, o para ser llamado
directamente desde el bot Telegram, automations runner, o tests.

Convenciones:
- Autor: `angel | africa | compartido | bris` (validado en common.normalize_author)
- Logging: cada llamada deja una línea JSONL en `claudio/logs/YYYY-MM-DD.jsonl`
- Vault path: configurable via env `VAULT_PATH` (default /home/nosvers/public_html/knowledge_base)
"""

__version__ = "0.1.0"
