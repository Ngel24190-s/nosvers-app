# Blueprint — Potager Tracking (Gastos + Cosecha + Ahorro)

> **Handoff para Claude Code** · Generado por Angel/Claude el 2026-04-18
> Ejecutar los pasos de la sección 5 en orden. No saltar pasos.
> Criterios de aceptación en sección 6.

## OBJETIVO

África registra en la app `nosvers.com/granja/` (especialista 🌿 Potager & Semis) los gastos en planteles/semillas y las cosechas para consumo personal. El sistema calcula el ahorro vs precio de mercado. Los precios de referencia los actualiza Claude cada lunes vía web search. Registro libre de variedades.

## DECISIONES YA TOMADAS

- Interfaz: web en `/granja/` dentro del especialista Potager (NO bot)
- Precios actualizados automáticamente por Claude cada semana
- Registro libre de variedades (no catálogo fijo)
- Vault sincronizado para que el agente unificado lea desde allí
- Idioma UI: francés (África)

## CONTEXTO TÉCNICO EXISTENTE

- Página WordPress en `nosvers.com/granja/` con auth por token (sessionStorage `nv_token`)
- Backend: `/home/nosvers/public_html/api.php` (491 líneas, 18 case actuales)
- Config DB: `/home/nosvers/public_html/config.php` (DB_HOST, DB_NAME, DB_USER, DB_PASS)
- Vault: `/home/nosvers/public_html/knowledge_base/huerto/` (solo tiene `calendario-dordogne.md`)
- Especialista Potager actual tiene 4 textareas: `etat_huerto_cultivos`, `etat_huerto_serre`, `etat_huerto_riego`, `etat_huerto_problemas`
- Unified agent en `/home/nosvers/unified-agent/` con scheduler APScheduler

---

## 1. MIGRACIÓN SQL

Ejecutar contra la DB de la granja (misma que `inventaire`, `checklist`, `journal`).

