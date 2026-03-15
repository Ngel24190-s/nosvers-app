#!/usr/bin/env python3
"""
NosVers · AGT-02 Instagram
Genera 5 posts/semana con copy completo en francés.
Guarda en vault para aprobación de Angel.
Publica SOLO cuando se llama con --publish o cuando un post está marcado como APPROVED.

Cron generación:  domingos 10h — 0 10 * * 0
Cron publicación: diaria 8h  — 0 8 * * *  (comprueba aprobados y publica)

Uso:
    python3 agt02_instagram.py              → genera posts semana siguiente
    python3 agt02_instagram.py --publish    → publica posts marcados como APPROVED en vault
"""
import sys
import os
import json
import re
import time
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, '/home/nosvers/agents')
from agent_base import NosVersAgent
from dotenv import load_dotenv

load_dotenv('/home/nosvers/.env')

INSTAGRAM_USER   = os.getenv('INSTAGRAM_USER', '')
INSTAGRAM_PASS   = os.getenv('INSTAGRAM_PASS', '')
SESSION_FILE     = Path('/home/nosvers/agents/.instagram_session.json')
APPROVED_MARKER  = 'STATUS: APPROVED'
PUBLISHED_MARKER = 'STATUS: PUBLISHED'

PERSONALITY = """PERSONALIDAD — AGT-02 "La Voz"
Conoces la audiencia de NosVers como si los hubieras criado.
El jardinero francés de 35 años no quiere que le vendan — quiere aprender.
Escribes en francés con la naturalidad de quien ha vivido en la tierra.
Tus captions empiezan siempre con una observación concreta o pregunta.
Nunca "Découvrez" ni "Profitez". El CTA siempre es uno solo y suave.
Tono: Editorial. Cercano. Educativo sin ser académico.
Reglas: Nunca "achetez maintenant". Nunca más de 1 CTA por post.
Nunca en inglés. Mínimo 20 hashtags. Nunca publicar sin aprobación de Angel.
REGLA: Nunca publiques sin aprobación de Angel."""


