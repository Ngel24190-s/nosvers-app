<?php
// ============================================================
//  NosVers · API Backend
//  Este archivo SI va a GitHub (sin credenciales)
//  Las credenciales estan en config.php (solo en Hostinger)
// ============================================================

$config = __DIR__ . '/config.php';
if (!file_exists($config)) {
    http_response_code(500);
    echo json_encode(['error' => 'config.php no encontrado en el servidor']);
    exit;
}
require_once $config;

header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, X-App-Token');
header('Content-Type: application/json; charset=utf-8');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(204);
    exit;
}

$action = $_GET['action'] ?? '';

if ($action !== 'login') {
    $token = $_SERVER['HTTP_X_APP_TOKEN'] ?? '';
    if (!validarToken($token)) {
        http_response_code(401);
        echo json_encode(['error' => 'No autorizado']);
        exit;
    }
}

function validarToken($token) {
    if (empty($token)) return false;
    $decoded = base64_decode($token);
    if (!$decoded || strpos($decoded, ':') === false) return false;
    list($user, $pass) = explode(':', $decoded, 2);
    $users = APP_USERS;
    return isset($users[$user]) && $users[$user] === $pass;
}

try {
    $pdo = new PDO(
        "mysql:host=" . DB_HOST . ";dbname=" . DB_NAME . ";charset=utf8mb4",
        DB_USER, DB_PASS,
        [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]
    );
} catch (PDOException $e) {
    http_response_code(500);
    echo json_encode(['error' => 'DB connection failed: ' . $e->getMessage()]);
    exit;
}