```sql
CREATE TABLE IF NOT EXISTS huerto_entradas (
  id INT AUTO_INCREMENT PRIMARY KEY,
  fecha DATE NOT NULL,
  tipo ENUM('gasto','cosecha') NOT NULL,
  variedad VARCHAR(100) NOT NULL,
  cantidad DECIMAL(10,3) NOT NULL,
  unidad ENUM('g','kg','unidades','botte','barquette') NOT NULL DEFAULT 'kg',
  coste_eur DECIMAL(10,2) NULL,
  precio_ref_eur_kg DECIMAL(10,2) NULL,
  ahorro_eur DECIMAL(10,2) NULL,
  proveedor VARCHAR(150) NULL,
  origen ENUM('achat','semis_maison') NULL,
  nota TEXT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_fecha (fecha),
  INDEX idx_tipo (tipo),
  INDEX idx_variedad (variedad)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS huerto_precios_ref (
  variedad VARCHAR(100) PRIMARY KEY,
  precio_eur_kg DECIMAL(10,2) NOT NULL,
  peso_unidad_g INT NULL,
  fuente VARCHAR(255) NULL,
  fecha_actualizacion DATE NOT NULL,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### Conversión de unidades a kg (para cálculo de ahorro)

- `kg` → cantidad tal cual
- `g` → cantidad / 1000
- `unidades`, `botte`, `barquette` → `(cantidad * peso_unidad_g) / 1000`
- Si no hay peso_unidad_g registrado, fallback **200g**

Pesos estándar sugeridos (el agente semanal los rellenará): lechuga=300g, poireau=150g, botte épinards=250g, barquette fraises=250g, oeuf=60g, tomate=150g, courgette=300g.


---

## 2. ENDPOINTS api.php

A�adir **antes del `default:`** del switch en `/home/nosvers/public_html/api.php`.

### 2.1 `huerto_entrada_add`

```php
case 'huerto_entrada_add':
    $data = json_decode(file_get_contents('php://input'), true);
    $tipo = $data['tipo'] ?? '';
    if (!in_array($tipo, ['gasto','cosecha'])) {
        http_response_code(400);
        echo json_encode(['error' => 'tipo invalido']);
        break;
    }
    $fecha = $data['fecha'] ?? date('Y-m-d');
    $variedad = trim(strtolower($data['variedad'] ?? ''));
    $cantidad = (float)($data['cantidad'] ?? 0);
    $unidad = $data['unidad'] ?? 'kg';
    $coste = isset($data['coste_eur']) ? (float)$data['coste_eur'] : null;
    $proveedor = $data['proveedor'] ?? null;
    $origen = $data['origen'] ?? null;
    $nota = $data['nota'] ?? null;
    $precio_ref = null;
    $ahorro = null;

    if ($tipo === 'cosecha') {
        $stmt = $pdo->prepare("SELECT precio_eur_kg, peso_unidad_g FROM huerto_precios_ref WHERE variedad = :v");
        $stmt->execute([':v' => $variedad]);
        $ref = $stmt->fetch(PDO::FETCH_ASSOC);
        if ($ref) {
            $precio_ref = (float)$ref['precio_eur_kg'];
            $peso_u = $ref['peso_unidad_g'] ? (int)$ref['peso_unidad_g'] : 200;
            $cantidad_kg = $cantidad;
            if ($unidad === 'g') $cantidad_kg = $cantidad / 1000;
            elseif (in_array($unidad, ['unidades','botte','barquette'])) {
                $cantidad_kg = ($cantidad * $peso_u) / 1000;
            }
            $ahorro = round($cantidad_kg * $precio_ref, 2);
        }
    }

    $stmt = $pdo->prepare(
        "INSERT INTO huerto_entradas
         (fecha, tipo, variedad, cantidad, unidad, coste_eur, precio_ref_eur_kg, ahorro_eur, proveedor, origen, nota)
         VALUES (:fecha,:tipo,:variedad,:cantidad,:unidad,:coste,:precio_ref,:ahorro,:proveedor,:origen,:nota)"
    );
    $stmt->execute([
        ':fecha' => $fecha, ':tipo' => $tipo, ':variedad' => $variedad,
        ':cantidad' => $cantidad, ':unidad' => $unidad, ':coste' => $coste,
        ':precio_ref' => $precio_ref, ':ahorro' => $ahorro,
        ':proveedor' => $proveedor, ':origen' => $origen, ':nota' => $nota
    ]);
    $id = $pdo->lastInsertId();

    // Sync vault
    $mes = substr($fecha, 0, 7);
    $vault_dir = '/home/nosvers/public_html/knowledge_base/huerto';
    if (!is_dir($vault_dir)) mkdir($vault_dir, 0755, true);
    $vault_path = "$vault_dir/entradas-$mes.md";
    if (!file_exists($vault_path)) {
        file_put_contents($vault_path,
            "# Entradas huerto $mes\n\n" .
            "| Fecha | Tipo | Variedad | Cantidad | Unidad | Coste EUR | Ahorro EUR | Nota |\n" .
            "|-------|------|----------|----------|--------|-----------|------------|------|\n"
        );
    }
    $line = sprintf("| %s | %s | %s | %s | %s | %s | %s | %s |\n",
        $fecha, $tipo, $variedad, $cantidad, $unidad,
        $coste !== null ? number_format($coste, 2) : '-',
        $ahorro !== null ? number_format($ahorro, 2) : '-',
        $nota ? str_replace('|','/',$nota) : ''
    );
    file_put_contents($vault_path, $line, FILE_APPEND);

    echo json_encode([
        'ok' => true, 'id' => $id,
        'precio_ref_eur_kg' => $precio_ref,
        'ahorro_eur' => $ahorro,
        'aviso_precio' => ($tipo === 'cosecha' && $precio_ref === null)
            ? 'Prix non reference - Claude le cherchera lundi' : null
    ]);
    break;
```


### 2.2 `huerto_entradas_list`

```php
case 'huerto_entradas_list':
    $tipo = $_GET['tipo'] ?? null;
    $mes = $_GET['mes'] ?? null;
    $limit = min((int)($_GET['limit'] ?? 50), 500);
    $where = [];
    $params = [];
    if ($tipo && in_array($tipo, ['gasto','cosecha'])) {
        $where[] = 'tipo = :tipo';
        $params[':tipo'] = $tipo;
    }
    if ($mes && preg_match('/^\d{4}-\d{2}$/', $mes)) {
        $where[] = 'DATE_FORMAT(fecha,"%Y-%m") = :mes';
        $params[':mes'] = $mes;
    }
    $sql = "SELECT * FROM huerto_entradas";
    if ($where) $sql .= ' WHERE ' . implode(' AND ', $where);
    $sql .= ' ORDER BY fecha DESC, id DESC LIMIT ' . $limit;
    $stmt = $pdo->prepare($sql);
    $stmt->execute($params);
    echo json_encode($stmt->fetchAll(PDO::FETCH_ASSOC));
    break;
```

### 2.3 `huerto_entrada_delete`

```php
case 'huerto_entrada_delete':
    $data = json_decode(file_get_contents('php://input'), true);
    $id = (int)($data['id'] ?? 0);
    if (!$id) { http_response_code(400); echo json_encode(['error'=>'id requerido']); break; }
    $stmt = $pdo->prepare("DELETE FROM huerto_entradas WHERE id = :id");
    $stmt->execute([':id' => $id]);
    echo json_encode(['ok' => true, 'deleted' => $stmt->rowCount()]);
    break;
