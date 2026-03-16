#!/usr/bin/env python3
"""
NosVers · Le Planificateur — Organisateur des tâches d'África
Le seul agent qui a la vue complète sur ce qu'África doit faire.
Reçoit les messages de tous les agents, crée des tâches concrètes, les priorise.
Notifie África chaque matin à 7h30 avec son plan du jour.
Cron: 30 7 * * * (matin) + toutes les 4h pour traiter inbox
"""
import sys, json
from datetime import datetime, timedelta
sys.path.insert(0, '/home/nosvers/agents')
from agent_base import NosVersAgent

PERSONALITY = """Tu es Le Planificateur, l'agent qui organise le travail d'África.

TON RÔLE:
- Tu reçois les demandes de tous les autres agents (Eisenia, Composteur, Berger, Dr. Ingham)
- Tu les transformes en tâches concrètes, ordonnées et réalistes pour África
- Tu connais ses contraintes: 2-4h disponibles par jour, souvent seule
- Tu priorises: urgence BIOLOGIQUE d'abord (vers, animaux), puis production, puis admin

RÈGLES DE PRIORISATION:
🔴 URGENTE (faire aujourd'hui): animaux en danger, bac en crise, sevrage dépassé
🟠 IMPORTANTE (faire cette semaine): récolte imminente, duplication programmée, semis critique
🟡 NORMALE (quand possible): observations, préparations, entretien
🟢 QUAND TU PEUX: documentation, notes, photos

FORMAT DES TÂCHES (toujours):
- Durée estimée (en minutes)
- Matériel nécessaire
- Étapes courtes et claires
- Résultat attendu

INTERACTIONS:
- Quand tu crées une tâche → l'écrire dans la checklist de l'app via API
- Chaque matin → envoyer le plan du jour à África par Telegram
- Si trop de tâches → demander à Angel de prioriser (Telegram)

STYLE: Clair, chronologique, maternel mais efficace. En français.
África ne doit jamais ouvrir l'app et se sentir submergée.
"""

TACHE_TEMPLATE = {
    'recolte': {
        'titre': '🪱 Récolte {bac}',
        'duree': 90,
        'materiel': 'Tamis, seau 20L, bac de réception, balance',
        'etapes': [
            'Arrêter l\'alimentation 48h avant (normalement déjà fait)',
            'Exposer à la lumière 30min pour faire descendre les vers',
            'Tamiser la moitié supérieure du bac',
            'Collecter le lombricompost dans le seau',
            'Peser et noter (cible: {kg_estimés}kg)',
            'Laisser les vers dans le bac avec leur lit',
        ]
    },
    'duplication': {
        'titre': '🪱 Duplication {bac}',
        'duree': 120,
        'materiel': 'Nouveau bac propre, carton humide, litière préparée, balance',
        'etapes': [
            'Préparer le nouveau bac avec litière (déjà préparée par Le Composteur)',
            'Séparer 50% des vers + compost → nouveau bac',
            'Peser les deux bacs',
            'Étiqueter les deux bacs avec date',
            'Alimenter les deux bacs légèrement',
            'Photographier et noter dans l\'app',
        ]
    },
    'litiere': {
        'titre': '🍂 Préparer litière nouveau bac',
        'duree': 30,
        'materiel': 'Carton non imprimé, eau, fumier lapin',
        'etapes': [
            'Découper et humidifier le carton (texture éponge, pas dégoulinant)',
            'Couvrir le fond du nouveau bac (5cm)',
            'Ajouter une couche mince de fumier lapin',
            'Vérifier humidité finale: test de la main',
        ]
    }
}

