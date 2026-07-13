#!/usr/bin/env python3
"""Mini API para recibir formularios de conecta.cl → email + WhatsApp"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess, json, os
from datetime import datetime

app = Flask(__name__)
CORS(app)

POSTMARK_SCRIPT = "/root/.hermes/scripts/postmark_send.py"
TO_EMAIL = "victor.vilche@conecta.cl"

SERVICE_LABELS = {
    "RTU": "RTU / Cambio de Remotas",
    "PMU": "PMU / Telemedida",
    "SCADA": "SCADA / EMS",
    "DCS": "DCS / Control de Procesos",
    "Instrumentacion": "Instrumentación / Equipos",
    "Ciberseguridad": "Ciberseguridad OT",
    "Protecciones": "Protecciones / EDAC",
    "BESS": "BESS / PMGD",
    "Consultoria": "Consultoría / Auditoría",
    "Otro": "Otro"
}

def send_whatsapp(name, phone, email, service):
    svc = SERVICE_LABELS.get(service, service)
    msg = f"🔵 *Nuevo lead conecta.cl*\n\n*Nombre:* {name}\n*Celular:* {phone}\n*Email:* {email}\n*Servicio:* {svc}\n*Fecha:* {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    try:
        subprocess.run(
            ["hermes", "send-message", "--target", "whatsapp", "--message", msg],
            capture_output=True, timeout=15,
            cwd="/root/.hermes"
        )
    except Exception as e:
        print(f"WhatsApp falló: {e}")

def send_email(name, phone, email, service):
    svc = SERVICE_LABELS.get(service, service)
    body = f"""<html><body style="font-family:Inter,sans-serif;padding:20px;background:#F1F5F9">
<div style="max-width:520px;margin:0 auto;background:#fff;border-radius:10px;padding:30px;box-shadow:0 4px 12px rgba(0,0,0,0.06)">
<h2 style="color:#0F172A;font-family:Outfit,sans-serif">Nuevo Lead — CONECTA S.A.</h2>
<div style="background:#F8FAFC;border-left:4px solid #2563eb;padding:16px;margin:20px 0;border-radius:0 6px 6px 0">
<p style="margin:6px 0"><strong>Nombre:</strong> {name}</p>
<p style="margin:6px 0"><strong>Celular:</strong> {phone}</p>
<p style="margin:6px 0"><strong>Email:</strong> {email}</p>
<p style="margin:6px 0"><strong>Servicio:</strong> {svc}</p>
</div>
<p style="color:#64748B;font-size:13px">Recibido desde conecta.cl — {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
</div></body></html>"""
    
    try:
        result = subprocess.run(
            ["python3", POSTMARK_SCRIPT,
             "--to", TO_EMAIL,
             "--subject", f"Nuevo lead: {name} — {svc}",
             "--body", body,
             "--html"],
            capture_output=True, text=True, timeout=20
        )
        print("Postmark:", result.stdout.strip())
        return result.returncode == 0
    except Exception as e:
        print(f"Postmark falló: {e}")
        return False

@app.route("/form", methods=["POST"])
def form_handler():
    data = request.get_json(force=True, silent=True) or {}
    name = data.get("name", "").strip()
    phone = data.get("phone", "").strip()
    email = data.get("email", "").strip()
    service = data.get("service", "").strip()
    
    if not name or not phone or not email or not service:
        return jsonify({"ok": False, "error": "Faltan campos"}), 400
    
    email_ok = send_email(name, phone, email, service)
    send_whatsapp(name, phone, email, service)
    
    return jsonify({
        "ok": True,
        "email_sent": email_ok,
        "message": "Recibido. Te contactaremos pronto."
    })

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8091)