```

### 2.4 `huerto_balance`

```php
case 'huerto_balance':
    $mes = $_GET['mes'] ?? date('Y-m');
    $where_mes = ($mes === 'total') ? '1=1' : 'DATE_FORMAT(fecha,"%Y-%m") = :mes';
    $params = ($mes === 'total') ? [] : [':mes' => $mes];

    $stmt = $pdo->prepare(
        "SELECT
            SUM(CASE WHEN tipo='gasto' THEN coste_eur ELSE 0 END) AS gasto_total,
            SUM(CASE WHEN tipo='cosecha' THEN ahorro_eur ELSE 0 END) AS valor_cosecha,
            COUNT(CASE WHEN tipo='gasto' THEN 1 END) AS n_gastos,
            COUNT(CASE WHEN tipo='cosecha' THEN 1 END) AS n_cosechas
         FROM huerto_entradas WHERE $where_mes"
    );
    $stmt->execute($params);
    $totals = $stmt->fetch(PDO::FETCH_ASSOC);

    $stmt = $pdo->prepare(
        "SELECT variedad,
                SUM(CASE WHEN tipo='gasto' THEN coste_eur ELSE 0 END) AS gasto,
                SUM(CASE WHEN tipo='cosecha' THEN ahorro_eur ELSE 0 END) AS valor
         FROM huerto_entradas WHERE $where_mes
         GROUP BY variedad ORDER BY valor DESC LIMIT 20"
    );
    $stmt->execute($params);
    $por_variedad = $stmt->fetchAll(PDO::FETCH_ASSOC);

    $stmt = $pdo->query(
        "SELECT DATE_FORMAT(fecha,'%Y-%m') AS mes,
                SUM(CASE WHEN tipo='gasto' THEN coste_eur ELSE 0 END) AS gasto,
                SUM(CASE WHEN tipo='cosecha' THEN ahorro_eur ELSE 0 END) AS valor
         FROM huerto_entradas
         WHERE fecha >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
         GROUP BY mes ORDER BY mes"
    );
    $serie = $stmt->fetchAll(PDO::FETCH_ASSOC);

    $gasto = (float)($totals['gasto_total'] ?? 0);
    $valor = (float)($totals['valor_cosecha'] ?? 0);

    echo json_encode([
        'mes' => $mes,
        'gasto_total' => round($gasto, 2),
        'valor_cosecha' => round($valor, 2),
        'ahorro_neto' => round($valor - $gasto, 2),
        'n_gastos' => (int)$totals['n_gastos'],
        'n_cosechas' => (int)$totals['n_cosechas'],
        'por_variedad' => $por_variedad,
        'serie_mensual' => $serie
    ]);
    break;
```


### 2.5 `huerto_precios_get` y `huerto_precios_set`

```php
case 'huerto_precios_get':
    $stmt = $pdo->query(
        "SELECT variedad, precio_eur_kg, peso_unidad_g, fuente, fecha_actualizacion
         FROM huerto_precios_ref ORDER BY variedad"
    );
    echo json_encode($stmt->fetchAll(PDO::FETCH_ASSOC));
    break;

case 'huerto_precios_set':
    $data = json_decode(file_get_contents('php://input'), true);
    $items = $data['items'] ?? [];
    $stmt = $pdo->prepare(
        "INSERT INTO huerto_precios_ref (variedad, precio_eur_kg, peso_unidad_g, fuente, fecha_actualizacion)
         VALUES (:v, :p, :pu, :f, :fa)
         ON DUPLICATE KEY UPDATE precio_eur_kg=:p2, peso_unidad_g=:pu2, fuente=:f2, fecha_actualizacion=:fa2"
    );
    $n = 0;
    foreach ($items as $it) {
        $v = trim(strtolower($it['variedad'] ?? ''));
        if (!$v) continue;
        $p = (float)$it['precio_eur_kg'];
        $pu = isset($it['peso_unidad_g']) ? (int)$it['peso_unidad_g'] : null;
        $f = $it['fuente'] ?? 'manuel';
        $fa = $it['fecha_actualizacion'] ?? date('Y-m-d');
        $stmt->execute([
            ':v'=>$v, ':p'=>$p, ':pu'=>$pu, ':f'=>$f, ':fa'=>$fa,
            ':p2'=>$p, ':pu2'=>$pu, ':f2'=>$f, ':fa2'=>$fa
        ]);
        $n++;
    }
    echo json_encode(['ok'=>true, 'updated'=>$n]);
    break;
