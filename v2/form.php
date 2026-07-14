<?php
header('Content-Type: application/json');
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['ok' => false, 'error' => 'Solo POST']);
    exit;
}
$raw = file_get_contents('php://input');
$data = json_decode($raw, true);
if (!$data || json_last_error() !== JSON_ERROR_NONE) {
    $data = $_POST;
}
$required = ['name', 'company', 'email', 'phone'];
foreach ($required as $f) {
    if (empty($data[$f])) {
        http_response_code(400);
        echo json_encode(['ok' => false, 'error' => "Falta: $f"]);
        exit;
    }
}
$svc = $data['service'] ?? 'No especificado';
$html = "<html><body><h2>Nuevo Lead CONECTA</h2><p><b>Nombre:</b> {$data['name']}<br><b>Empresa:</b> {$data['company']}<br><b>Email:</b> {$data['email']}<br><b>Telefono:</b> {$data['phone']}<br><b>Servicio:</b> $svc</p></body></html>";
$ch = curl_init('https://api.postmarkapp.com/email');
curl_setopt_array($ch, [
    CURLOPT_POST => true,
    CURLOPT_HTTPHEADER => ['Accept: application/json', 'Content-Type: application/json', 'X-Postmark-Server-Token: 8b3d04b1-ebbb-460e-9373-aec2ca8442c8'],
    CURLOPT_POSTFIELDS => json_encode(['From' => 'victor.vilche@conecta.cl', 'To' => 'victor.vilche@conecta.cl', 'Subject' => "Nuevo Lead: {$data['company']}", 'HtmlBody' => $html]),
    CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 10
]);
$result = curl_exec($ch);
$httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);
if ($httpCode === 200) {
    echo json_encode(['ok' => true, 'message' => 'Recibido. Te contactaremos pronto.']);
} else {
    http_response_code(500);
    echo json_encode(['ok' => false, 'error' => 'Error interno. Intenta de nuevo.']);
}
