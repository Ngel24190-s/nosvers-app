#!/bin/bash
# Envía una notificación pendiente al bot de Telegram
# Uso: bash /home/nosvers/bot/notify.sh "mensaje aquí"
NOTIF_DIR="/home/nosvers/bot/notifications"
mkdir -p "$NOTIF_DIR"
TIMESTAMP=$(date +%s%N)
echo "$1" > "$NOTIF_DIR/$TIMESTAMP.txt"
echo "Notificación guardada. Se entregará cuando Angel interactúe con el bot."
