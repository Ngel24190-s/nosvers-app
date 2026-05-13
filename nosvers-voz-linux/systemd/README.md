# Instalación como servicio systemd user-mode

```bash
mkdir -p ~/.config/systemd/user
cp nosvers-voz.service ~/.config/systemd/user/

# Variable de entorno con ANTHROPIC_API_KEY (sólo para el servicio)
mkdir -p ~/.config/nosvers-voz
cat > ~/.config/nosvers-voz/env <<'EOF'
ANTHROPIC_API_KEY=sk-ant-...
EOF
chmod 600 ~/.config/nosvers-voz/env
# Descomentar la línea EnvironmentFile en nosvers-voz.service después

systemctl --user daemon-reload
systemctl --user enable --now nosvers-voz.service
journalctl --user -u nosvers-voz -f
```

## Lingering

Para que el servicio arranque sin sesión iniciada (e.g. tras reboot
sin que Angel haga login gráfico), habilita lingering como root:

```bash
sudo loginctl enable-linger $USER
```

## Reiniciar tras editar configuración

```bash
systemctl --user restart nosvers-voz.service
```

## Parar

```bash
systemctl --user stop nosvers-voz.service
systemctl --user disable nosvers-voz.service
```