class InstagramAgent(NosVersAgent):

    DIAS  = {0: 'Lunes 18h', 2: 'Miércoles 19h', 3: 'Jueves 18h', 4: 'Viernes 18h', 6: 'Domingo 11h'}
    TIPOS = {
        0: '🏡 Ferme/Présentation',
        2: '📚 Éducatif (carrousel)',
        3: '🎬 Reel 15-30s',
        4: '🌺 Humain/África',
        6: '🎯 Produit/Club',
    }

    def __init__(self) -> None:
        super().__init__('agt02_instagram', '📱', PERSONALITY)

    # ── INSTAGRAPI SESSION ────────────────────────────────────────────────────

    def _get_client(self):
        """
        Crea y devuelve un cliente instagrapi autenticado.

        Intenta cargar sesión persistente desde disco para evitar login repetido.
        Guarda sesión nueva si el login es exitoso.

        Returns:
            instagrapi.Client: cliente listo para uso.

        Raises:
            RuntimeError: si las credenciales no están configuradas o el login falla.
        """
        from instagrapi import Client
        from instagrapi.exceptions import (
            LoginRequired,
            TwoFactorRequired,
            BadPassword,
            ChallengeRequired,
        )

        if not INSTAGRAM_USER or INSTAGRAM_USER == 'PENDING_ANGEL_CONFIG':
            raise RuntimeError(
                "INSTAGRAM_USER no configurado en /home/nosvers/.env"
            )
        if not INSTAGRAM_PASS or INSTAGRAM_PASS == 'PENDING_ANGEL_CONFIG':
            raise RuntimeError(
                "INSTAGRAM_PASS no configurado en /home/nosvers/.env"
            )

        cl = Client()
        cl.delay_range = [1, 3]  # delay humanizado entre requests

        # Intentar cargar sesión guardada
        if SESSION_FILE.exists():
            try:
                self.log.info("Cargando sesión Instagram desde disco")
                cl.load_settings(str(SESSION_FILE))
                cl.login(INSTAGRAM_USER, INSTAGRAM_PASS)
                cl.get_timeline_feed()          # valida que la sesión siga activa
                self.log.info("Sesión Instagram reutilizada correctamente")
                return cl
            except LoginRequired:
                self.log.warning("Sesión caducada — realizando login completo")
                cl = Client()
                cl.delay_range = [1, 3]
            except Exception as e:
                self.log.warning(f"Error cargando sesión guardada: {e} — login completo")
                cl = Client()
                cl.delay_range = [1, 3]

        # Login completo
        try:
            self.log.info(f"Login Instagram como {INSTAGRAM_USER}")
            cl.login(INSTAGRAM_USER, INSTAGRAM_PASS)
        except TwoFactorRequired:
            # 2FA: instagrapi puede gestionar TOTP automáticamente si se proporciona
            # la clave TOTP. Por ahora notificamos a Angel para intervención manual.
            self.log.error("Instagram requiere 2FA — acción manual necesaria")
            self.notify(
                "Instagram requiere verificación 2FA.\n"
                "Por favor desactiva 2FA temporalmente o configura TOTP en el bot."
            )
            raise RuntimeError("2FA requerida — ver notificación Telegram")
        except ChallengeRequired:
            self.log.error("Instagram lanzó challenge (captcha/email)")
            self.notify(
                "Instagram lanzó un challenge de seguridad.\n"
                "Accede manualmente a la cuenta y acepta el challenge, luego reintenta."
            )
            raise RuntimeError("Challenge de Instagram requerido — ver notificación Telegram")
        except BadPassword:
            raise RuntimeError("Contraseña de Instagram incorrecta — revisa INSTAGRAM_PASS en .env")
        except Exception as e:
            raise RuntimeError(f"Error de login en Instagram: {e}")

        # Guardar sesión para reutilizar
        SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
        cl.dump_settings(str(SESSION_FILE))
        self.log.info(f"Sesión Instagram guardada en {SESSION_FILE}")

        return cl

    # ── PUBLICACIÓN ───────────────────────────────────────────────────────────

    def publish_post(self, image_path: str, caption: str) -> str:
        """
        Publica una foto en Instagram con su caption.

        Args:
            image_path: Ruta absoluta a la imagen (JPG/PNG, mínimo 320px).
            caption: Texto completo del post incluyendo hashtags.

        Returns:
            URL pública del post publicado (https://www.instagram.com/p/CODE/).

        Raises:
            FileNotFoundError: si la imagen no existe.
            RuntimeError: si el login falla o la subida falla.
        """
        img = Path(image_path)
        if not img.exists():
            raise FileNotFoundError(f"Imagen no encontrada: {image_path}")

        self.log.info(f"Publicando en Instagram: {img.name}")
        cl = self._get_client()

        try:
            media = cl.photo_upload(
                path=str(img),
                caption=caption,
            )
            post_url = f"https://www.instagram.com/p/{media.code}/"
            self.log.info(f"Post publicado: {post_url}")

            # Guardar sesión actualizada
            cl.dump_settings(str(SESSION_FILE))
            return post_url

        except Exception as e:
            self.log.error(f"Error subiendo foto a Instagram: {e}")
            raise RuntimeError(f"Error publicando en Instagram: {e}") from e

    # ── VAULT APPROVED POSTS ──────────────────────────────────────────────────

    def _parse_approved_posts(self, vault_content: str) -> list[dict]:
        """
        Extrae posts marcados como APPROVED del contenido vault.

        El formato esperado en vault es que cada bloque de post contenga
        una línea 'STATUS: APPROVED' y una 'IMAGE: /ruta/absoluta.jpg'.

        Args:
            vault_content: Contenido completo del archivo _aprobados.md.

        Returns:
            Lista de dicts con claves 'caption', 'image', 'block_text'.
        """
        approved: list[dict] = []
        # Separamos por bloques delimitados por ---POST o lineas ---
        blocks = re.split(r'\n---+\n', vault_content)

        for block in blocks:
            if APPROVED_MARKER not in block:
                continue
            if PUBLISHED_MARKER in block:
                continue  # ya publicado, ignorar

            # Extraer imagen
            image_match = re.search(r'^IMAGE:\s*(.+)$', block, re.MULTILINE)
            if not image_match:
                self.log.warning("Bloque APPROVED sin línea IMAGE: — ignorando")
                continue

            image_path = image_match.group(1).strip()

            # Extraer caption: todo entre CAPTION: y HASHTAGS: (o hasta fin)
            caption_match = re.search(
                r'CAPTION:\s*\n(.*?)(?=\nHASHTAGS:|\nSTATUS:|\Z)',
                block, re.DOTALL
            )
            hashtag_match = re.search(r'HASHTAGS:\s*\n(.+?)(?=\nSTATUS:|\Z)', block, re.DOTALL)

            caption_text = caption_match.group(1).strip() if caption_match else ''
            hashtag_text = hashtag_match.group(1).strip() if hashtag_match else ''

            full_caption = f"{caption_text}\n\n{hashtag_text}".strip() if hashtag_text else caption_text

            if not full_caption:
                self.log.warning("Bloque APPROVED sin caption — ignorando")
                continue

            approved.append({
                'image': image_path,
                'caption': full_caption,
                'block_text': block.strip(),
            })

        return approved

    def _mark_as_published(self, post_url: str, block_text: str) -> None:
        """
        Reemplaza STATUS: APPROVED → STATUS: PUBLISHED en el archivo de aprobados
        y añade la URL pública del post.

        Args:
            post_url: URL del post publicado en Instagram.
            block_text: Texto exacto del bloque en vault para ubicarlo.
        """
        fp = self.vault / 'agentes' / 'agt02_instagram' / '_aprobados.md'
        if not fp.exists():
            return
        content = fp.read_text(encoding='utf-8')
        ts = datetime.now().strftime('%Y-%m-%d %H:%M')
        updated_block = block_text.replace(
            APPROVED_MARKER,
            f"{PUBLISHED_MARKER}\nPUBLISHED_URL: {post_url}\nPUBLISHED_AT: {ts}"
        )
        content = content.replace(block_text, updated_block)
        fp.write_text(content, encoding='utf-8')
        self.log.info(f"Post marcado como PUBLISHED en vault: {post_url}")

    def publish_approved(self) -> int:
        """
        Lee posts marcados como APPROVED en vault y los publica en Instagram.

        Lee de: agentes/agt02_instagram/_aprobados.md
        Cada post necesita:
            STATUS: APPROVED
            IMAGE: /ruta/absoluta/a/imagen.jpg
            CAPTION: (texto)
            HASHTAGS: (hashtags)

        Nunca publica automáticamente. Solo ejecutar con --publish.

        Returns:
            Número de posts publicados exitosamente.
        """
        self.log.info("Buscando posts aprobados en vault")
        content = self.vault_read('agentes/agt02_instagram', '_aprobados')

        if not content:
            self.log.info("No hay archivo _aprobados.md en vault")
            self.notify("No hay posts aprobados pendientes de publicación.")
            return 0

        approved_posts = self._parse_approved_posts(content)

        if not approved_posts:
            self.log.info("No hay posts marcados como APPROVED pendientes")
            self.notify("No hay posts con STATUS: APPROVED pendientes de publicación.")
            return 0

        self.log.info(f"Encontrados {len(approved_posts)} posts aprobados para publicar")
        published_count = 0

        for i, post in enumerate(approved_posts):
            try:
                self.log.info(f"Publicando post {i+1}/{len(approved_posts)}: {post['image']}")
                post_url = self.publish_post(post['image'], post['caption'])
                self._mark_as_published(post_url, post['block_text'])
                self.notify(
                    f"Post publicado en Instagram\n{post_url}\n\n"
                    f"Caption preview:\n{post['caption'][:200]}..."
                )
                published_count += 1

                # Espera entre posts para no estresar la API de Instagram
                if i < len(approved_posts) - 1:
                    self.log.info("Esperando 30s entre publicaciones")
                    time.sleep(30)

            except FileNotFoundError as e:
                self.log.error(f"Imagen no encontrada para post {i+1}: {e}")
                self.notify(f"Error al publicar post {i+1}: imagen no encontrada.\n{e}")
            except RuntimeError as e:
                self.log.error(f"Error publicando post {i+1}: {e}")
                self.notify(f"Error publicando post {i+1} en Instagram:\n{e}")
                # Si es error de login/challenge, abortamos el resto
                if 'login' in str(e).lower() or 'challenge' in str(e).lower() or '2FA' in str(e):
                    self.log.error("Error de autenticación — abortando publicación")
                    break

        self.log.info(f"Publicación completada: {published_count}/{len(approved_posts)} posts")
        self.save_memory(
            f"Publicados {published_count} posts Instagram — {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        return published_count

    # ── GENERACIÓN DE POSTS ───────────────────────────────────────────────────

    def check_triggers(self) -> list:
        triggers = []
        # Verificar si hay fotos de África disponibles
        africa_memoria = self.vault_read('agentes/agt05_africa', '_memoria')
        if 'fotos' in africa_memoria.lower() or 'photos' in africa_memoria.lower():
            triggers.append('fotos_disponibles')
        # Verificar si faltan posts esta semana
        resultado = self.vault_read('agentes/agt02_instagram', '_resultado')
        if not resultado or 'semana' not in resultado.lower():
            triggers.append('posts_pendientes')
        return triggers

    def generar_posts(self) -> str:
        """
        Genera 5 posts usando Claude con contexto completo de la ferme.

        Returns:
            String con los 5 posts formateados listos para vault.
        """
        contexto_identidad = self.vault_read('contexto', 'nosvers-identidad')
        contexto_africa    = self.vault_read('agentes/agt05_africa', '_memoria')
        memoria_propia     = self.get_memory()

        semana_num = datetime.now().isocalendar()[1]
        mes        = datetime.now().strftime('%B')

        prompt = f"""Genera 5 posts Instagram completos para @nosvers.ferme para la semana que viene.

CONTEXTO DE LA FERME:
{contexto_identidad[:500]}

CONOCIMIENTO DE ÁFRICA (usar su voz):
{contexto_africa[:400]}

HISTORIAL POSTS ANTERIORES:
{memoria_propia[-300:] if memoria_propia else 'Primeros posts'}

REQUISITOS:
- Semana {semana_num}, mes: {mes}
- Idioma: FRANCÉS siempre
- 80% éducatif, 20% produit
- CTA único por post: "lien en bio"
- 28 hashtags mix (micro/medio/macro)
- Cada post: caption completa + hashtags + horario + tipo de visual necesario

FORMATO para cada post:
---POST [N] — [DÍA/HORA]---
TIPO: [tipo de contenido]
VISUAL: [descripción del visual necesario]
IMAGE: [ruta absoluta a imagen cuando esté disponible, sino dejar vacío]
STATUS: PENDING_APPROVAL
CAPTION:
[caption completa]
HASHTAGS:
[hashtags]
---"""

        return self.ask_claude(prompt, max_tokens=3000)

    def process_inbox(self, inbox: str) -> None:
        """Procesar mensajes de otros agentes."""
        if 'fotos disponibles' in inbox.lower():
            self.log.info("AGT-01 informó de fotos disponibles — regenerando posts con visuales")
            posts = self.generar_posts()
            if posts:
                self.save_result(posts)
                self.send_message(
                    'orchestrator',
                    'Posts regenerados con fotos',
                    'Posts Instagram actualizados con los nuevos visuales de África. Listo para aprobación.',
                )

    # ── ENTRY POINTS ─────────────────────────────────────────────────────────

    def run(self) -> None:
        """Genera posts semanales y los guarda en vault para aprobación."""
        self.log.info("AGT-02 Instagram iniciando — modo generación")

        # Leer inbox
        inbox = self.read_inbox()
        if inbox and 'PENDIENTE' in inbox:
            self.process_inbox(inbox)
            self.mark_inbox_done()
            return

        # Generar posts semanales
        self.log.info("Generando posts semana siguiente")
        posts = self.generar_posts()

        if not posts:
            self.log.error("Claude no generó posts")
            self.send_message(
                'orchestrator',
                'ERROR generando posts',
                'AGT-02 falló al generar posts. Verificar ANTHROPIC_API_KEY.',
                priority='alta',
            )
            return

        # Guardar en vault para aprobación
        self.save_result(posts)
        # También guardar en _aprobados.md como candidatos con STATUS: PENDING_APPROVAL
        self.vault_write('agentes/agt02_instagram', '_aprobados', posts, modo='append')
        self.save_memory(f"Posts generados semana {datetime.now().isocalendar()[1]}")

        # Informar al orchestrator
        self.send_message(
            'orchestrator',
            'Posts listos para aprobación',
            (
                f"5 posts semana {datetime.now().isocalendar()[1]} generados y guardados en vault.\n"
                "agentes/agt02_instagram/_resultado.md\n\n"
                "Para aprobar un post: cambia STATUS: PENDING_APPROVAL → STATUS: APPROVED\n"
                "Para publicar los aprobados: python3 agt02_instagram.py --publish"
            ),
        )

        # Notificar a Angel
        preview = posts[:400] if posts else 'Error'
        self.notify(
            f"5 posts generados para la semana\n\n"
            f"Guardados en vault para tu aprobación.\n\n"
            f"Para aprobar: edita _aprobados.md y pon STATUS: APPROVED\n"
            f"Para publicar: python3 agt02_instagram.py --publish\n\n"
            f"Preview:\n{preview}..."
        )

        self.log.info("AGT-02 completado")

    def run_publish(self) -> None:
        """Publica posts aprobados en vault. Solo se invoca con --publish."""
        self.log.info("AGT-02 Instagram iniciando — modo publicación")
        count = self.publish_approved()
        if count == 0:
            self.log.info("Ningún post publicado en esta ejecución")
        else:
            self.log.info(f"Publicados {count} posts en Instagram")


# ── MAIN ──────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    agent = InstagramAgent()

    if '--publish' in sys.argv:
        # Publicar posts aprobados en vault — NUNCA se hace automáticamente
        agent.run_publish()
    else:
        # Comportamiento por defecto: generar posts para aprobación
        agent.run()