```

### 2.6 `huerto_variedades_distinct` (para autocompletado)

```php
case 'huerto_variedades_distinct':
    $stmt = $pdo->query(
        "SELECT DISTINCT variedad FROM huerto_entradas
         UNION
         SELECT variedad FROM huerto_precios_ref
         ORDER BY 1"
    );
    echo json_encode($stmt->fetchAll(PDO::FETCH_COLUMN));
    break;
```


---

## 3. UI — Añadir al especialista Potager

En la página WordPress de `/granja/`, localizar el bloque con `<div class="etat-title">🌿 Potager & Semis</div>` y **después** del `</div>` de cierre del `etat-grid` existente, añadir estos 3 bloques nuevos. Mantener coherencia visual con las clases existentes.

### 3.1 HTML

```html
<!-- ======= HUERTO TRACKING ======= -->
<div class="etat-section huerto-tracking" data-cat="huerto">
  <div class="etat-title">💸 Achat de plants / semis</div>
  <div class="huerto-form">
    <input type="date" id="ht_gasto_fecha">
    <input list="ht_variedades" id="ht_gasto_variedad" placeholder="Variété (ex: laitue, tomate...)">
    <input type="number" step="0.01" id="ht_gasto_cantidad" placeholder="Quantité" min="0">
    <select id="ht_gasto_unidad">
      <option value="unidades">unités</option>
      <option value="g">g</option>
      <option value="kg">kg</option>
      <option value="barquette">barquette</option>
    </select>
    <input type="number" step="0.01" id="ht_gasto_coste" placeholder="Coût €" min="0">
    <input type="text" id="ht_gasto_proveedor" placeholder="Fournisseur (optionnel)">
    <select id="ht_gasto_origen">
      <option value="achat">Acheté</option>
      <option value="semis_maison">Semis maison</option>
    </select>
    <button class="btn-primary" onclick="huertoGuardarGasto()">Enregistrer achat</button>
  </div>
  <div id="ht_gasto_feedback" class="huerto-feedback"></div>
</div>

<div class="etat-section huerto-tracking" data-cat="huerto">
  <div class="etat-title">🧺 Récolte pour consommation</div>
  <div class="huerto-form">
    <input type="date" id="ht_cosecha_fecha">
    <input list="ht_variedades" id="ht_cosecha_variedad" placeholder="Variété">
    <input type="number" step="0.01" id="ht_cosecha_cantidad" placeholder="Quantité" min="0">
    <select id="ht_cosecha_unidad">
      <option value="kg">kg</option>
      <option value="g">g</option>
      <option value="unidades">unités</option>
      <option value="botte">botte</option>
      <option value="barquette">barquette</option>
    </select>
    <input type="text" id="ht_cosecha_nota" placeholder="Note (optionnel)">
    <button class="btn-primary" onclick="huertoGuardarCosecha()">Enregistrer récolte</button>
  </div>
  <div id="ht_cosecha_feedback" class="huerto-feedback"></div>
</div>

<datalist id="ht_variedades"></datalist>

<div class="etat-section huerto-tracking" data-cat="huerto">
  <div class="etat-title">📊 Bilan potager</div>
  <div class="huerto-balance" id="ht_balance">
    <div class="bilan-row">
      <div class="bilan-cell">
        <div class="bilan-label">Dépensé (mois)</div>
        <div class="bilan-value" id="ht_b_gasto">—</div>
      </div>
      <div class="bilan-cell">
        <div class="bilan-label">Valeur récolte</div>
        <div class="bilan-value positive" id="ht_b_valor">—</div>
      </div>
      <div class="bilan-cell">
        <div class="bilan-label">Économie nette</div>
        <div class="bilan-value highlight" id="ht_b_ahorro">—</div>
      </div>
    </div>
    <div class="bilan-variedades" id="ht_b_variedades"></div>
    <div class="bilan-ultimas" id="ht_b_ultimas"></div>
    <button class="btn-secondary" onclick="huertoRecargarBalance()">🔄 Rafraîchir</button>
  </div>
