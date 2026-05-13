# nosvers-voz-linux

Cliente del asistente de voz personal NosVers para el ordenador Linux de casa
de Angel. Vive **en el PC de Angel, no en el VPS**.

## Funcionalidad

1. Detector de wake word **"Claudio"** (openWakeWord, modelo custom `models/claudio.onnx`).
2. STT local con `faster-whisper` (modelo `small`).
3. TTS local con Kokoro (`kokoro-onnx`), voces `ef_dora` (es) y `ff_siwis` (fr).
4. Cliente HTTPS contra `nosvers-mcp-2026` (Bearer JWT).
5. State machine de sesión: IDLE → DESPIERTA → ACTIVA → IDLE, con auto-cierre
   por inactividad y cooldown post-TTS.

## Instalación

```bash
git clone <repo> ~/nosvers-voz-linux
cd ~/nosvers-voz-linux
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Modelo wake word

1. Abrir `training/train_claudio.ipynb` en Google Colab Pro (GPU T4).
2. Ejecutar todas las celdas (~75-90 min).
3. Descargar `claudio.onnx` y copiarlo a `models/claudio.onnx`.

## Configuración

```bash
mkdir -p ~/.config/nosvers-voz
cp config.example.toml ~/.config/nosvers-voz/config.toml
$EDITOR ~/.config/nosvers-voz/config.toml   # rellenar mcp_url y mcp_token
```

Token MCP: emitirlo en el VPS con
```bash
ssh root@srv1313138.hstgr.cloud
sudo -u nosvers /home/nosvers/voz/scripts/issue_token.py --device pc-casa-angel
```

## Test de cada componente

```bash
# wake word
python3 -m nosvers_voz.wake --test

# STT
python3 -m nosvers_voz.stt_local --file sample.wav

# TTS
python3 -m nosvers_voz.tts_local --texto "Hola Angel"
```

## Servicio

```bash
mkdir -p ~/.config/systemd/user
cp systemd/nosvers-voz.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now nosvers-voz.service
journalctl --user -u nosvers-voz -f
```

## Logs

`~/.local/state/nosvers-voz/nosvers-voz.log` (rotado por logrotate si está
configurado, o limitado por tamaño internamente).
