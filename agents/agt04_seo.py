#!/usr/bin/env python3
"""
NosVers · AGT-04 SEO
Genera artículo blog semanal en WordPress + análisis keywords.
Cron: lunes 7h — 0 7 * * 1
"""
import sys, requests as req
sys.path.insert(0, '/home/nosvers/agents')
from agent_base import NosVersAgent, APP_URL, APP_TOKEN, WP_URL, WP_USER, WP_PASS
from datetime import datetime
import os


PERSONALITY = """PERSONALIDAD — AGT-04 "El Investigador"
Lees estudios científicos y los traduces en artículos que la gente entiende y Google ama.
El SEO no es spam de keywords — es responder mejor que nadie la pregunta que alguien escribe ahora mismo.
Estructura: pregunta → contexto científico → aplicación práctica → NosVers como solución natural.
Sin venta dura. La referencia científica al final, no al inicio.
Tono: Periodismo de divulgación. Rigor sin pedantería.
Nunca inventar datos. Nunca usar keywords de forma forzada. Nunca copiar de otros blogs.
REGLA: Nunca publiques sin aprobación de Angel."""

class SEOAgent(NosVersAgent):

    TOPICS_ROTACION = [
        "LombriThé — protocole complet et science derrière",
        "Pourquoi votre sol est fatigué (et comment l'aider)",
        "Eisenia fetida — tout savoir sur nos vers de compost",
        "Soil Food Web — le réseau invisible qui nourrit vos plantes",
        "Compostage vs lombricompostage — quelle différence vraiment?",
        "Les plantes indicatrices — lire son jardin comme un livre",
        "Engrais vert — quand et comment les utiliser",
    ]

    def __init__(self):
        super().__init__('agt04_seo', '🔍', PERSONALITY)

    def check_triggers(self) -> list:
        triggers = []
        memoria = self.get_memory()
        # Verificar si ya publicamos esta semana
        semana_actual = str(datetime.now().isocalendar()[1])
        if f"semana_{semana_actual}" not in memoria:
            triggers.append('generar_articulo')
        return triggers

    def get_next_topic(self) -> str:
        """Determinar el siguiente tema por rotación."""
        memoria = self.get_memory()
        for topic in self.TOPICS_ROTACION:
            if topic not in memoria:
                return topic
        return self.TOPICS_ROTACION[0]  # Reset rotación

    def generar_articulo(self, topic: str) -> dict:
        """Generar artículo SEO completo con Claude."""
        africa_conocimiento = self.vault_read('contexto', 'africa-conocimiento')
        estudios = self.vault_read('estudios', 'soil-food-web')

        prompt = f"""Escribe un artículo SEO completo para el blog de nosvers.com.

TEMA: {topic}

CONOCIMIENTO CIENTÍFICO DISPONIBLE:
{estudios[:400]}

CONOCIMIENTO DE AFRICA:
{africa_conocimiento[:300]}

REQUISITOS SEO:
- Idioma: FRANCÉS
- Longitud: 1000-1400 palabras
- Keyword principal en título (max 60 chars), H2s, primer párrafo, meta description
- Keywords secundarias: lombricompost dordogne, sol vivant jardin, ferme biologique france
- Estructura: intro (problema) → desarrollo (solución científica) → aplicación práctica → CTA al Club
- Tono: experto pero accesible, con ejemplos concretos de la ferme
- CTA final: link al Club Sol Vivant (15€/mes)

FORMATO DE RESPUESTA (JSON):
{{
  "titre": "...",
  "meta_description": "... (max 155 chars)",
  "contenu_html": "...",
  "excerpt": "... (150 mots)"
}}"""

        respuesta = self.ask_claude(prompt, max_tokens=3000)
        if not respuesta:
            return {}

        # Intentar parsear JSON
        import json, re
        try:
            # Limpiar posible markdown
            clean = re.sub(r'```json|```', '', respuesta).strip()
            return json.loads(clean)
        except:
            # Si no es JSON válido, extraer manualmente
            return {
                "titre": f"NosVers — {topic}",
                "meta_description": topic[:150],
                "contenu_html": respuesta,
                "excerpt": respuesta[:200]
            }

    def publicar_wordpress(self, articulo: dict) -> dict:
        """Publicar como borrador en WordPress."""
        if not WP_PASS:
            return {"error": "WP_PASS no configurada"}

        # Envolver en bloques Gutenberg
        contenido = articulo.get('contenu_html', '')
        if '<!-- wp:' not in contenido:
            bloques = '\n\n'.join([
                f'<!-- wp:paragraph --><p>{p}</p><!-- /wp:paragraph -->'
                for p in contenido.split('\n\n') if p.strip()
            ])
        else:
            bloques = contenido

        try:
            r = req.post(f"{WP_URL}posts",
                auth=(WP_USER, WP_PASS),
                json={
                    "title": articulo.get('titre', 'Nouveau article'),
                    "content": bloques,
                    "excerpt": articulo.get('excerpt', ''),
                    "status": "draft",
                    "meta": {"rank_math_description": articulo.get('meta_description', '')}
                }, timeout=15)
            return r.json()
        except Exception as e:
            return {"error": str(e)}

    def run(self):
        self.log.info("AGT-04 SEO iniciando")

        # Verificar inbox
        inbox = self.read_inbox()
        if inbox and 'PENDIENTE' in inbox:
            self.mark_inbox_done()

        semana_actual = datetime.now().isocalendar()[1]
        memoria = self.get_memory()

        if f"semana_{semana_actual}" in memoria:
            self.log.info(f"Ya publicamos esta semana ({semana_actual})")
            return

        topic = self.get_next_topic()
        self.log.info(f"Generando artículo: {topic}")

        articulo = self.generar_articulo(topic)
        if not articulo:
            self.send_message('orchestrator', 'ERROR SEO', 'No se pudo generar artículo. Verificar API key.')
            return

        # Publicar como borrador
        wp_result = self.publicar_wordpress(articulo)
        post_id = wp_result.get('id', 'error')
        post_url = wp_result.get('link', '')

        # Guardar en vault
        self.vault_write('agentes/agt04_seo', '_resultado',
            f"# Artículo semana {semana_actual}\n\n"
            f"**Tema:** {topic}\n"
            f"**Post ID:** {post_id}\n"
            f"**URL:** {post_url}\n"
            f"**Estado:** Borrador — pendiente aprobación\n\n"
            f"**Meta:** {articulo.get('meta_description','')}",
            modo='overwrite')

        self.save_memory(
            f"semana_{semana_actual}: {topic}\n"
            f"Post ID: {post_id}\nURL: {post_url}"
        )

        # Avisar al orchestrator
        self.send_message('orchestrator',
            f'Artículo SEO listo — semana {semana_actual}',
            f'Borrador creado en WordPress.\nTema: {topic}\nPost ID: {post_id}\nPendiente aprobación de Angel.')

        self.notify(
            f"🔍 *Artículo SEO generado*\n\n"
            f"📝 {articulo.get('titre',topic)}\n"
            f"ID: {post_id}\n"
            f"Guardado como borrador — pendiente tu aprobación."
        )

        self.log.info(f"AGT-04 completado — Post {post_id}")

if __name__ == '__main__':
    SEOAgent().run()