</div>
```


### 3.2 CSS

```css
.huerto-form {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 8px;
  margin-bottom: 8px;
}
.huerto-form input, .huerto-form select {
  padding: 8px; border: 1px solid #ccc; border-radius: 6px; font-size: 14px;
}
.huerto-form button { grid-column: 1 / -1; }
.huerto-feedback { font-size: 13px; margin-top: 6px; min-height: 20px; }
.huerto-feedback.ok { color: #2d7a3e; }
.huerto-feedback.warn { color: #b36b00; }
.huerto-feedback.err { color: #c62828; }
.bilan-row { display: flex; gap: 12px; margin-bottom: 12px; flex-wrap: wrap; }
.bilan-cell {
  flex: 1; min-width: 120px;
  background: #f7f7f2; padding: 12px; border-radius: 8px; text-align: center;
}
.bilan-label { font-size: 12px; color: #666; text-transform: uppercase; }
.bilan-value { font-size: 24px; font-weight: 700; margin-top: 4px; }
.bilan-value.positive { color: #2d7a3e; }
.bilan-value.highlight { color: #d4a017; }
.bilan-variedades, .bilan-ultimas { font-size: 13px; margin-top: 8px; }
```

### 3.3 JS

```javascript
// ======= HUERTO TRACKING =======
async function huertoApi(action, body = null, query = '') {
  const token = sessionStorage.getItem('nv_token');
  const url = API_URL + '?action=' + action + (query ? '&' + query : '');
  const opts = { headers: { 'Content-Type': 'application/json', 'X-App-Token': token } };
  if (body) { opts.method = 'POST'; opts.body = JSON.stringify(body); }
  const r = await fetch(url, opts);
  if (!r.ok) throw new Error('HTTP ' + r.status);
  return r.json();
}

function huertoHoy() { return new Date().toISOString().slice(0, 10); }

async function huertoCargarVariedades() {
  try {
    const vs = await huertoApi('huerto_variedades_distinct');
    const dl = document.getElementById('ht_variedades');
    dl.innerHTML = '';
    vs.forEach(v => { const o = document.createElement('option'); o.value = v; dl.appendChild(o); });
  } catch (e) { console.warn('variedades', e); }
}

async function huertoGuardarGasto() {
  const fb = document.getElementById('ht_gasto_feedback');
  const body = {
    tipo: 'gasto',
    fecha: document.getElementById('ht_gasto_fecha').value || huertoHoy(),
    variedad: document.getElementById('ht_gasto_variedad').value.trim().toLowerCase(),
    cantidad: parseFloat(document.getElementById('ht_gasto_cantidad').value || 0),
    unidad: document.getElementById('ht_gasto_unidad').value,
    coste_eur: parseFloat(document.getElementById('ht_gasto_coste').value || 0),
    proveedor: document.getElementById('ht_gasto_proveedor').value.trim() || null,
    origen: document.getElementById('ht_gasto_origen').value
  };
  if (!body.variedad || !body.cantidad || !body.coste_eur) {
    fb.textContent = '⚠️ Variété, quantité et coût obligatoires';
    fb.className = 'huerto-feedback warn';
    return;
  }
  try {
    await huertoApi('huerto_entrada_add', body);
    fb.textContent = `✅ ${body.variedad} · ${body.coste_eur}€ enregistré`;
    fb.className = 'huerto-feedback ok';
    ['ht_gasto_cantidad','ht_gasto_coste','ht_gasto_variedad','ht_gasto_proveedor']
      .forEach(id => document.getElementById(id).value = '');
    huertoCargarVariedades();
    huertoRecargarBalance();
  } catch (e) {
    fb.textContent = '❌ ' + e.message;
    fb.className = 'huerto-feedback err';
  }
}

async function huertoGuardarCosecha() {
  const fb = document.getElementById('ht_cosecha_feedback');
  const body = {
    tipo: 'cosecha',
    fecha: document.getElementById('ht_cosecha_fecha').value || huertoHoy(),
    variedad: document.getElementById('ht_cosecha_variedad').value.trim().toLowerCase(),
    cantidad: parseFloat(document.getElementById('ht_cosecha_cantidad').value || 0),
    unidad: document.getElementById('ht_cosecha_unidad').value,
    nota: document.getElementById('ht_cosecha_nota').value.trim() || null
  };
  if (!body.variedad || !body.cantidad) {
    fb.textContent = '⚠️ Variété et quantité obligatoires';
    fb.className = 'huerto-feedback warn';
    return;
  }
  try {
    const r = await huertoApi('huerto_entrada_add', body);
    if (r.ahorro_eur !== null) {
      fb.textContent = `✅ Valeur marché : ${r.ahorro_eur}€`;
      fb.className = 'huerto-feedback ok';
    } else {
      fb.textContent = `✅ Enregistré — ${r.aviso_precio || 'prix à venir'}`;
      fb.className = 'huerto-feedback warn';
    }
    ['ht_cosecha_cantidad','ht_cosecha_variedad','ht_cosecha_nota']
      .forEach(id => document.getElementById(id).value = '');
    huertoCargarVariedades();
    huertoRecargarBalance();
  } catch (e) {
    fb.textContent = '❌ ' + e.message;
    fb.className = 'huerto-feedback err';
  }
}

async function huertoRecargarBalance() {
  try {
    const b = await huertoApi('huerto_balance');
    document.getElementById('ht_b_gasto').textContent = b.gasto_total.toFixed(2) + ' €';
    document.getElementById('ht_b_valor').textContent = b.valor_cosecha.toFixed(2) + ' €';
    const s = b.ahorro_neto >= 0 ? '+' : '';
    document.getElementById('ht_b_ahorro').textContent = s + b.ahorro_neto.toFixed(2) + ' €';

    const vs = document.getElementById('ht_b_variedades');
    vs.innerHTML = b.por_variedad && b.por_variedad.length
      ? '<strong>Top variétés :</strong><br>' + b.por_variedad.slice(0,5).map(v =>
          `${v.variedad} — récolte ${parseFloat(v.valor).toFixed(2)}€ / achat ${parseFloat(v.gasto).toFixed(2)}€`
        ).join('<br>') : '';

    const ultimas = await huertoApi('huerto_entradas_list', null, 'limit=5');
    document.getElementById('ht_b_ultimas').innerHTML =
      '<strong>Dernières :</strong><br>' + ultimas.map(e => {
        const icon = e.tipo === 'gasto' ? '💸' : '🧺';
        const eur = e.tipo === 'gasto' ? `-${e.coste_eur}€` : (e.ahorro_eur ? `+${e.ahorro_eur}€` : '—');
        return `${icon} ${e.fecha} · ${e.variedad} · ${e.cantidad}${e.unidad} · <b>${eur}</b>`;
      }).join('<br>');
  } catch (e) { console.warn('balance', e); }
}

document.addEventListener('DOMContentLoaded', () => {
  setTimeout(() => {
    if (sessionStorage.getItem('nv_token')) {
      document.getElementById('ht_gasto_fecha').value = huertoHoy();
      document.getElementById('ht_cosecha_fecha').value = huertoHoy();
      huertoCargarVariedades();
      huertoRecargarBalance();
    }
  }, 500);
});
```


---

## 4. TASK SEMANAL — Actualización automática de precios

Crear tool para el **unified-agent** que corre cada lunes 06:00.

**Archivo**: `/home/nosvers/unified-agent/tools/precios_huerto_scan.py`

```python
"""
precios_huerto_scan
Scheduler: lunes 06:00
Para cada variedad registrada, busca precio medio actual en Francia via web_search.
Actualiza huerto_precios_ref. Notifica a Angel cambios >15%.
"""
import os, json, re, requests
from datetime import date
from anthropic import Anthropic

API_URL = "https://nosvers.com/granja/api.php"
APP_TOKEN = os.getenv("NOSVERS_APP_TOKEN")
TELEGRAM_BOT = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_ANGEL = os.getenv("TELEGRAM_CHAT_ID_ANGEL")

def run():
    headers = {"X-App-Token": APP_TOKEN, "Content-Type": "application/json"}

    r = requests.get(f"{API_URL}?action=huerto_variedades_distinct", headers=headers)
    variedades = r.json()
    if not variedades:
        return {"ok": True, "msg": "Sin variedades aún"}

    r = requests.get(f"{API_URL}?action=huerto_precios_get", headers=headers)
    precios_actuales = {p["variedad"]: p for p in r.json()}

    client = Anthropic()
    updates = []
    cambios = []

    for variedad in variedades:
        if not variedad: continue
        prompt = (
            f"Cherche le prix moyen actuel en France de: {variedad} "
            f"(produit frais, bio si possible, €/kg). "
            f"Si vendu à la pièce/botte, donne aussi le poids moyen en grammes. "
            f'Réponds UNIQUEMENT en JSON strict: '
            f'{{"precio_eur_kg": <float>, "peso_unidad_g": <int|null>, "fuente": "<source>"}}'
        )
        try:
            msg = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=400,
                tools=[{"type": "web_search_20250305", "name": "web_search"}],
                messages=[{"role": "user", "content": prompt}]
            )
            text = "".join(b.text for b in msg.content if hasattr(b, "text"))
            m = re.search(r'\{[^{}]+\}', text)
            if not m: continue
            data = json.loads(m.group(0))
            nuevo = float(data["precio_eur_kg"])

            actual = precios_actuales.get(variedad, {}).get("precio_eur_kg")
            if actual and abs(nuevo - float(actual)) / float(actual) > 0.15:
                cambios.append(f"{variedad}: {actual}€ → {nuevo}€/kg")

            updates.append({
                "variedad": variedad,
                "precio_eur_kg": nuevo,
                "peso_unidad_g": data.get("peso_unidad_g"),
                "fuente": (data.get("fuente") or "web_search")[:200],
                "fecha_actualizacion": date.today().isoformat()
            })
        except Exception as e:
            print(f"Error {variedad}: {e}")
            continue

    if updates:
        requests.post(f"{API_URL}?action=huerto_precios_set",
                      headers=headers, json={"items": updates})

    if cambios and TELEGRAM_BOT and TELEGRAM_ANGEL:
        texto = "📊 Prix huerto — maj lundi\n\n" + "\n".join(cambios)
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT}/sendMessage",
                      json={"chat_id": TELEGRAM_ANGEL, "text": texto})

    return {"ok": True, "updated": len(updates), "cambios_grandes": len(cambios)}

if __name__ == "__main__":
    print(run())
```

**Registrar en scheduler del agente unificado**:

```python
# En el SCHEDULE del orchestrator interno del unified-agent
"06:00 lun": "precios_huerto_scan",
```


---

## 5. PLAN DE EJECUCIÓN (para Claude Code)

Ejecutar en este orden. No saltar pasos.

### Paso 1 — Migración SQL

```bash
# Leer credenciales DB
source <(php -r 'require "/home/nosvers/public_html/config.php";
  echo "export DB_H=" . escapeshellarg(DB_HOST) . "\n";
  echo "export DB_N=" . escapeshellarg(DB_NAME) . "\n";
  echo "export DB_U=" . escapeshellarg(DB_USER) . "\n";
  echo "export DB_P=" . escapeshellarg(DB_PASS) . "\n";
')
# Ejecutar los 2 CREATE del paso 1
mysql -h"$DB_H" -u"$DB_U" -p"$DB_P" "$DB_N" < /tmp/huerto_schema.sql
# Verificar
mysql -h"$DB_H" -u"$DB_U" -p"$DB_P" "$DB_N" -e "SHOW TABLES LIKE 'huerto_%';"
```

### Paso 2 — Backup y patch api.php

```bash
cp /home/nosvers/public_html/api.php /home/nosvers/public_html/api.php.bak_$(date +%Y%m%d_%H%M)
# Insertar los 6 nuevos `case` ANTES de `case 'default':` (o el último `default:`)
# Validar sintaxis PHP
php -l /home/nosvers/public_html/api.php
```

### Paso 3 — Test endpoints con curl

```bash
# Login → obtener token
TOKEN=$(curl -s -X POST "https://nosvers.com/granja/api.php?action=login" \
  -H "Content-Type: application/json" \
  -d '{"user":"<usuario>","pass":"<pwd>"}' | jq -r .token)

# Test gasto
curl -s -X POST "https://nosvers.com/granja/api.php?action=huerto_entrada_add" \
  -H "Content-Type: application/json" -H "X-App-Token: $TOKEN" \
  -d '{"tipo":"gasto","variedad":"laitue","cantidad":24,"unidad":"unidades","coste_eur":7.00,"proveedor":"Santasté","origen":"achat"}'

# Test balance
curl -s "https://nosvers.com/granja/api.php?action=huerto_balance" -H "X-App-Token: $TOKEN"

# Limpiar test
curl -s -X POST "https://nosvers.com/granja/api.php?action=huerto_entrada_delete" \
  -H "Content-Type: application/json" -H "X-App-Token: $TOKEN" -d '{"id":<ID>}'
```

### Paso 4 — Patch página /granja

La página `/granja/` es un post WordPress. Opciones para editarla:

1. **Vía wp-cli** (si instalado): `wp post get <ID> --field=post_content > /tmp/granja.html`, editar, luego `wp post update <ID> --post_content=@/tmp/granja.html`
2. **Vía phpMyAdmin**: editar directamente `wp_posts.post_content` del post con slug `granja`
3. **Vía WP Admin**: copiar HTML/CSS/JS y pegar en el editor de bloques (block "HTML personalizado")

Backup obligatorio antes:
```bash
mysqldump -h"$DB_H" -u"$DB_U" -p"$DB_P" "$DB_N" wp_posts --where="post_name='granja'" > /tmp/granja_backup_$(date +%Y%m%d).sql
```

Insertar:
- HTML de sección 3.1 tras el `</div>` de cierre del grid Potager actual
- CSS de sección 3.2 en el bloque `<style>` existente de la página
- JS de sección 3.3 al final del bloque `<script>` existente

### Paso 5 — Test UI en producción

1. Abrir `https://nosvers.com/granja/` en móvil y desktop → login
2. Scroll hasta 🌿 Potager → verificar 3 bloques nuevos visibles
3. Registrar 1 gasto de test + 1 cosecha de test
4. Verificar inserción en DB y en `vault/huerto/entradas-YYYY-MM.md`
5. Borrar las entradas de test con `huerto_entrada_delete`

### Paso 6 — Tool precios_huerto_scan

```bash
# Crear tool
mkdir -p /home/nosvers/unified-agent/tools
# Copiar código de sección 4 a /home/nosvers/unified-agent/tools/precios_huerto_scan.py
chmod +x /home/nosvers/unified-agent/tools/precios_huerto_scan.py

# Ejecutar manualmente para poblar precios iniciales
cd /home/nosvers/unified-agent && python3 tools/precios_huerto_scan.py

# Verificar
curl -s "https://nosvers.com/granja/api.php?action=huerto_precios_get" -H "X-App-Token: $TOKEN" | jq
```

Luego registrar en scheduler APScheduler del unified-agent: lunes 06:00.

### Paso 7 — Documentación y cierre

- Actualizar `vault/operaciones/evolution-roadmap.md` marcando feature como completada
- Crear `vault/huerto/README.md` con guía para África (en español, breve)
- Notificar a Angel por Telegram: "✅ Huerto tracking operativo"


---

## 6. CRITERIOS DE ACEPTACIÓN

- [ ] Tablas `huerto_entradas` y `huerto_precios_ref` creadas con sus índices
- [ ] 6 endpoints nuevos funcionan con token válido (probados con curl)
- [ ] 3 bloques UI visibles y funcionales en `/granja` (mobile + desktop)
- [ ] Al registrar cosecha con variedad con precio ref → muestra ahorro calculado
- [ ] Al registrar cosecha sin precio ref → avisa "Claude le cherchera lundi" (no rompe)
- [ ] Balance del mes se actualiza inmediatamente tras cada registro
- [ ] Fichero `vault/huerto/entradas-YYYY-MM.md` se crea y appendea tras cada entrada
- [ ] Task `precios_huerto_scan` corre manualmente OK
- [ ] El agente unificado lee `vault/huerto/` sin cambios adicionales
- [ ] Backup de api.php y de la página `/granja` realizados antes de los cambios

---

## 7. NOTAS OPERATIVAS

- **Auth**: reutiliza `validarToken()` que ya existe. No tocar.
- **Idioma UI**: francés (África interactúa con la app en francés).
- **Variedades**: siempre lowercase en BD (se hace con `strtolower` en el endpoint). Evita duplicados "Tomate"/"tomate".
- **Moneda**: EUR fijo.
- **Prefijo CSS/JS**: todas las clases y funciones nuevas usan `huerto-` o `ht_` para evitar colisiones con estilos existentes.
- **Fallback peso_unidad_g**: 200g si no hay valor en `huerto_precios_ref` (mejor que fallar).
- **Coste del scheduler semanal**: ~0.005€ × 20 variedades × 4 semanas = 0.40€/mes. Despreciable.

---

## 8. FAQ DURANTE LA EJECUCIÓN

**¿Y si `/granja` no es un template PHP sino un post de WordPress?**
→ Es un post. Editar via wp-cli (preferido), phpMyAdmin, o WP Admin (bloque HTML personalizado). El código va inline en el `post_content`.

**¿Conflictos con CSS existente?**
→ Prevenido con prefijo `huerto-`. Si aparece un issue, inspeccionar con devtools y aumentar especificidad.

**¿`vault_write` tiene restricciones de path?**
→ El endpoint `huerto_entrada_add` usa `file_put_contents` directamente sobre el path absoluto, no pasa por `vault_write`. Sin dependencias.

**¿Qué hago si el agente unificado no tiene aún `precios_huerto_scan` registrado?**
→ Ejecutarlo manualmente como cronjob temporal: `0 6 * * 1 cd /home/nosvers/unified-agent && python3 tools/precios_huerto_scan.py`. Migrar al scheduler interno cuando la FASE 3 del unified-agent lo permita.

**¿Modelo Claude para precios?**
→ Haiku 4.5 con web_search (`claude-haiku-4-5-20251001`). API key en `.env` del unified-agent (`ANTHROPIC_API_KEY`).

**¿Qué variables de entorno necesita `precios_huerto_scan.py`?**
→ `ANTHROPIC_API_KEY`, `NOSVERS_APP_TOKEN` (generar un token permanente en `config.php` o reutilizar uno existente), `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID_ANGEL`.

**¿Puede ejecutarse todo sin romper lo existente?**
→ Sí. Los cambios son aditivos: nuevas tablas, nuevos endpoints, nuevos bloques HTML. Si algo falla, borrar las 2 tablas y revertir `api.php` al backup.

---

## HANDOFF

**Estado**: blueprint completo, listo para ejecución.
**Ejecutor sugerido**: Claude Code con acceso al VPS vía SSH o MCP.
**Tiempo estimado**: 45-90 min de ejecución + testing.
**Dependencia crítica**: credenciales DB en `config.php` y token de login válido para tests.

Cualquier decisión no cubierta en este blueprint: **NO improvisar** — documentar en `vault/operaciones/huerto-tracking-decisiones-code.md` y pausar hasta validación de Angel.
