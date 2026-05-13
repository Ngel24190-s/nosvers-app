# FINAL PUSH — Rematar las 17 tareas pendientes

Estado actual confirmado por Opus móvil (revisión 2026-05-13 10:25 UTC):
- Refactor multi-usuario R1-R9: 100% ✓
- Tests: 65/65 passing
- Pool común vault: ✓ con migración hecha
- PWA, voz-linux, agente, tools MCP: código completo

## Instrucciones

Termina las 17 pendientes (T056-T074) EXCEPTO con estas excepciones:

### Excepción 1: T056 — Entrenar modelo wake word Claudio en Colab

**NO PUEDES hacer esto desde el VPS**. Requiere que Angel abra Google Colab manualmente, ejecute el notebook `nosvers-voz-linux/training/train_claudio.ipynb`, descargue el `.onnx` resultante, y lo suba al VPS en `nosvers-voz-linux/models/claudio.onnx`.

Marca T056 como `[~] BLOCKED_HUMAN` y continúa. Sigue con T057+ asumiendo que el modelo NO existe todavía. Cualquier tarea que dependa del modelo, márcala como `[~] PENDING_T056` y continúa con las independientes.

### Excepción 2: Ajuste pequeño PWA — Onboarding multi-usuario

Añade un paso de onboarding en `public_html/voz/index.html`:
- Si NO hay `nosvers_voz_device` en localStorage al primer arranque → mostrar pantalla con dos botones grandes: "Soy Angel" / "Soy África"
- Al hacer clic, setea `nosvers_voz_device` a `movil-angel` o `movil-africa`
- Luego pide el token JWT correspondiente
- Esto evita que África use por defecto la identidad de Angel

Esto es una tarea nueva: márcala como **T075** y mételo en el flujo.

### Bug vigilado: telegram_enviar

Si CUALQUIER llamada al MCP se cuelga más de **30 segundos**, abortala con Ctrl+C interno y reintenta. NO esperes 9 horas como anoche. Si pasa dos veces seguidas, salta esa tarea y continúa, anotándolo en tasks.md como `[!] MCP_STALL_RETRY_AFTER`.

### Al terminar

Telegram a Angel via `telegram_enviar` con:
- Resumen: tareas hechas / bloqueadas
- Pasos manuales pendientes (entrenamiento Colab)
- Comando para Angel: cómo desplegar el cliente voz-linux en su ordenador casa
- Próximos pasos: revisión final por Opus móvil

## Después de terminar

NO empezar el proyecto 002 (second-brain-dashboard) hasta que Angel valide y desbloquee. El BRIEF del 002 ya está en `/home/nosvers/specs/second-brain-dashboard/BRIEF.md` para referencia tuya, no lo toques.

---
*Instrucciones preparadas por Claude Opus 4.7 (sesión móvil), 2026-05-13 10:30 UTC*
