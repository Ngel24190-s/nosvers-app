<?php
// ============================================================
//  NosVers · API Backend
//  Fichier : api.php
//  À placer dans le même dossier que index.html sur Hostinger
// ============================================================

// ── Credenciales Hostinger NosVers ────────────────────────────
define('DB_HOST', 'localhost');
define('DB_NAME', 'u859094205_zqrpl');
define('DB_USER', 'u859094205_zqrpl'); // ⚠ confirma tu usuario MySQL en Hostinger
define('DB_PASS', 'TU_CONTRASEÑA');    // ⚠ pon aquí tu contraseña MySQL
define('CLAUDE_KEY', 'TU_NUEVA_API_KEY'); // ⚠ pon aquí tu nueva API key de Anthropic
// ──────────────────────────────────────────────────────────────

// CORS - permite que la app llame a esta API
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');
header('Content-Type: application/json; charset=utf-8');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(204);
    exit;
}

// Conexión PDO
try {
    $pdo = new PDO(
        "mysql:host=" . DB_HOST . ";dbname=" . DB_NAME . ";charset=utf8mb4",
        DB_USER,
        DB_PASS,
        [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]
    );
} catch (PDOException $e) {
    http_response_code(500);
    echo json_encode(['error' => 'DB connection failed: ' . $e->getMessage()]);
    exit;
}

$action = $_GET['action'] ?? '';

switch ($action) {

    // ── JOURNAL ──────────────────────────────────────────────

    case 'journal_get':
        $limit = (int)($_GET['limit'] ?? 60);
        $stmt = $pdo->prepare("SELECT * FROM journal ORDER BY created_at DESC LIMIT :lim");
        $stmt->bindValue(':lim', $limit, PDO::PARAM_INT);
        $stmt->execute();
        echo json_encode($stmt->fetchAll(PDO::FETCH_ASSOC));
        break;

    case 'journal_add':
        $data = json_decode(file_get_contents('php://input'), true);
        $stmt = $pdo->prepare(
            "INSERT INTO journal (domain, action, completed) VALUES (:domain, :action, :completed)"
        );
        $stmt->execute([
            ':domain'    => $data['domain']    ?? '',
            ':action'    => $data['action']    ?? '',
            ':completed' => $data['completed'] ?? 0,
        ]);
        echo json_encode(['ok' => true, 'id' => $pdo->lastInsertId()]);
        break;

    case 'journal_clear':
        $pdo->exec("TRUNCATE TABLE journal");
        echo json_encode(['ok' => true]);
        break;

    // ── INVENTAIRE ───────────────────────────────────────────

    case 'inventaire_get':
        $stmt = $pdo->query("SELECT cle, valeur FROM inventaire");
        $rows = $stmt->fetchAll(PDO::FETCH_KEY_PAIR);
        echo json_encode($rows);
        break;

    case 'inventaire_set':
        $data = json_decode(file_get_contents('php://input'), true);
        $stmt = $pdo->prepare(
            "INSERT INTO inventaire (cle, valeur) VALUES (:cle, :valeur)
             ON DUPLICATE KEY UPDATE valeur = :valeur2"
        );
        foreach ($data as $cle => $valeur) {
            $stmt->execute([
                ':cle'    => $cle,
                ':valeur' => (float)$valeur,
                ':valeur2'=> (float)$valeur,
            ]);
        }
        echo json_encode(['ok' => true]);
        break;

    // ── CHECKLIST ────────────────────────────────────────────

    case 'checklist_get':
        $jour = date('Y-m-d');
        $stmt = $pdo->prepare(
            "SELECT task_id, done FROM checklist WHERE jour = :jour"
        );
        $stmt->execute([':jour' => $jour]);
        $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);
        $result = [];
        foreach ($rows as $r) {
            $result[$r['task_id']] = (bool)$r['done'];
        }
        echo json_encode($result);
        break;

    case 'checklist_set':
        $data = json_decode(file_get_contents('php://input'), true);
        $jour = date('Y-m-d');
        $stmt = $pdo->prepare(
            "INSERT INTO checklist (task_id, jour, done) VALUES (:tid, :jour, :done)
             ON DUPLICATE KEY UPDATE done = :done2"
        );
        foreach ($data as $tid => $done) {
            $stmt->execute([
                ':tid'   => $tid,
                ':jour'  => $jour,
                ':done'  => $done ? 1 : 0,
                ':done2' => $done ? 1 : 0,
            ]);
        }
        echo json_encode(['ok' => true]);
        break;

    // ── AGENTE IA (proxy seguro hacia Claude) ───────────────
    case 'agente':
        $data = json_decode(file_get_contents('php://input'), true);
        if (empty($data['system']) || empty($data['user'])) {
            http_response_code(400);
            echo json_encode(['error' => 'Faltan parámetros system/user']);
            break;
        }

        $payload = json_encode([
            'model'      => 'claude-sonnet-4-5-20250929',
            'max_tokens' => 1000,
            'system'     => $data['system'],
            'messages'   => [['role' => 'user', 'content' => $data['user']]]
        ]);

        $ch = curl_init('https://api.anthropic.com/v1/messages');
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_POST           => true,
            CURLOPT_POSTFIELDS     => $payload,
            CURLOPT_HTTPHEADER     => [
                'Content-Type: application/json',
                'x-api-key: ' . CLAUDE_KEY,
                'anthropic-version: 2023-06-01'
            ],
            CURLOPT_TIMEOUT        => 60,
        ]);

        $resp   = curl_exec($ch);
        $status = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $err    = curl_error($ch);
        curl_close($ch);

        if ($err) {
            http_response_code(500);
            echo json_encode(['error' => 'cURL: ' . $err]);
            break;
        }

        http_response_code($status);
        echo $resp;
        break;

    default:
        http_response_code(400);
        echo json_encode(['error' => 'Action inconnue: ' . $action]);
        break;
}
