<?php
/**
 * Proxy PHP para formulario CONECTA
 * Recibe POST del formulario HTML y lo reenvía a la API del VPS
 */
header('Content-Type: application/json');

// Solo aceptar POST
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['ok' => false, 'error' => 'Solo POST']);
    exit;
}

// Leer JSON del body
$json = file_get_contents('php://input');
$data = json_decode($json, true);

// Validar campos requeridos
$required = ['name', 'company', 'role', 'phone', 'email', 'service', 'urgency'];
foreach ($required as $field) {
    if (empty($data[$field])) {
        http_response_code(400);
        echo json_encode(['ok' => false, 'error' => "Falta campo: $field"]);
        exit;
    }
}

// Reenviar a la API del VPS
$api_url = 'http://76.13.239.113:8091/form';
$ch = curl_init($api_url);
curl_setopt_array($ch, [
    CURLOPT_POST => true,
    CURLOPT_POSTFIELDS => json_encode($data),
    CURLOPT_HTTPHEADER => ['Content-Type: application/json'],
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_TIMEOUT => 15,
]);

$response = curl_exec($ch);
$http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

http_response_code($http_code);
echo $response;