class PlanificateurAgent(NosVersAgent):

    def __init__(self):
        super().__init__('agt_planificateur', '📋', PERSONALITY)
        self.taches_file = 'agentes/agt_planificateur'

    def get_taches_actives(self) -> list:
        """Lire les tâches actives depuis la vault."""
        raw = self.vault_read(self.taches_file, '_taches')
        if not raw:
            return []
        try:
            return json.loads(raw)
        except:
            return []

    def save_taches(self, taches: list):
        self.vault_write(self.taches_file, '_taches',
                         json.dumps(taches, ensure_ascii=False, indent=2), modo='overwrite')

    def add_tache(self, tache: dict):
        """Ajouter une tâche à la liste."""
        taches = self.get_taches_actives()
        tache['id'] = f"T{datetime.now().strftime('%m%d%H%M')}"
        tache['created'] = datetime.now().strftime('%d/%m/%Y %H:%M')
        tache['done'] = False
        taches.append(tache)
        # Trier par priorité
        priority_order = {'rouge': 0, 'orange': 1, 'jaune': 2, 'vert': 3}
        taches.sort(key=lambda x: priority_order.get(x.get('priorite', 'jaune'), 2))
        self.save_taches(taches)
        return tache['id']

    def process_inbox(self):
        """Lire et traiter les messages des autres agents."""
        inbox = self.vault_read(self.taches_file, '_inbox')
        if not inbox or not inbox.strip():
            return
        messages = [m.strip() for m in inbox.split('---') if m.strip()]

        for msg in messages:
            self.log.info(f"Message reçu: {msg[:100]}")
            tache = self.parse_message_to_tache(msg)
            if tache:
                tid = self.add_tache(tache)
                self.log.info(f"Tâche créée: {tid} — {tache.get('titre', '')}")

        # Vider inbox
        self.vault_write(self.taches_file, '_inbox', '', modo='overwrite')

    def parse_message_to_tache(self, msg: str) -> dict:
        """Transformer un message inter-agent en tâche structurée."""
        prompt = f"""{self.personality}

MESSAGE REÇU D'UN AGENT:
{msg}

Transforme ce message en une tâche structurée pour África au format JSON:
{{
  "titre": "titre court avec emoji",
  "source": "nom de l'agent source",
  "priorite": "rouge|orange|jaune|vert",
  "duree_min": durée en minutes,
  "materiel": ["item1", "item2"],
  "etapes": ["étape 1", "étape 2", "étape 3"],
  "resultat_attendu": "ce qu'África doit voir à la fin",
  "delai_jours": nombre de jours avant deadline
}}

Réponds UNIQUEMENT avec le JSON, rien d'autre."""
        response = self.call_claude(prompt, max_tokens=400)
        try:
            import re
            json_match = re.search(r'\{[\s\S]+\}', response)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        return None

    def build_plan_du_jour(self) -> str:
        """Construire le plan du jour pour África."""
        taches = [t for t in self.get_taches_actives() if not t.get('done')]
        if not taches:
            return None

        # Filtrer par priorité et durée disponible (max 3h = 180min)
        temps_total = 0
        taches_du_jour = []
        for t in taches:
            duree = t.get('duree_min', 30)
            if temps_total + duree <= 180:
                taches_du_jour.append(t)
                temps_total += duree
            if len(taches_du_jour) >= 5:
                break

        if not taches_du_jour:
            return None

        lines = [
            f"📋 *Plan du jour — {datetime.now().strftime('%A %d %B')}*",
            f"Temps estimé: *{temps_total} min*\n"
        ]

        priority_icons = {'rouge': '🔴', 'orange': '🟠', 'jaune': '🟡', 'vert': '🟢'}
        for i, t in enumerate(taches_du_jour, 1):
            icon = priority_icons.get(t.get('priorite', 'jaune'), '🟡')
            duree = t.get('duree_min', '?')
            lines.append(f"{icon} *{i}. {t['titre']}* ({duree}min)")
            if t.get('etapes'):
                for etape in t['etapes'][:3]:
                    lines.append(f"   • {etape}")

        remaining = len(taches) - len(taches_du_jour)
        if remaining > 0:
            lines.append(f"\n_+{remaining} autre(s) tâche(s) en attente_")

        return '\n'.join(lines)

    def send_morning_briefing(self):
        """Envoyer le briefing du matin à África."""
        plan = self.build_plan_du_jour()
        if plan:
            self.notify_telegram(plan)
            self.log.info("Briefing matinal envoyé à África")
        else:
            self.notify_telegram(
                "📋 *Planificateur*\n"
                "Aucune tâche urgente aujourd'hui. "
                "Bonne journée África 🌿"
            )

    def run(self):
        self.log.info("Le Planificateur — traitement inbox")
        self.process_inbox()

        # Si c'est le matin (7h-8h), envoyer briefing
        heure = datetime.now().hour
        if 7 <= heure <= 8:
            self.send_morning_briefing()

    def consult(self, question: str, contexte: str = "") -> str:
        taches = self.get_taches_actives()
        taches_str = json.dumps(
            [t for t in taches if not t.get('done')][:5],
            ensure_ascii=False, indent=2
        )
        prompt = f"""{self.personality}

TÂCHES ACTIVES:
{taches_str}

QUESTION: {question}

Réponds directement. Si tu dois créer ou modifier des tâches, dis-le clairement."""
        return self.call_claude(prompt, max_tokens=400)


if __name__ == '__main__':
    agent = PlanificateurAgent()
    if len(sys.argv) > 1:
        if sys.argv[1] == 'consult':
            q = ' '.join(sys.argv[2:]) if len(sys.argv) > 2 else "Quelles sont mes tâches?"
            print(agent.consult(q))
        elif sys.argv[1] == 'briefing':
            agent.send_morning_briefing()
    else:
        agent.run()
