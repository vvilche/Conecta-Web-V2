#!/usr/bin/env python3
"""
WhatsApp Auto-Responder Bot para CONECTA S.A.
Detecta el mensaje trigger "Más información de CONECTA S.A." y arranca
una conversación estructurada. Al finalizar, notifica a Víctor por Hermes.
"""

import requests, json, time, os, subprocess
from datetime import datetime

BRIDGE = "http://localhost:3000"
STATE_FILE = "/root/.hermes/conecta_bot_state.json"
TRIGGER = "más información de conecta"
VICTOR_CHAT = None  # Se obtiene del primer mensaje

SERVICE_MAP = {
    "1":"RTU / Cambio de Remotas","2":"PMU / Telemedida","3":"SCADA / EMS",
    "4":"DCS / Control de Procesos","5":"Instrumentación / Equipos",
    "6":"Ciberseguridad OT","7":"Protecciones / EDAC","8":"BESS / PMGD",
    "9":"Consultoría / Auditoría","10":"Otro"
}

URGENCY_MAP = {"a":"Inmediata","b":"Este mes","c":"Este trimestre","d":"Solo cotización"}

def load_state():
    if os.path.exists(STATE_FILE):
        return json.load(open(STATE_FILE))
    return {}

def save_state(s):
    json.dump(s, open(STATE_FILE, "w"), indent=2)

def send_msg(chat_id, text):
    try:
        r = requests.post(f"{BRIDGE}/send", json={"chatId": chat_id, "message": text}, timeout=10)
        return r.status_code == 200
    except Exception as e:
        print(f"send_msg error: {e}")
        return False

def notify_victor(name, company, email, service, urgency):
    msg = f"""✅ *Lead calificado — CONECTA Bot*

*Nombre:* {name}
*Empresa:* {company}
*Email:* {email}
*Servicio:* {service}
*Urgencia:* {urgency}
*Fecha:* {datetime.now().strftime('%d/%m/%Y %H:%M')}"""
    try:
        subprocess.run(["hermes","send-message","--target","whatsapp","--message",msg],
                      capture_output=True, timeout=15, cwd="/root/.hermes")
    except: pass

def process_messages():
    state = load_state()
    print(f"Bot iniciado. {len(state)} conversaciones activas.")
    
    while True:
        try:
            r = requests.get(f"{BRIDGE}/messages", timeout=30)
            if r.status_code != 200:
                time.sleep(2)
                continue
            
            data = r.json()
            if not data or "messages" not in data:
                time.sleep(1)
                continue
            
            for msg in data.get("messages", []):
                chat_id = msg.get("chatId", "")
                text = (msg.get("message", "") or "").strip().lower()
                
                if not chat_id or not text:
                    continue
                
                # --- NEW CONVERSATION ---
                if text.startswith(TRIGGER):
                    state[chat_id] = {"step": 1, "data": {}}
                    send_msg(chat_id, "¡Hola! 👋 Gracias por contactar a CONECTA S.A.\n\nPara ayudarte mejor, necesito algunos datos.\n\n*¿Cuál es tu nombre y empresa?*")
                    save_state(state)
                    continue
                
                if chat_id not in state:
                    continue
                
                s = state[chat_id]
                step = s["step"]
                d = s["data"]
                
                # --- STEP 1: Nombre + empresa ---
                if step == 1:
                    d["name_company"] = msg.get("message","").strip()
                    s["step"] = 2
                    save_state(state)
                    send_msg(chat_id, "Gracias! ¿Cuál es tu *email corporativo*?")
                
                # --- STEP 2: Email ---
                elif step == 2:
                    d["email"] = msg.get("message","").strip()
                    s["step"] = 3
                    save_state(state)
                    services = "\n".join([f"{k}. {v}" for k,v in SERVICE_MAP.items()])
                    send_msg(chat_id, f"¿Qué *servicio* te interesa? Responde con el número:\n\n{services}")
                
                # --- STEP 3: Servicio ---
                elif step == 3:
                    num = text.strip().rstrip('.')
                    svc = SERVICE_MAP.get(num, text)
                    d["service"] = svc
                    s["step"] = 4
                    save_state(state)
                    send_msg(chat_id, "¿Cuál es tu *urgencia*?\n\nA. Inmediata\nB. Este mes\nC. Este trimestre\nD. Solo cotización")
                
                # --- STEP 4: Urgencia → FINALIZAR ---
                elif step == 4:
                    urg = URGENCY_MAP.get(text.strip().lower()[:1], text)
                    d["urgency"] = urg
                    
                    # Parse name/company
                    nc = d.get("name_company","").split(",") if "," in d.get("name_company","") else d.get("name_company","").split("|")
                    name = nc[0].strip() if len(nc) > 0 else d.get("name_company","")
                    company = nc[1].strip() if len(nc) > 1 else ""
                    
                    send_msg(chat_id, f"✅ ¡Listo! Te contactaremos pronto.\n\nResumen:\n• {name}\n• {company}\n• {d['email']}\n• {d['service']}\n• {d['urgency']}")
                    
                    notify_victor(name, company, d["email"], d["service"], d["urgency"])
                    del state[chat_id]
                    save_state(state)
        
        except requests.exceptions.Timeout:
            pass  # Long-poll timeout, normal
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(3)

if __name__ == "__main__":
    process_messages()
