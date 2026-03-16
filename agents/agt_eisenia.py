#!/usr/bin/env python3
"""
NosVers · Maître Eisenia — Spécialiste Lombricompost
Expert: Eisenia fetida, bacs, récolte, duplication, humidité, pH, alimentation.
Détecte les événements bac et déclenche la cascade inter-agents.
Cron: toutes les 6h — 0 */6 * * *
"""
import sys, json
from datetime import datetime, timedelta
sys.path.insert(0, '/home/nosvers/agents')
from agent_base import NosVersAgent

PERSONALITY = """Tu es Maître Eisenia, expert lombricompost de NosVers.

EXPERTISE ABSOLUE:
- Eisenia fetida: biologie, comportement, stress, reproduction
- Gestion des bacs: humidité (70-80%), pH (6.5-7.5), température (15-25°C)
- Récolte et duplication: timing, technique, pesée, transfert
- Alimentation: ratios C/N, fréquences, aliments à éviter
- Diagnostic visuel: fuite des vers, odeurs, couleur, texture

BACS NOSVERS (état actuel):
- Bac #1: bac principal, ~9kg de vers, opérationnel depuis 8 mois
- Bac #2: deuxième bac, ~9kg de vers, opérationnel depuis 6 mois  
- IBC: grand bac extérieur, production intensive
- Nouveau bac: en préparation si duplication prévue

RÈGLE CASCADES — quand tu détectes un événement, tu NOTIFIES:
- Bac prêt à récolter → Message à Le Composteur (préparer litière réception)
- Bac prêt à dupliquer → Message à África via Telegram + créer tâche dans checklist
- Problème détecté (fuite, odeur, surcharge) → Alerte urgente Telegram + Angel
- Après récolte → Notifier L'Analyste (mise à jour stock lombricompost)

STYLE: Direct, technique, concret. Donne des chiffres. En français. 
Quand África pose une question: réponds avec ce qu'elle peut FAIRE AUJOURD'HUI.
"""

# Seuils de déclenchement cascade
SEUILS = {
    'humidite_min': 65,
    'humidite_max': 85,
    'temp_min': 12,
    'temp_max': 28,
    'jours_avant_recolte': 3,    # Prévenir 3j avant
    'jours_avant_duplication': 5, # Prévenir 5j avant
}

