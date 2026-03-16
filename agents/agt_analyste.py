#!/usr/bin/env python3
"""
NosVers · L'Analyste — Métriques & Intelligence
Lit les stats Instagram, WooCommerce, WordPress.
Rapport hebdomadaire le vendredi. Informe Le Directeur.
Cron: vendredi 18h — 0 18 * * 5
"""
import sys, json, requests
from datetime import datetime, timedelta
sys.path.insert(0, '/home/nosvers/agents')
from agent_base import NosVersAgent

PERSONALITY = """Tu es L'Analyste, expert en métriques et performance de NosVers.

RÔLE:
- Collecter et interpréter les données de performance
- Rapport hebdomadaire: ce qui a marché, ce qui n'a pas marché, pourquoi
- Recommandations concrètes pour Le Directeur
- Surveiller les ventes WooCommerce et les tendances

MÉTRIQUES SUIVIES:
- Instagram: engagement, portée, croissance followers, meilleurs posts
- WordPress: visites, pages les plus vues, temps sur page
- WooCommerce: commandes, CA semaine, produits les plus vendus
- Telegram Club: engagement membres (quand Club ouvert)

FORMAT RAPPORT:
- Court et actionnable (max 10 lignes)
- Chiffres en gras
- 1 recommandation principale pour la semaine suivante

STYLE: Factuel, chiffres, pas de blabla. Si pas de données: le dire clairement.
"""

class AnalysteAgent(NosVersAgent):

    def __init__(self):
        super().__init__('agt_analyste', '📊', PERSONALITY)

    def get_wp_stats(self) -> dict:
        """Récupérer les stats WordPress via API."""
        try:
            r = requests.get(
                f"{self.vault_read('contexto', 'nosvers-identidad') or 'https://nosvers.com'}/wp-json/wp/v2/posts?per_page=5&_fields=id,title,date,link",
                auth=(self.vault_read('contexto', 'wp-credentials') or 'claude_nosvers', ''),
                timeout=10
            )
            return {'posts_recents': len(r.json()) if r.ok else 0}
        except:
            return {}

    def get_woo_stats(self) -> dict:
        """Récupérer les commandes WooCommerce."""
        try:
            week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%dT00:00:00')
            r = requests.get(
                'https://nosvers.com/wp-json/wc/v3/orders',
                params={'after': week_ago, 'per_page': 50, '_fields': 'id,total,status,line_items'},
                auth=('claude_nosvers', 'fkLzcfDHAE8i6WZQEUCVCvY3'),
                timeout=10
            )
            if r.ok:
                orders = r.json()
                total_ca = sum(float(o.get('total', 0)) for o in orders if o.get('status') == 'completed')
                return {
                    'commandes_semaine': len(orders),
                    'ca_semaine': round(total_ca, 2),
                    'commandes_completees': sum(1 for o in orders if o.get('status') == 'completed')
                }
        except:
            pass
        return {}

    def generate_report(self) -> str:
        wp = self.get_wp_stats()
        woo = self.get_woo_stats()

        data_str = f"""
DONNÉES COLLECTÉES:
WordPress: {json.dumps(wp, ensure_ascii=False)}
WooCommerce: {json.dumps(woo, ensure_ascii=False)}
P�riode: semaine du {(datetime.now()-timedelta(7)).strftime('%d/%m')} au {datetime.now().strftime('%d/%m/%Y')}
"""
        prompt = f"""{self.personality}

{data_str}

Génère le rapport hebdomadaire court:
- 3-4 chiffres clés
- Ce qui a bien marché
- Ce qui peut être amélioré
- 1 recommandation pour Le Directeur

Format Telegram (markdown, court)."""
        return self.call_claude(prompt, max_tokens=300)

    def run(self):
        self.log.info("L'Analyste — rapport hebdomadaire")
        report = self.generate_report()
        self.save_result(report)

        # Envoyer rapport au Directeur
        self.message_agent('agt_directeur',
            f"RAPPORT SEMAINE — DE L'ANALYSTE\n{datetime.now().strftime('%d/%m/%Y')}\n\n{report}")

        # Telegram Angel
        self.notify_telegram(f"📊 *Rapport hebdomadaire — L'Analyste*\n\n{report}")
        self.log.info("Rapport envoyé")

    def consult(self, question: str, contexte: str = "") -> str:
        data = self.get_woo_stats()
        prompt = f"""{self.personality}
DONNÉES ACTUELLES: {json.dumps(data, ensure_ascii=False)}
QUESTION: {question}
Réponds avec des chiffres et une recommandation."""
        return self.call_claude(prompt, max_tokens=300)


if __name__ == '__main__':
    agent = AnalysteAgent()
    if len(sys.argv) > 1 and sys.argv[1] == 'consult':
        q = ' '.join(sys.argv[2:]) if len(sys.argv) > 2 else "Performance cette semaine?"
        print(agent.consult(q))
    else:
        agent.run()
