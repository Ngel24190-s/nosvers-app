#!/bin/bash
set -e

# ============================================================
#  NosVers · Script de despliegue VPS
#  Ejecutar como root en el VPS:
#    bash /home/nosvers/scripts/deploy.sh
# ============================================================

echo "🌿 NosVers · Despliegue VPS"
echo "============================"
echo ""

NOSVERS="/home/nosvers"
VAULT="$NOSVERS/public_html/knowledge_base"

# ── 1. Estructura de directorios ──────────────────────────
echo "📁 Creando estructura de directorios..."

mkdir -p "$NOSVERS"/{public_html,bot,agents,uploads/visuels,uploads/africa,uploads/pdfs}
mkdir -p "$VAULT"/{contexto,agentes,operaciones,vers,compost,animaux,huerto,estudios,club}

echo "   ✅ Directorios creados"

# ── 2. Copiar archivos del repo ──────────────────────────
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"

if [ "$(realpath "$REPO_DIR")" = "$(realpath "$NOSVERS")" ]; then
    echo "   ℹ️  Repo y destino son el mismo directorio — copiando solo a subdirectorios"
    # Solo copiar archivos que van a subdirectorios distintos del origen
    cp "$REPO_DIR/api.php" "$NOSVERS/public_html/" 2>/dev/null || true
    cp "$REPO_DIR/kb_search.php" "$NOSVERS/public_html/" 2>/dev/null || true
    cp "$REPO_DIR/agent_memory.json" "$NOSVERS/public_html/" 2>/dev/null || true
    cp "$REPO_DIR/index.html" "$NOSVERS/public_html/" 2>/dev/null || true
    echo "   ✅ public_html/ (archivos copiados desde raíz)"
    if [ -d "$REPO_DIR/vault_init" ]; then
        cp -rn "$REPO_DIR/vault_init/"* "$VAULT/" 2>/dev/null || true
        echo "   ✅ Vault content inicial"
    fi
else
    echo "📦 Copiando archivos desde repo ($REPO_DIR)..."

    # Bot
    cp "$REPO_DIR/bot/bot.py" "$NOSVERS/bot/"
    echo "   ✅ bot/bot.py"

    # Agentes
    cp "$REPO_DIR/agents/"*.py "$NOSVERS/agents/"
    echo "   ✅ agents/*.py"

    # App granja (api.php y relacionados)
    cp "$REPO_DIR/api.php" "$NOSVERS/public_html/"
    cp "$REPO_DIR/kb_search.php" "$NOSVERS/public_html/" 2>/dev/null || true
    cp "$REPO_DIR/agent_memory.json" "$NOSVERS/public_html/" 2>/dev/null || true
    cp "$REPO_DIR/index.html" "$NOSVERS/public_html/" 2>/dev/null || true
    echo "   ✅ public_html/"

    # Vault content inicial
    if [ -d "$REPO_DIR/vault_init" ]; then
        cp -rn "$REPO_DIR/vault_init/"* "$VAULT/" 2>/dev/null || true
        echo "   ✅ Vault content inicial"
    fi
fi

# ── 3. Instalar dependencias del sistema ──────────────────
echo "📦 Instalando dependencias del sistema..."

apt-get update -qq
apt-get install -y -qq python3-pip python3-venv git curl > /dev/null 2>&1
echo "   ✅ python3, pip, venv, git, curl"

# ── 4. Entorno virtual Python ─────────────────────────────
echo "🐍 Configurando entorno virtual Python..."

if [ ! -d "$NOSVERS/venv" ]; then
    python3 -m venv "$NOSVERS/venv"
    echo "   Creado venv en $NOSVERS/venv"
fi

"$NOSVERS/venv/bin/pip" install -q python-telegram-bot requests python-dotenv anthropic schedule
echo "   ✅ Dependencias Python instaladas"

