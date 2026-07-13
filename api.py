#!/usr/bin/env python3
"""Mini API para recibir formularios de conecta.cl -> email + WhatsApp"""
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import subprocess, json, os
from datetime import datetime

app = Flask(__name__, static_folder='assets', static_url_path='/assets')
CORS(app)
POSTMARK_SCRIPT = "/root/.hermes/scripts/postmark_send.py"
TO_EMAIL = "victor.vilche@conecta.cl"

SERVICE_LABELS = {"RTU":"RTU / Cambio de Remotas","PMU":"PMU / Telemedida","SCADA":"SCADA / EMS","DCS":"DCS / Control de Procesos","Instrumentacion":"Instrumentacion / Equipos","Ciberseguridad":"Ciberseguridad OT","Protecciones":"Protecciones / EDAC","BESS":"BESS / PMGD","Consultoria":"Consultoria / Auditoria","Otro":"Otro"}
URGENCY_LABELS = {"inmediata":"Inmediata","este_mes":"Este mes","este_trimestre":"Este trimestre","cotizacion":"Solo cotizacion"}

def build_msg(name, company, role, phone, email, service, urgency):
    svc = SERVICE_LABELS.get(service, service)
    urg = URGENCY_LABELS.get(urgency, urgency)
    return f"""+{name} | {company} | {role}
Tel: {phone} | {email}
Servicio: {svc}
Urgencia: {urg}
{datetime.now().strftime('%d/%m/%Y %H:%M')}"""

def send_all(name, company, role, phone, email, service, urgency):
    svc = SERVICE_LABELS.get(service, service)
    urg = URGENCY_LABELS.get(urgency, urgency)
    now = datetime.now().strftime('%d/%m/%Y %H:%M')

    # WhatsApp
    try:
        subprocess.run(["hermes","send-message","--target","whatsapp","--message",
            f"🔵 *Nuevo lead*\n*{name}* | {company}\n{role}\n📞 {phone}\n📧 {email}\n🛠 {svc}\n⏰ {urg}\n_{now}_"],
            capture_output=True, timeout=15, cwd="/root/.hermes")
    except: pass

    # Email
    body = f"""<html><body style="font-family:Inter,sans-serif;padding:20px;background:#F1F5F9">
<div style="max-width:520px;margin:0 auto;background:#fff;border-radius:10px;padding:30px;box-shadow:0 4px 12px rgba(0,0,0,0.06)">
<h2 style="color:#0F172A;font-family:Outfit,sans-serif">Nuevo Lead — CONECTA S.A.</h2>
<div style="background:#F8FAFC;border-left:4px solid #2563eb;padding:16px;margin:20px 0;border-radius:0 6px 6px 0">
<p><strong>Nombre:</strong> {name}</p><p><strong>Empresa:</strong> {company}</p>
<p><strong>Cargo:</strong> {role}</p><p><strong>Celular:</strong> {phone}</p>
<p><strong>Email:</strong> {email}</p><p><strong>Servicio:</strong> {svc}</p>
<p><strong>Urgencia:</strong> {urg}</p></div>
<p style="color:#64748B;font-size:13px">{now} — conecta.cl</p></div></body></html>"""
    try:
        subprocess.run(["python3",POSTMARK_SCRIPT,"--to",TO_EMAIL,"--subject",f"Lead: {name} — {company} | {svc}","--body",body,"--html"],
            capture_output=True, text=True, timeout=20)
    except: pass

@app.route("/form", methods=["POST"])
def form_handler():
    d = request.get_json(force=True, silent=True) or {}
    fields = ["name","company","role","phone","email","service","urgency"]
    vals = {f: d.get(f,"").strip() for f in fields}
    if not all(vals.values()):
        return jsonify({"ok":False,"error":"Faltan campos"}), 400
    send_all(**vals)
    return jsonify({"ok":True,"message":"Recibido. Te contactaremos pronto."})

@app.route("/health")
def health():
    return jsonify({"status":"ok"})

@app.route("/whatsapp-notify", methods=["POST"])
def whatsapp_notify():
    d = request.get_json(force=True, silent=True) or {}
    msg = d.get("message", "Nuevo lead desde conecta.cl/v2")
    try:
        subprocess.run(["hermes","send-message","--target","whatsapp","--message",msg],
                      capture_output=True, timeout=10, cwd="/root/.hermes")
        return jsonify({"ok":True})
    except:
        return jsonify({"ok":False}), 500

@app.route("/")
def index():
    return send_from_directory('.', 'index_light.html')

@app.route("/<path:path>")
def static_files(path):
    if os.path.isfile(path):
        return send_from_directory('.', path)
    return send_from_directory('.', 'index_light.html')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8091)
