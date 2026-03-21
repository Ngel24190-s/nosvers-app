#!/usr/bin/env python3
"""
NosVers · Growth Tracker — Ventas, ROI, Experimentos
Mide todo lo que importa para llegar a 2.000€/mes.
Cron: viernes 19h — 0 19 * * 5
"""
import sys, json, os
from datetime import datetime, timedelta
sys.path.insert(0, '/home/nosvers/agents')
from agent_base import NosVersAgent
import requests

PERSONALITY = """Eres el Growth Tracker de NosVers. Mides ventas, costes, ROI por canal.

OBJETIVO: M3=600€/mes, M6=2.000€/mes

PRODUCTOS Y MÁRGENES:
| Producto | PVP | Coste | Margen |
|----------|-----|-------|--------|
| Pack Engrais Vert | 9,90€ | ~3€ | ~70% |
| Lombricompost 5L | 9,90€ | ~2€ | ~80% |
| Kit Extrait Vivant | 45€ | ~15€ | ~67% |
| Service Frais | 25€ | ~8€ | ~68% |
| Atelier Sol Vivant | 85€ | ~10€ | ~88% |
| Club Sol Vivant | 15€/mes | ~2€ | ~87% |

REGLAS:
- Números primero, interpretación después
- Si no hay datos suficientes, dilo claramente
- Nunca infles resultados
- Propón siempre al menos 1 experimento concreto
- Dashboard semanal máximo 10 líneas

TONO: Directo. Datos. Sin adornos."""


class GrowthAgent(NosVersAgent):

    def __init__(self):
        super().__init__('agt_growth', '📈', PERSONALITY)

    def get_wc_orders(self) -> dict:
        """Obtener pedidos recientes de WooCommerce Store API."""
        try:
            r = requests.get(
                'https://nosvers.com/wp-json/wc/store/v1/cart',
                timeout=10
            )
            # Store API is limited without auth, so let's try the main API
            # This is a read-only check
        except:
            pass

        # Check WooCommerce orders via REST API
        wp_url = os.getenv('WP_URL', 'https://nosvers.com/wp-json/wp/v2/')
        wp_user = os.getenv('WP_USER', '')
        wp_pass = os.getenv('WP_PASS', '')

        if not wp_user or not wp_pass:
            return {'error': 'WP credentials not configured', 'orders': []}

        try:
            # Use WC REST API
            wc_url = 'https://nosvers.com/wp-json/wc/v3/orders'
            after = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%dT00:00:00')
            r = requests.get(
                f'{wc_url}?after={after}&per_page=50&status=completed,processing',
                auth=(wp_user, wp_pass),
                timeout=15
            )
            if r.status_code == 200:
                orders = r.json()
                return {'orders': orders, 'count': len(orders)}
            else:
                return {'error': f'WC API {r.status_code}', 'orders': []}
        except Exception as e:
            return {'error': str(e), 'orders': []}

    def get_blog_stats(self) -> str:
        """Obtener stats de posts del blog."""
        try:
            r = requests.get(
                'https://nosvers.com/wp-json/wp/v2/posts?per_page=10&_fields=id,title,date',
                timeout=10
            )
            posts = r.json()
            return f"{len(posts)} posts publicados. Último: {posts[0]['date'][:10]} — {posts[0]['title']['rendered'][:50]}" if posts else "Sin posts"
        except:
            return "Error obteniendo posts"

    def estimate_api_cost(self) -> str:
        """Estimar coste API Claude basado en logs de agentes."""
        logs_dir = '/home/nosvers/logs'
        agents_dir = '/home/nosvers/agents'
        total_calls = 0
        today = datetime.now().strftime('%Y-%m-%d')
        week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

        for logf in [f for d in [logs_dir, agents_dir] for f in os.listdir(d) if f.endswith('.log')]:
            full = os.path.join(logs_dir if logf in os.listdir(logs_dir) else agents_dir, logf)
            try:
                with open(full, 'r', errors='replace') as f:
                    for line in f:
                        if week_ago <= line[:10] <= today and 'Claude API' not in line and 'completado' in line.lower():
                            total_calls += 1
            except:
                continue

        # Estimate: ~0.01-0.03€ per Sonnet call average
        cost_low = total_calls * 0.01
        cost_high = total_calls * 0.03
        return f"~{total_calls} ejecuciones agentes esta semana → {cost_low:.2f}-{cost_high:.2f}€ estimado"

    def get_products_info(self) -> str:
        """Obtener info de productos."""
        try:
            r = requests.get(
                'https://nosvers.com/wp-json/wc/store/v1/products?per_page=20',
                timeout=10
            )
            products = r.json()
            lines = []
            for p in products:
                price = int(p.get('prices', {}).get('price', 0)) / 100
                stock = '✅' if p.get('is_in_stock') else '❌'
                lines.append(f"  {stock} {p['name'][:40]} — {price:.2f}€")
            return '\n'.join(lines)
        except Exception as e:
            return f"Error: {e}"

    def run(self):
        self.log.info("Growth Tracker — dashboard semanal")

        orders = self.get_wc_orders()
        blog = self.get_blog_stats()
        api_cost = self.estimate_api_cost()
        products = self.get_products_info()

        # Build context for Claude
        orders_summary = "Sin datos de pedidos (WC API no configurada o sin pedidos)"
        if orders.get('orders'):
            total_revenue = sum(float(o.get('total', 0)) for o in orders['orders'])
            orders_summary = f"{orders['count']} pedidos / {total_revenue:.2f}€ en los últimos 30 días"
        elif orders.get('error'):
            orders_summary = f"Error WC: {orders['error']}"

        prompt = f"""{self.personality}

DATOS ESTA SEMANA:

VENTAS (30 días):
{orders_summary}

PRODUCTOS ACTIVOS:
{products}

BLOG:
{blog}

COSTE INFRAESTRUCTURA:
{api_cost}
VPS Hostinger: ~10€/mes
Canva: gratis

Genera un dashboard semanal para Angel con:
1. VENTAS: resumen + tendencia
2. CONTENIDO: blog + Instagram (posts publicados)
3. COSTES: API + infra vs ingresos
4. EXPERIMENTO: propón 1 test concreto para esta semana
5. FOCO RECOMENDADO: qué producto empujar y por qué

Máximo 15 líneas. Directo. Sin adornos."""

        result = self.ask_claude(prompt, max_tokens=600)
        self.save_result(result)

        # Save to vault
        self.vault_write('operaciones', 'dashboard-semanal',
                        f"# Dashboard — {self.ts}\n\n{result}", modo='overwrite')

        # Notify Angel
        short = result[:500] if result else "Sin datos suficientes"
        self.notify(f"📈 *Growth Tracker — Semana*\n\n{short}")
        self.log.info("Growth Tracker completado")

    def consult(self, question: str) -> str:
        products = self.get_products_info()
        prompt = f"""{self.personality}

PRODUCTOS:
{products}

PREGUNTA: {question}

Responde con datos concretos. Si no tienes datos, di qué necesitas para responder."""
        return self.ask_claude(prompt, max_tokens=400)


if __name__ == '__main__':
    agent = GrowthAgent()
    if len(sys.argv) > 1 and sys.argv[1] == 'consult':
        q = ' '.join(sys.argv[2:]) if len(sys.argv) > 2 else "Resumen de ventas"
        print(agent.consult(q))
    else:
        agent.run()
