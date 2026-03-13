<?php
// ============================================================
//  Knowledge Base Search API
//  Búsqueda en base de conocimiento markdown
// ============================================================

header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');

$action = $_GET['action'] ?? '';
$kb_path = __DIR__ . '/knowledge_base';

// Simple keyword search in markdown files
function searchKB($keywords, $category = null) {
    global $kb_path;
    
    $keywords = array_map('trim', array_filter(explode(' ', strtolower($keywords))));
    if (empty($keywords)) return [];
    
    $results = [];
    $categories = $category ? [$category] : array_diff(scandir($kb_path), ['.', '..']);
    
    foreach ($categories as $cat) {
        $cat_path = $kb_path . '/' . $cat;
        if (!is_dir($cat_path)) continue;
        
        $files = array_diff(scandir($cat_path), ['.', '..']);
        foreach ($files as $file) {
            if (!str_ends_with($file, '.md')) continue;
            
            $filepath = $cat_path . '/' . $file;
            $content = file_get_contents($filepath);
            $content_lower = strtolower($content);
            
            // Calculate relevance score
            $score = 0;
            $matched_keywords = [];
            foreach ($keywords as $kw) {
                $count = substr_count($content_lower, $kw);
                if ($count > 0) {
                    $score += $count;
                    $matched_keywords[] = $kw;
                }
            }
            
            if ($score > 0) {
                // Extract relevant chunks (paragraphs containing keywords)
                $lines = explode("\n", $content);
                $chunks = [];
                $current_chunk = [];
                
                foreach ($lines as $line) {
                    $line_lower = strtolower($line);
                    $has_keyword = false;
                    foreach ($keywords as $kw) {
                        if (strpos($line_lower, $kw) !== false) {
                            $has_keyword = true;
                            break;
                        }
                    }
                    
                    if ($has_keyword || !empty($current_chunk)) {
                        $current_chunk[] = $line;
                        if (empty(trim($line)) && count($current_chunk) > 2) {
                            $chunks[] = implode("\n", $current_chunk);
                            $current_chunk = [];
                        }
                    }
                }
                if (!empty($current_chunk)) {
                    $chunks[] = implode("\n", $current_chunk);
                }
                
                // Keep top 3 most relevant chunks
                $chunks = array_slice($chunks, 0, 3);
                
                $results[] = [
                    'category' => $cat,
                    'file' => str_replace('.md', '', $file),
                    'score' => $score,
                    'matched_keywords' => $matched_keywords,
                    'chunks' => $chunks,
                    'full_path' => "$cat/$file"
                ];
            }
        }
    }
    
    // Sort by relevance
    usort($results, fn($a, $b) => $b['score'] - $a['score']);
    
    return array_slice($results, 0, 5); // Top 5 results
}

// Get full content of a specific file
function getKBFile($category, $file) {
    global $kb_path;
    $filepath = $kb_path . '/' . $category . '/' . $file . '.md';
    if (!file_exists($filepath)) {
        return ['error' => 'File not found'];
    }
    return [
        'category' => $category,
        'file' => $file,
        'content' => file_get_contents($filepath)
    ];
}

// List all categories and files
function listKB() {
    global $kb_path;
    $structure = [];
    $categories = array_diff(scandir($kb_path), ['.', '..']);
    
    foreach ($categories as $cat) {
        $cat_path = $kb_path . '/' . $cat;
        if (!is_dir($cat_path)) continue;
        
        $files = array_diff(scandir($cat_path), ['.', '..']);
        $structure[$cat] = array_map(fn($f) => str_replace('.md', '', $f), 
                                     array_filter($files, fn($f) => str_ends_with($f, '.md')));
    }
    
    return $structure;
}

switch ($action) {
    case 'search':
        $keywords = $_GET['q'] ?? '';
        $category = $_GET['category'] ?? null;
        echo json_encode(searchKB($keywords, $category));
        break;
        
    case 'get':
        $category = $_GET['category'] ?? '';
        $file = $_GET['file'] ?? '';
        echo json_encode(getKBFile($category, $file));
        break;
        
    case 'list':
        echo json_encode(listKB());
        break;
        
    default:
        http_response_code(400);
        echo json_encode(['error' => 'Invalid action']);
}
