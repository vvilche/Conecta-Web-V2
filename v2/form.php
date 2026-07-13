<?php
/**
 * Formulario CONECTA — autosuficiente
 * Envía email via Postmark API + intenta notificar WhatsApp via Hermes
 * Sin dependencia del VPS
 */
header('Content-Type: application/json');

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['ok' => false, 'error' => 'Solo POST']);
    exit;
}

$json = file_get_contents('php://input');
$data = json_decode($json, true);

$required = ['name', 'company', 'role', 'phone', 'email', 'service', 'urgency'];
foreach ($required as $field) {
    if (empty($data[$field])) {
        http_response_code(400);
        echo json_encode(['ok' => false, 'error' => "Falta campo: $field"]);
        exit;
    }
}

// Mapeo de nombres de servicio/urgencia
$services = [
    'RTU' => 'RTU / Cambio de Remotas', 'PMU' => 'PMU / Telemedida',
    'SCADA' => 'SCADA / EMS', 'DCS' => 'DCS / Control de Procesos',
    'Instrumentacion' => 'Instrumentación / Equipos', 'Ciberseguridad' => 'Ciberseguridad OT',
    'Protecciones' => 'Protecciones / EDAC', 'BESS' => 'BESS / PMGD',
    'Consultoria' => 'Consultoría / Auditoría', 'Otro' => 'Otro'
];
$urgencies = [
    'inmediata' => 'Inmediata', 'este_mes' => 'Este mes',
    'este_trimestre' => 'Este trimestre', 'cotizacion' => 'Solo cotización'
];

$svc = isset($services[$data['service']]) ? $services[$data['service']] : $data['service'];
$urg = isset($urgencies[$data['urgency']]) ? $urgencies[$data['urgency']] : $data['urgency'];
$now = date('d/m/Y H:i');

// === 1. ENVIAR EMAIL VIA POSTMARK (siempre funciona, no depende del VPS) ===
$postmark_token = '8b3d04b1-ebbb-460e-9373-aec2ca8442c8';
$email_html = "<html><body style=\"font-family:Inter,sans-serif;padding:20px;background:#F1F5F9\">
<div style=\"max-width:520px;margin:0 auto;background:#fff;border-radius:10px;padding:30px;box-shadow:0 4px 12px rgba(0,0,0,0.06)\">
<h2 style=\"color:#0F172A;font-family:Outfit,sans-serif\">🔵 Nuevo Lead — CONECTA S.A.</h2>
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
        'X-Postmark-Server-Token: ' . $postmark_token
    ],
    CURLOPT_POSTFIELDS => json_encode([
        'From' => 'victor.vilche@conecta.cl',
        'To' => 'victor.vilche@conecta.cl',
        'Subject' => "Lead: {$data['name']} — {$data['company']} | $svc",
        'HtmlBody' => $email_html,
        'MessageStream' => 'outbound'
    ]),
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_TIMEOUT => 15,
]);
$email_result = curl_exec($ch);
$email_ok = curl_getinfo($ch, CURLINFO_HTTP_CODE) === 200;
curl_close($ch);

// === 2. INTENTAR WHATSAPP VIA HERMES (best-effort, no bloquea) ===
$wa_msg = "🔵 *Nuevo lead*\n*{$data['name']}* | {$data['company']}\n{$data['role']}\n📞 {$data['phone']}\n📧 {$data['email']}\n🛠 $svc\n⏰ $urg\n_$now_";
$wa_ch = curl_init('http://76.13.239.113:8091/whatsapp-notify');
curl_setopt_array($wa_ch, [
    CURLOPT_POST => true,
    CURLOPT_POSTFIELDS => json_encode(['message' => $wa_msg]),
    CURLOPT_HTTPHEADER => ['Content-Type: application/json'],
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_TIMEOUT => 5,  // timeout corto, no bloquea
]);
curl_exec($wa_ch);
curl_close($wa_ch);

echo json_encode(['ok' => true, 'message' => 'Recibido. Te contactaremos pronto.']);
