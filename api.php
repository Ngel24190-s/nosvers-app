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

        $payload = json_encode(['model' => 'claude-sonnet-4-5-20250929', 'max_tokens' => 1200, 'system' => $data['system'], 'messages' => [['role' => 'user', 'content' => $userContent]]]);
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

    default:
        http_response_code(400);
        echo json_encode(['error' => 'Accion desconocida: ' . $action]);
        break;
}