# ── 5. Archivo .env ───────────────────────────────────────
if [ ! -f "$NOSVERS/.env" ]; then
    echo "⚙️  Creando .env desde template..."
    cp "$REPO_DIR/.env.example" "$NOSVERS/.env"
    chmod 600 "$NOSVERS/.env"
    echo "   ⚠️  EDITA $NOSVERS/.env con los valores reales"
    echo "   Comando: nano $NOSVERS/.env"
else
    echo "   ✅ .env ya existe (no se sobreescribe)"
fi

# ── 6. Servicio systemd para el bot ──────────────────────
echo "🤖 Configurando servicio Bot Telegram..."

cp "$REPO_DIR/bot/nosvers-bot.service" /etc/systemd/system/nosvers-bot.service
systemctl daemon-reload
systemctl enable nosvers-bot

# No arrancar si no hay token configurado
if grep -q "TELEGRAM_TOKEN=\$\|TELEGRAM_TOKEN=$" "$NOSVERS/.env" 2>/dev/null; then
    echo "   ⚠️  Bot instalado pero NO arrancado — falta TELEGRAM_TOKEN en .env"
else
    systemctl restart nosvers-bot
    echo "   ✅ Bot arrancado"
fi

# ── 7. Crontabs ──────────────────────────────────────────
echo "⏰ Configurando crontabs..."

VENV_PY="$NOSVERS/venv/bin/python3"

# Crear crontab (preservar existentes)
EXISTING_CRON=$(crontab -l 2>/dev/null || true)

# Solo añadir si no existen ya
if ! echo "$EXISTING_CRON" | grep -q "orchestrator.py"; then
    (echo "$EXISTING_CRON"
     echo ""
     echo "# === NosVers Agents ==="
     echo "0 * * * * $VENV_PY $NOSVERS/agents/orchestrator.py >> $NOSVERS/agents/orchestrator.log 2>&1"
     echo "0 10 * * 0 $VENV_PY $NOSVERS/agents/agt02_instagram.py >> $NOSVERS/agents/agt02.log 2>&1"
     echo "0 7 * * 1 $VENV_PY $NOSVERS/agents/agt04_seo.py >> $NOSVERS/agents/agt04.log 2>&1"
     echo "0 */6 * * * $VENV_PY $NOSVERS/agents/agt05_africa.py >> $NOSVERS/agents/agt05.log 2>&1"
    ) | crontab -
    echo "   ✅ Crontabs instalados"
else
    echo "   ✅ Crontabs ya existentes (no duplicados)"
fi

# ── 8. Permisos ──────────────────────────────────────────
echo "🔒 Ajustando permisos..."

chmod 755 "$VAULT" -R
chmod 755 "$NOSVERS/agents" -R
chmod 755 "$NOSVERS/bot" -R
chmod 600 "$NOSVERS/.env"

echo "   ✅ Permisos configurados"

# ── 9. Resumen ───────────────────────────────────────────
echo ""
echo "============================================"
echo "🌿 NosVers · Despliegue completado"
echo "============================================"
echo ""
echo "Estructura:"
echo "  $NOSVERS/"
echo "  ├── public_html/     (app granja)"
echo "  │   └── knowledge_base/ (vault: $(ls "$VAULT" | wc -l) categorías)"
echo "  ├── bot/             (Telegram bot)"
echo "  ├── agents/          ($(ls "$NOSVERS/agents/"*.py 2>/dev/null | wc -l) agentes)"
echo "  ├── uploads/         (fotos + PDFs)"
echo "  ├── venv/            (Python)"
echo "  └── .env             (credenciales)"
echo ""
echo "PASOS SIGUIENTES:"
echo "  1. Editar credenciales: nano $NOSVERS/.env"
echo "  2. Regenerar token Telegram via @BotFather"
echo "  3. Arrancar bot: systemctl restart nosvers-bot"
echo "  4. Verificar: systemctl status nosvers-bot"
echo ""
