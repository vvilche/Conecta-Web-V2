#!/usr/bin/env python3
"""WhatsApp Auto-Responder Bot para CONECTA S.A."""
import requests, json, time, os, subprocess
from datetime import datetime

BRIDGE = "http://localhost:3000"
STATE_FILE = "/root/.hermes/conecta_bot_state.json"
TRIGGER = "mas informacion de conecta"

SERVICE_MAP = {"1":"RTU / Cambio de Remotas","2":"PMU / Telemedida","3":"SCADA / EMS","4":"DCS / Control de Procesos","5":"Instrumentacion / Equipos","6":"Ciberseguridad OT","7":"Protecciones / EDAC","8":"BESS / PMGD","9":"Consultoria / Auditoria","10":"Otro"}
URGENCY_MAP = {"a":"Inmediata","b":"Este mes","c":"Este trimestre","d":"Solo cotizacion"}

def load_state():
    if os.path.exists(STATE_FILE): return json.load(open(STATE_FILE))
    return {}

def save_state(s): json.dump(s, open(STATE_FILE,"w"), indent=2)

def send_msg(chat_id, text):
    try:
        r = requests.post(BRIDGE + "/send", json={"chatId": chat_id, "message": text}, timeout=10)
        print("SEND %s -> %s %s" % (chat_id[:20], r.status_code, r.text[:80]))
        return r.status_code == 200
    except Exception as e:
        print("SEND error:", e)
        return False

def notify_victor(name, company, email, service, urgency):
    msg = "\n".join([
        "Lead calificado - CONECTA Bot",
        "Nombre: " + name,
        "Empresa: " + company,
        "Email: " + email,
        "Servicio: " + service,
        "Urgencia: " + urgency,
        "Fecha: " + datetime.now().strftime("%d/%m/%Y %H:%M")
    ])
    try:
        subprocess.run(["hermes","send-message","--target","whatsapp","--message",msg],
                      capture_output=True, timeout=15, cwd="/root/.hermes")
    except: pass

def process_messages():
    state = load_state()
    print("Bot iniciado. %d conversaciones activas. Escuchando..." % len(state))
    
    while True:
        try:
            r = requests.get(BRIDGE + "/messages", timeout=30)
            msgs = r.json() if r.status_code == 200 else []
            if not isinstance(msgs, list): msgs = []
            
            for msg in msgs:
                chat_id = msg.get("chatId", "")
                text = (msg.get("message", msg.get("body", "")) or "").strip()
                print("MSG [%s]: %s" % (chat_id[:25], text[:80]))
                
                if not chat_id or not text: continue
                
                text_lower = text.lower().replace("á","a").replace("ó","o").replace("é","e")
                
                # NEW CONVERSATION
                if TRIGGER in text_lower:
                    state[chat_id] = {"step": 1, "data": {}}
                    save_state(state)
                    send_msg(chat_id, "Hola! Gracias por contactar a CONECTA S.A.\n\nPara ayudarte mejor, necesito algunos datos.\n\nCual es tu nombre y empresa?")
                    continue
                
                if chat_id not in state: continue
                
                s = state[chat_id]; step = s["step"]; d = s["data"]
                user_msg = msg.get("message","").strip()
                
                if step == 1:
                    d["name_company"] = user_msg
                    s["step"] = 2; save_state(state)
                    send_msg(chat_id, "Gracias! Cual es tu email corporativo?")
                
                elif step == 2:
                    d["email"] = user_msg
                    s["step"] = 3; save_state(state)
                    svcs = "\n".join([k + ". " + v for k,v in SERVICE_MAP.items()])
                    send_msg(chat_id, "Que servicio te interesa? Responde con el numero:\n\n" + svcs)
                
                elif step == 3:
                    num = text.strip().rstrip('.')
                    d["service"] = SERVICE_MAP.get(num, text)
                    s["step"] = 4; save_state(state)
                    send_msg(chat_id, "Cual es tu urgencia?\n\nA. Inmediata\nB. Este mes\nC. Este trimestre\nD. Solo cotizacion")
                
                elif step == 4:
                    urg = URGENCY_MAP.get(text.strip().lower()[:1], text)
                    d["urgency"] = urg
                    nc = d.get("name_company","").replace("|",",").split(",")
                    name = nc[0].strip() if nc else d.get("name_company","")
                    company = nc[1].strip() if len(nc) > 1 else ""
                    
                    send_msg(chat_id, "Listo! Te contactaremos pronto.\n\nResumen:\n- %s\n- %s\n- %s\n- %s\n- %s" % (name, company, d["email"], d["service"], d["urgency"]))
                    notify_victor(name, company, d["email"], d["service"], d["urgency"])
                    del state[chat_id]; save_state(state)
        
        except requests.exceptions.Timeout: pass
        except Exception as e:
            print("Error:", e)
            time.sleep(3)
        time.sleep(2)  # Evitar CPU burn, la API no hace long-poll real

if __name__ == "__main__":
    process_messages()