class EiseniaAgent(NosVersAgent):

    def __init__(self):
        super().__init__('agt_eisenia', '🪱', PERSONALITY)

    def check_bacs_status(self):
        """Lire l'état des bacs depuis la vault et détecter les événements."""
        etat_raw = self.vault_read('agentes/agt_eisenia', '_etat_bacs')
        if not etat_raw:
            return {}
        try:
            import re as _re
            jm = _re.search(r'\{[\s\S]+\}', etat_raw)
            return json.loads(jm.group()) if jm else {}
        except:
            return {}

    def save_bacs_status(self, etat: dict):
        self.vault_write('agentes/agt_eisenia', '_etat_bacs',
                         json.dumps(etat, ensure_ascii=False, indent=2), modo='overwrite')

    def detect_cascades(self, bacs: dict) -> list:
        """Detecter les événements qui déclenchent des cascades."""
        cascades = []
        today = datetime.now()

        for bac_id, bac in bacs.items():
            jours_depuis_dernier = bac.get('jours_depuis_dernier_apport', 0)
            jours_depuis_creation = bac.get('jours_depuis_creation', 0)
            humidite = bac.get('humidite', 75)
            temperature = bac.get('temperature', 20)
            poids_vers = bac.get('poids_vers_kg', 0)
            recolte_prevue = bac.get('recolte_prevue_dans_jours', 999)
            duplication_prevue = bac.get('duplication_prevue_dans_jours', 999)

            # Récolte imminente
            if 0 < recolte_prevue <= SEUILS['jours_avant_recolte']:
                cascades.append({
                    'type': 'recolte_imminente',
                    'bac': bac_id,
                    'jours': recolte_prevue,
                    'kg_estimés': bac.get('kg_lombricompost_pret', 0),
                    'urgence': 'haute' if recolte_prevue <= 1 else 'normale'
                })

            # Duplication imminente
            if 0 < duplication_prevue <= SEUILS['jours_avant_duplication']:
                cascades.append({
                    'type': 'duplication_imminente',
                    'bac': bac_id,
                    'jours': duplication_prevue,
                    'poids_vers': poids_vers,
                    'urgence': 'haute' if duplication_prevue <= 2 else 'normale'
                })

            # Problème humidité
            if humidite < SEUILS['humidite_min']:
                cascades.append({
                    'type': 'humidite_basse',
                    'bac': bac_id,
                    'valeur': humidite,
                    'urgence': 'haute'
                })
            elif humidite > SEUILS['humidite_max']:
                cascades.append({
                    'type': 'humidite_haute',
                    'bac': bac_id,
                    'valeur': humidite,
                    'urgence': 'normale'
                })

            # Problème température
            if temperature < SEUILS['temp_min'] or temperature > SEUILS['temp_max']:
                cascades.append({
                    'type': 'temperature_hors_seuil',
                    'bac': bac_id,
                    'valeur': temperature,
                    'urgence': 'haute'
                })

        return cascades

    def notify_composteur(self, cascade: dict):
        """Notifier Le Composteur qu'une récolte approche."""
        msg = f"""📬 MESSAGE DE MAÎTRE EISENIA → LE COMPOSTEUR
Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}
Événement: {cascade['type']}
Bac: {cascade['bac']}
Dans: {cascade.get('jours', '?')} jours
KG lombricompost disponibles: ~{cascade.get('kg_estimés', '?')} kg

ACTION REQUISE:
Le bac {cascade['bac']} sera prêt à récolter dans {cascade.get('jours', '?')} jour(s).
Prépare la litière de réception:
- Carton humidifié pour la base
- Matière brune disponible (feuilles, paille)
- Espace libéré dans le taller

Maître Eisenia 🪱"""
        self.message_agent('agt_composteur', msg)
        self.log.info(f"Notifié Le Composteur: récolte {cascade['bac']} dans {cascade.get('jours')}j")

    def notify_africa_duplication(self, cascade: dict):
        """Notifier África d'une duplication imminente."""
        jours = cascade.get('jours', '?')
        bac = cascade['bac']
        poids = cascade.get('poids_vers', '?')

        msg_telegram = (
            f"🪱 *Maître Eisenia* — Duplication {bac}\n\n"
            f"Le {bac} est prêt pour la duplication dans *{jours} jour(s)*.\n"
            f"Poids des vers estimé: *{poids} kg*\n\n"
            f"*Ce qu'il faut préparer:*\n"
            f"• Nouveau bac propre + litière carton\n"
            f"• Seau 20L + tamis de récolte\n"
            f"• Étiquette + date de création\n\n"
            f"Le Planificateur t'a créé les tâches dans l'app 📋"
        )
        self.notify_telegram(msg_telegram)

        # Écrire dans inbox du planificateur
        tache_msg = f"""TÂCHE DUPLICATION — {bac}
Source: Maître Eisenia
Date détection: {datetime.now().strftime('%d/%m/%Y')}
Délai: {jours} jours
Priorité: {'URGENTE' if cascade['urgence'] == 'haute' else 'NORMALE'}

Tâches pour África:
1. Préparer le nouveau bac (carton + litière)
2. Tamisage de récolte côté {bac} (garder 1/3 vers + vieux compost)
3. Transfert 50% des vers dans le nouveau bac
4. Peser les deux bacs après transfert
5. Étiqueter avec date de création
6. Informer Maître Eisenia du résultat"""
        self.message_agent('agt_planificateur', tache_msg)

    def run(self):
        self.log.info("Maître Eisenia — vérification des bacs")

        bacs = self.check_bacs_status()
        if not bacs:
            self.log.info("Pas de données bacs en vault — mode consultation uniquement")
            return

        cascades = self.detect_cascades(bacs)
        if not cascades:
            self.log.info("Tous les bacs en ordre — aucune cascade déclenchée")
            return

        for c in cascades:
            self.log.info(f"Cascade détectée: {c['type']} sur {c['bac']}")

            if c['type'] == 'recolte_imminente':
                self.notify_composteur(c)

            elif c['type'] == 'duplication_imminente':
                self.notify_africa_duplication(c)
                self.notify_composteur(c)  # Composteur aussi prévenu

            elif c['type'] in ('humidite_basse', 'humidite_haute', 'temperature_hors_seuil'):
                urgence = "🚨 URGENT" if c['urgence'] == 'haute' else "⚠️ Attention"
                self.notify_telegram(
                    f"{urgence} — *Maître Eisenia*\n"
                    f"Problème {c['bac']}: {c['type']}\n"
                    f"Valeur: {c.get('valeur', '?')}"
                )

        # Sauvegarder le résumé des cascades
        self.save_result(json.dumps(cascades, ensure_ascii=False, indent=2))

    def consult(self, question: str, contexte: str = "") -> str:
        """Répondre à une question technique sur le lombricompost."""
        bacs = self.check_bacs_status()
        bacs_context = json.dumps(bacs, ensure_ascii=False) if bacs else "Non disponible"

        prompt = f"""{self.personality}

ÉTAT ACTUEL DES BACS:
{bacs_context}

CONTEXTE ADDITIONNEL: {contexte}

QUESTION: {question}

Réponds de façon pratique et directe. Si l'état des bacs est pertinent, utilise-le.
Si tu as besoin d'un autre agent (Le Composteur, Le Berger, Dr. Ingham), dis-le clairement.
"""
        return self.call_claude(prompt, max_tokens=600)


if __name__ == '__main__':
    agent = EiseniaAgent()
    if len(sys.argv) > 1 and sys.argv[1] == 'consult':
        q = ' '.join(sys.argv[2:]) if len(sys.argv) > 2 else "État général des bacs?"
        print(agent.consult(q))
    else:
        agent.run()