switch ($action) {

    case 'login':
        $data = json_decode(file_get_contents('php://input'), true);
        $user = trim($data['user'] ?? '');
        $pass = trim($data['pass'] ?? '');
        $users = APP_USERS;
        if (isset($users[$user]) && $users[$user] === $pass) {
            $token = base64_encode($user . ':' . $pass);
            echo json_encode(['ok' => true, 'token' => $token, 'user' => $user]);
        } else {
            http_response_code(401);
            echo json_encode(['error' => 'Usuario o contrasena incorrectos']);
        }
        break;

    case 'journal_get':
        $limit = (int)($_GET['limit'] ?? 60);
        $stmt = $pdo->prepare("SELECT * FROM journal ORDER BY created_at DESC LIMIT :lim");
        $stmt->bindValue(':lim', $limit, PDO::PARAM_INT);
        $stmt->execute();
        echo json_encode($stmt->fetchAll(PDO::FETCH_ASSOC));
        break;

    case 'journal_add':
        $data = json_decode(file_get_contents('php://input'), true);
        $stmt = $pdo->prepare("INSERT INTO journal (domain, action, completed) VALUES (:domain, :action, :completed)");
        $stmt->execute([':domain' => $data['domain'] ?? '', ':action' => $data['action'] ?? '', ':completed' => $data['completed'] ?? 0]);
        echo json_encode(['ok' => true, 'id' => $pdo->lastInsertId()]);
        break;

    case 'journal_clear':
        $pdo->exec("TRUNCATE TABLE journal");
        echo json_encode(['ok' => true]);
        break;

    case 'inventaire_get':
        $stmt = $pdo->query("SELECT cle, valeur FROM inventaire");
        echo json_encode($stmt->fetchAll(PDO::FETCH_KEY_PAIR));
        break;

    case 'inventaire_set':
        $data = json_decode(file_get_contents('php://input'), true);
        $stmt = $pdo->prepare("INSERT INTO inventaire (cle, valeur) VALUES (:cle, :valeur) ON DUPLICATE KEY UPDATE valeur = :valeur2");
        foreach ($data as $cle => $valeur) {
            $stmt->execute([':cle' => $cle, ':valeur' => (float)$valeur, ':valeur2' => (float)$valeur]);
        }
        echo json_encode(['ok' => true]);
        break;

    case 'checklist_get':
        $jour = date('Y-m-d');
        $stmt = $pdo->prepare("SELECT task_id, done FROM checklist WHERE jour = :jour");
        $stmt->execute([':jour' => $jour]);
        $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);
        $result = [];
        foreach ($rows as $r) { $result[$r['task_id']] = (bool)$r['done']; }
        echo json_encode($result);
        break;

    case 'checklist_set':
        $data = json_decode(file_get_contents('php://input'), true);
        $jour = date('Y-m-d');
        $stmt = $pdo->prepare("INSERT INTO checklist (task_id, jour, done) VALUES (:tid, :jour, :done) ON DUPLICATE KEY UPDATE done = :done2");
        foreach ($data as $tid => $done) {
            $stmt->execute([':tid' => $tid, ':jour' => $jour, ':done' => $done ? 1 : 0, ':done2' => $done ? 1 : 0]);
        }
        echo json_encode(['ok' => true]);
        break;

    case 'etat_get':
        $stmt = $pdo->query("SELECT cle, valeur FROM inventaire WHERE cle LIKE 'etat_%'");
        $rows = $stmt->fetchAll(PDO::FETCH_KEY_PAIR);
        echo json_encode($rows);
        break;

    case 'etat_set':
        $data = json_decode(file_get_contents('php://input'), true);
        $stmt = $pdo->prepare(
            "INSERT INTO inventaire (cle, valeur) VALUES (:cle, :valeur)
             ON DUPLICATE KEY UPDATE valeur = :valeur2"
        );
        foreach ($data as $cle => $valeur) {
            if (strpos($cle, 'etat_') === 0) {
                $stmt->execute([':cle' => $cle, ':valeur' => $valeur, ':valeur2' => $valeur]);
            }
        }
        echo json_encode(['ok' => true]);
        break;

    case 'agente':
        $data = json_decode(file_get_contents('php://input'), true);
        if (empty($data['system'])) {
            http_response_code(400);
            echo json_encode(['error' => 'Falta parametro system']);
            break;
        }
        if (empty($data['user']) && empty($data['user_content'])) {
            http_response_code(400);
            echo json_encode(['error' => 'Falta parametro user o user_content']);
            break;
        }

        // Build message content - text only, text+image, or full content array
        if (!empty($data['user_content']) && is_array($data['user_content'])) {
            // Full content array passed directly (huerto photo analysis)
            $userContent = $data['user_content'];
        } elseif (!empty($data['image_base64'])) {
            $imageType = $data['image_type'] ?? 'image/jpeg';
            $userContent = [
                ['type' => 'image', 'source' => ['type' => 'base64', 'media_type' => $imageType, 'data' => $data['image_base64']]],
                ['type' => 'text', 'text' => $data['user']]
            ];
        } else {
            $userContent = $data['user'];
        }

        // Historial conversacional (campo 'messages' opcional desde chat.html)
        if (!empty($data['messages']) && is_array($data['messages'])) {
            $msgs = $data['messages'];
            // Si el último mensaje es user, reemplazar content con el procesado (puede tener imagen)
            for ($i = count($msgs)-1; $i >= 0; $i--) {
                if ($msgs[$i]['role'] === 'user') { $msgs[$i]['content'] = $userContent; break; }
            }
        } else {
            $msgs = [['role' => 'user', 'content' => $userContent]];
        }
        $model = $data['model'] ?? 'claude-sonnet-4-6';
        $payload = json_encode(['model' => $model, 'max_tokens' => 1500, 'system' => $data['system'], 'messages' => $msgs]);
        $ch = curl_init('https://api.anthropic.com/v1/messages');
        curl_setopt_array($ch, [CURLOPT_RETURNTRANSFER => true, CURLOPT_POST => true, CURLOPT_POSTFIELDS => $payload, CURLOPT_HTTPHEADER => ['Content-Type: application/json', 'x-api-key: ' . CLAUDE_KEY, 'anthropic-version: 2023-06-01'], CURLOPT_TIMEOUT => 60]);
        $resp = curl_exec($ch);
        $status = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $err = curl_error($ch);
        curl_close($ch);
        if ($err) { http_response_code(500); echo json_encode(['error' => 'cURL: ' . $err]); break; }
        http_response_code($status);
        echo $resp;
        break;

    // ============================================================
    //  VAULT WRITE — Nuevo endpoint para api.php
    //  Añadir dentro del switch($action) en api.php
    //  Escribe/actualiza archivos Markdown en la knowledge_base
    // ============================================================

    case 'vault_write':
        $data = json_decode(file_get_contents('php://input'), true);
        
        // Parámetros requeridos
        $category = preg_replace('/[^a-z0-9_-]/', '', strtolower($data['category'] ?? ''));
        $filename  = preg_replace('/[^a-z0-9_-]/', '', strtolower($data['filename'] ?? ''));
        $content   = $data['content'] ?? '';
        $mode      = $data['mode'] ?? 'append'; // 'append' o 'overwrite'

        if (!$category || !$filename || !$content) {
            http_response_code(400);
            echo json_encode(['error' => 'Faltan category, filename o content']);
            break;
        }

        $kb_path  = __DIR__ . '/knowledge_base';
        $cat_path = $kb_path . '/' . $category;
        $filepath = $cat_path . '/' . $filename . '.md';

        // Crear carpeta de categoría si no existe
        if (!is_dir($cat_path)) {
            mkdir($cat_path, 0755, true);
        }

        $timestamp = date('Y-m-d H:i:s');
        $entry = "

