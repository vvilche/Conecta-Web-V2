<?php
/**
 * Formulario CONECTA — Email via Postmark
 */
header('Content-Type: application/json');

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['ok' => false, 'error' => 'Solo POST']);
    exit;
}

$data = json_decode(file_get_contents('php://input'), true);
$required = ['name', 'company', 'role', 'phone', 'email', 'service', 'urgency'];
foreach ($required as $f) {
    if (empty($data[$f])) {
        http_response_code(400);
        echo json_encode(['ok' => false, 'error' => "Falta: $f"]);
        exit;
    }
}

$svc = [
    'RTU'=>'RTU / Cambio de Remotas','PMU'=>'PMU / Telemedida',
    'SCADA'=>'SCADA / EMS','DCS'=>'DCS / Control de Procesos',
    'Instrumentacion'=>'Instrumentación / Equipos','Ciberseguridad'=>'Ciberseguridad OT',
    'Protecciones'=>'Protecciones / EDAC','BESS'=>'BESS / PMGD',
    'Consultoria'=>'Consultoría / Auditoría','Otro'=>'Otro'
][$data['service']] ?? $data['service'];

$urg = [
    'inmediata'=>'Inmediata','este_mes'=>'Este mes',
    'este_trimestre'=>'Este trimestre','cotizacion'=>'Solo cotización'
][$data['urgency']] ?? $data['urgency'];

$now = date('d/m/Y H:i');

$html = "<html><body style=\"font-family:Inter,sans-serif;padding:20px;background:#F1F5F9\">
<div style=\"max-width:520px;margin:0 auto;background:#fff;border-radius:10px;padding:30px;box-shadow:0 4px 12px rgba(0,0,0,.06)\">
<h2 style=\"color:#0F172A;font-family:Outfit,sans-serif\">Nuevo Lead — CONECTA S.A.</h2>
<div style=\"background:#F8FAFC;border-left:4px solid #2563eb;padding:16px;margin:20px 0;border-radius:0 6px 6px 0\">
<p><strong>Nombre:</strong> {$data['name']}</p><p><strong>Empresa:</strong> {$data['company']}</p>
<p><strong>Cargo:</strong> {$data['role']}</p><p><strong>Celular:</strong> {$data['phone']}</p>
<p><strong>Email:</strong> {$data['email']}</p><p><strong>Servicio:</strong> $svc</p>
<p><strong>Urgencia:</strong> $urg</p></div>
<p style=\"color:#64748B;font-size:13px\">$now — conecta.cl</p></div></body></html>";

$ch = curl_init('https://api.postmarkapp.com/email');
curl_setopt_array($ch, [
    CURLOPT_POST => true,
    CURLOPT_HTTPHEADER => [
        'Accept: application/json',
        'Content-Type: application/json',
        'X-Postmark-Server-Token: 8b3d04b1-ebbb-460e-9373-aec2ca8442c8'
    ],
    CURLOPT_POSTFIELDS => json_encode([
        'From' => 'victor.vilche@conecta.cl',
        'To' => 'victor.vilche@conecta.cl',
        'Subject' => "Lead: {$data['name']} — {$data['company']} | $svc",
        'HtmlBody' => $html,
        'MessageStream' => 'outbound'
    ]),
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_TIMEOUT => 15,
]);
curl_exec($ch);
$ok = curl_getinfo($ch, CURLINFO_HTTP_CODE) === 200;
curl_close($ch);

echo json_encode(['ok' => $ok, 'message' => $ok ? 'Recibido. Te contactaremos pronto.' : 'Error al enviar']);
