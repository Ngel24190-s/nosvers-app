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
        if (empty($image)) { http_response_code(400); echo json_encode(['error' => 'No image']); break; }
        $imageData = base64_decode($image);
        if ($imageData === false) { http_response_code(400); echo json_encode(['error' => 'Invalid base64']); break; }
        $ext = 'jpg';
        if (strpos($type, 'png') !== false) $ext = 'png';
        elseif (strpos($type, 'webp') !== false) $ext = 'webp';
        $uploadDir = __DIR__ . '/uploads/' . $user;
        if (!is_dir($uploadDir)) mkdir($uploadDir, 0755, true);
        $filename = date('Y-m-d_His') . '_' . bin2hex(random_bytes(4)) . '.' . $ext;
        $filepath = $uploadDir . '/' . $filename;
        if (file_put_contents($filepath, $imageData) === false) { http_response_code(500); echo json_encode(['error' => 'Save failed']); break; }
        try {
            $stmt = $pdo->prepare("INSERT INTO journal (domain, action, completed) VALUES (:d, :a, 1)");
            $stmt->execute([':d' => $user, ':a' => 'Photo: ' . $filename . ($note ? ' - ' . $note : '')]);
        } catch (Exception $e) {}
        $baseUrl = (isset($_SERVER['HTTPS']) && $_SERVER['HTTPS'] === 'on' ? 'https' : 'http') . '://' . $_SERVER['HTTP_HOST'];
        echo json_encode(['ok' => true, 'filename' => $filename, 'url' => $baseUrl . '/granja/uploads/' . $user . '/' . $filename, 'size' => strlen($imageData)]);
        break;

    default:
        http_response_code(400);
        echo json_encode(['error' => 'Accion desconocida: ' . $action]);
        break;
}