---
*Actualizado: {$timestamp}*

" . $content;

        if ($mode === 'overwrite' || !file_exists($filepath)) {
            // Crear o sobreescribir con header
            $header = "# " . ucfirst(str_replace('-', ' ', $filename)) . "
";
            $header .= "*Categoría: {$category} · Creado: {$timestamp}*
";
            file_put_contents($filepath, $header . "
" . $content);
        } else {
            // Append — añadir al final con separador
            file_put_contents($filepath, $entry, FILE_APPEND);
        }

        // Actualizar agent_memory.json
        $memory_path = __DIR__ . '/agent_memory.json';
        $memory = file_exists($memory_path) 
            ? json_decode(file_get_contents($memory_path), true) 
            : [];
        
        $memory[$category]['last_vault_write'] = $timestamp;
        $memory[$category]['last_file']        = $filename . '.md';
        
        file_put_contents($memory_path, json_encode($memory, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));

        echo json_encode([
            'ok'       => true,
            'file'     => $category . '/' . $filename . '.md',
            'mode'     => $mode,
            'timestamp'=> $timestamp
        ]);
        break;

    // ============================================================
    //  VAULT READ — Leer un archivo Markdown de la knowledge_base
    // ============================================================

    case 'vault_read':
        $category = preg_replace('/[^a-z0-9_-]/', '', strtolower($_GET['category'] ?? ''));
        $filename  = preg_replace('/[^a-z0-9_-]/', '', strtolower($_GET['filename'] ?? ''));

        if (!$category || !$filename) {
            http_response_code(400);
            echo json_encode(['error' => 'Faltan category y filename']);
            break;
        }

        $filepath = __DIR__ . '/knowledge_base/' . $category . '/' . $filename . '.md';
        
        if (!file_exists($filepath)) {
            http_response_code(404);
            echo json_encode(['error' => 'Archivo no encontrado', 'path' => $category . '/' . $filename . '.md']);
            break;
        }

        echo json_encode([
            'ok'      => true,
            'category'=> $category,
            'filename'=> $filename . '.md',
            'content' => file_get_contents($filepath),
            'size'    => filesize($filepath),
            'modified'=> date('Y-m-d H:i:s', filemtime($filepath))
        ]);
        break;

    // ============================================================
    //  VAULT LIST — Listar todos los archivos de la vault
    // ============================================================

    case 'vault_list':
        $kb_path = __DIR__ . '/knowledge_base';
        $category = preg_replace('/[^a-z0-9_-]/', '', strtolower($_GET['category'] ?? ''));
        
        $result = [];
        $cats = $category ? [$category] : array_diff(scandir($kb_path), ['.', '..']);
        
        foreach ($cats as $cat) {
            $cat_path = $kb_path . '/' . $cat;
            if (!is_dir($cat_path)) continue;
            $files = array_diff(scandir($cat_path), ['.', '..']);
            foreach ($files as $f) {
                if (!str_ends_with($f, '.md')) continue;
                $fp = $cat_path . '/' . $f;
                $result[] = [
                    'category' => $cat,
                    'file'     => $f,
                    'size'     => filesize($fp),
                    'modified' => date('Y-m-d H:i:s', filemtime($fp))
                ];
            }
        }
        echo json_encode(['ok' => true, 'files' => $result, 'total' => count($result)]);
        break;


    // ============================================================
    //  UPLOAD PHOTO
    // ============================================================
    case 'upload_photo':
        $data = json_decode(file_get_contents('php://input'), true);
        $image = $data['image'] ?? '';
        $type = $data['type'] ?? 'image/jpeg';
        $user = preg_replace('/[^a-z0-9_-]/', '', strtolower($data['user'] ?? 'unknown'));
        $note = $data['note'] ?? '';
        $category = preg_replace('/[^a-z0-9_-]/', '', strtolower($data['category'] ?? 'general'));
        $agent = preg_replace('/[^a-z0-9_-]/', '', strtolower($data['agent'] ?? ''));
        $validCats = ['instagram', 'huerto', 'vers', 'produits', 'general', 'animaux', 'ferme', 'compost'];
        if (!in_array($category, $validCats)) $category = 'general';
        if (empty($image)) { http_response_code(400); echo json_encode(['error' => 'No image']); break; }
        $imageData = base64_decode($image);
        if ($imageData === false) { http_response_code(400); echo json_encode(['error' => 'Invalid base64']); break; }
        $ext = 'jpg';
        if (strpos($type, 'png') !== false) $ext = 'png';
        elseif (strpos($type, 'webp') !== false) $ext = 'webp';
        // Organize by category
        $uploadDir = __DIR__ . '/uploads/' . $category;
        if (!is_dir($uploadDir)) mkdir($uploadDir, 0755, true);
        $filename = date('Y-m-d_His') . '_' . $category . '_' . bin2hex(random_bytes(4)) . '.' . $ext;
        $filepath = $uploadDir . '/' . $filename;
        if (file_put_contents($filepath, $imageData) === false) { http_response_code(500); echo json_encode(['error' => 'Save failed']); break; }
        try {
            $stmt = $pdo->prepare("INSERT INTO journal (domain, action, completed) VALUES (:d, :a, 1)");
            $noteStr = $category . ': ' . $filename . ($note ? ' - ' . $note : '') . ($agent ? ' [' . $agent . ']' : '');
            $stmt->execute([':d' => $user, ':a' => 'Photo: ' . $noteStr]);
        } catch (Exception $e) {}
        // Write to photos log file for agents
        $logLine = date('Y-m-d H:i') . " | $user | $category | $note | $filename | pending_drive_sync\n";
        file_put_contents(__DIR__ . '/uploads/photos_log.txt', $logLine, FILE_APPEND);
        $baseUrl = (isset($_SERVER['HTTPS']) && $_SERVER['HTTPS'] === 'on' ? 'https' : 'http') . '://' . $_SERVER['HTTP_HOST'];
        echo json_encode(['ok' => true, 'filename' => $filename, 'url' => $baseUrl . '/granja/uploads/' . $user . '/' . $filename, 'size' => strlen($imageData)]);
        break;

    // ============================================================
    //  PROCESS PHOTO INSTAGRAM — Edita foto con AGT-01 y devuelve base64
    // ============================================================
    case 'process_photo_instagram':
        $data = json_decode(file_get_contents('php://input'), true);
        $image_b64   = $data['image_base64'] ?? '';
        $caption_hint = $data['caption_hint'] ?? '';
        $image_type  = $data['image_type'] ?? 'image/jpeg';

        if (empty($image_b64)) {
            http_response_code(400);
            echo json_encode(['error' => 'Falta image_base64']);
            break;
        }

        // Decode y guardar en /tmp/
        $ext       = (strpos($image_type, 'png') !== false) ? 'png' : 'jpg';
        $tmp_in    = '/tmp/nosvers_ig_in_' . bin2hex(random_bytes(4)) . '.' . $ext;
        $tmp_out   = '/tmp/nosvers_ig_out_' . bin2hex(random_bytes(4)) . '.jpg';
        $img_bytes = base64_decode($image_b64);

        if ($img_bytes === false || file_put_contents($tmp_in, $img_bytes) === false) {
            http_response_code(500);
            echo json_encode(['error' => 'No se pudo guardar la imagen temporal']);
            break;
        }

        // Llamar a AGT-01 para editar
        $payload_json = json_encode(['input_path' => $tmp_in, 'output_path' => $tmp_out]);
        $cmd = '/home/nosvers/venv/bin/python3 /home/nosvers/agents/agt01_visual.py process ' . escapeshellarg($payload_json) . ' 2>&1';
        $output = shell_exec($cmd);
        @unlink($tmp_in);

        $result = json_decode(trim($output), true);
        if (empty($result['ok'])) {
            http_response_code(500);
            echo json_encode(['error' => 'AGT-01 error: ' . ($result['error'] ?? $output)]);
            break;
        }

        // Devolver imagen editada como base64 + sugerencia de caption
        $edited_b64 = $result['base64'] ?? base64_encode(file_get_contents($tmp_out));
        @unlink($tmp_out);

        echo json_encode([
            'ok'              => true,
            'edited_base64'   => $edited_b64,
            'caption_hint'    => $caption_hint,
            'output_path'     => $result['output_path'] ?? $tmp_out,
        ]);
        break;

    // ============================================================
    //  PUBLISH INSTAGRAM — Publica foto llamando a AGT-02
    // ============================================================
    case 'publish_instagram':
        $data       = json_decode(file_get_contents('php://input'), true);
        $image_path = $data['image_path'] ?? '';
        $caption    = $data['caption'] ?? '';

        if (empty($image_path) || empty($caption)) {
            http_response_code(400);
            echo json_encode(['error' => 'Faltan image_path y caption']);
            break;
        }

        // Seguridad: solo rutas bajo /tmp/ o /home/nosvers/uploads/
        if (!str_starts_with($image_path, '/tmp/') && !str_starts_with($image_path, '/home/nosvers/uploads/')) {
            http_response_code(403);
            echo json_encode(['error' => 'Ruta no permitida']);
            break;
        }

        $payload_json = json_encode(['image_path' => $image_path, 'caption' => $caption]);
        $cmd = '/home/nosvers/venv/bin/python3 /home/nosvers/agents/agt02_instagram.py --publish-single ' . escapeshellarg($payload_json) . ' 2>&1';
        $output = shell_exec($cmd);

        $result = json_decode(trim($output), true);
        if (empty($result['ok'])) {
            http_response_code(500);
            echo json_encode(['error' => 'AGT-02 error: ' . ($result['error'] ?? $output)]);
            break;
        }

        echo json_encode([
            'ok'            => true,
            'instagram_url' => $result['instagram_url'] ?? '',
            'post_id'       => $result['post_id'] ?? '',
        ]);
        break;

    // ============================================================
    //  LIST PHOTOS — by category
    // ============================================================
    case 'list_photos':
        $category = preg_replace('/[^a-z0-9_-]/', '', strtolower($_GET['category'] ?? ''));
        $uploadsBase = __DIR__ . '/uploads/';
        $result = [];
        
        $cats = $category ? [$category] : ['instagram', 'huerto', 'vers', 'produits', 'general', 'animaux', 'ferme', 'compost'];
        foreach ($cats as $cat) {
            $catDir = $uploadsBase . $cat;
            if (!is_dir($catDir)) continue;
            $files = array_diff(scandir($catDir, SCANDIR_SORT_DESCENDING), ['.', '..']);
            foreach ($files as $f) {
                $fp = $catDir . '/' . $f;
                if (!is_file($fp)) continue;
                $result[] = [
                    'category' => $cat,
                    'filename' => $f,
                    'size' => filesize($fp),
                    'date' => date('Y-m-d H:i', filemtime($fp)),
                    'url' => 'uploads/' . $cat . '/' . $f,
                    'drive_synced' => false
                ];
            }
        }
        echo json_encode(['ok' => true, 'photos' => $result, 'total' => count($result)]);
        break;

    // ============================================================
    //  HUERTO TRACKING — 6 endpoints
    // ============================================================

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

    case 'huerto_entrada_delete':
        $data = json_decode(file_get_contents('php://input'), true);
        $id = (int)($data['id'] ?? 0);
        if (!$id) { http_response_code(400); echo json_encode(['error'=>'id requerido']); break; }
        $stmt = $pdo->prepare("DELETE FROM huerto_entradas WHERE id = :id");
        $stmt->execute([':id' => $id]);
        echo json_encode(['ok' => true, 'deleted' => $stmt->rowCount()]);
        break;

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

    case 'huerto_variedades_distinct':
        $stmt = $pdo->query(
            "SELECT DISTINCT variedad FROM huerto_entradas
             UNION
             SELECT variedad FROM huerto_precios_ref
             ORDER BY 1"
        );
        echo json_encode($stmt->fetchAll(PDO::FETCH_COLUMN));
        break;

    default:
        http_response_code(400);
        echo json_encode(['error' => 'Accion desconocida: ' . $action]);
        break;
}
