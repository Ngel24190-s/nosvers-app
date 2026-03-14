# drive-config
*2026-03-14 12:29*

# Google Drive NosVers Media — Configuración
*Carpetas creadas por Nerea · 2026-03-14*

## IDs de carpetas

| Carpeta | ID | URL |
|---|---|---|
| NosVers Media (raíz) | `1U3gQVGIH8j-_ARJv0Fqs8IQPlMrG0VDv` | https://drive.google.com/drive/folders/1U3gQVGIH8j-_ARJv0Fqs8IQPlMrG0VDv |
| instagram | `1SVQk3yGYhQztjISmSBK2wKNSl-crsLHk` | https://drive.google.com/drive/folders/1SVQk3yGYhQztjISmSBK2wKNSl-crsLHk |
| Vers de compost | `1_ZkuC6NLAx9iLMQFomShXr-vACBpzD-F` | https://drive.google.com/drive/folders/1_ZkuC6NLAx9iLMQFomShXr-vACBpzD-F |
| Huerto | `1jHAay7I5rA267DUHAhwxZNPQw6-SYtGz` | https://drive.google.com/drive/folders/1jHAay7I5rA267DUHAhwxZNPQw6-SYtGz |
| General | `1-coq2zW5-KyMD5GHfV_Ys2M_1spcDkr5` | https://drive.google.com/drive/folders/1-coq2zW5-KyMD5GHfV_Ys2M_1spcDkr5 |

## Uso por agente

- **AGT-01 Visual**: lee todas las carpetas, procesa fotos brutas
- **AGT-02 Instagram**: lee carpeta `instagram` para posts
- **AGT-04 SEO**: lee carpeta `General` para imágenes del blog
- **Web WordPress**: las fotos procesadas se suben via WP Media API

## Cómo subir fotos a Drive (África y Angel)
1. Abrir Google Drive en el móvil
2. Ir a "NosVers Media" → subcarpeta correspondiente
3. Subir foto directamente desde la cámara o galería
4. El agente AGT-01 la detecta en su próxima ejecución

## Variables de entorno necesarias en VPS (.env)
```
DRIVE_FOLDER_ROOT=1U3gQVGIH8j-_ARJv0Fqs8IQPlMrG0VDv
DRIVE_FOLDER_INSTAGRAM=1SVQk3yGYhQztjISmSBK2wKNSl-crsLHk
DRIVE_FOLDER_VERS=1_ZkuC6NLAx9iLMQFomShXr-vACBpzD-F
DRIVE_FOLDER_HUERTO=1jHAay7I5rA267DUHAhwxZNPQw6-SYtGz
DRIVE_FOLDER_GENERAL=1-coq2zW5-KyMD5GHfV_Ys2M_1spcDkr5
```
