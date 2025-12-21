from flask import Flask, render_template, request, jsonify
import json
import os
import threading  # <--- SECRETO DE LA VELOCIDAD
from datetime import datetime
from supabase import create_client, Client

app = Flask(__name__)

# --- CONFIGURACIÓN ---
SUPABASE_URL = "https://tu-proyecto.supabase.co"
SUPABASE_KEY = "tu-clave-anon"
ID_TALLER_PRO = "68b4f064-657d-47a0-b95f-732356ffc5c1"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

DATA_FILE = 'clientes_local.json'

# FUNCIÓN ASÍNCRONA: Guarda en la nube sin hacerte esperar
def guardar_en_nube_async(cliente):
    try:
        supabase.table("clientes").insert(cliente).execute()
        print(f"☁️ Nube actualizada: {cliente['matricula']}")
    except Exception as e:
        print(f"⚠️ Error Nube (pero guardado en local): {e}")

@app.route('/')
def home(): return render_template('index.html')

@app.route('/admin')
def admin(): return render_template('admin.html')

@app.route('/ask', methods=['POST'])
def ask():
    data = request.get_json()
    msg = data.get('message', '').lower()
    
    # RESPUESTA INMEDIATA (IA Local)
    if any(w in msg for w in ["veleta", "beleta", "bieleta"]):
        res = "Análisis: Son las bieletas de suspensión. Unen la estabilizadora y el amortiguador para evitar vibraciones."
    elif "aceite" in msg:
        res = "Para un Golf 2016, usa aceite 5W30 sintético (especificación VW 504 00/507 00)."
    else:
        res = "Consulta técnica recibida. Buscando en el manual de AutomaDrive Pro..."
    
    return jsonify({'response': res})

@app.route('/guardar_cliente', methods=['POST'])
def guardar_cliente():
    cliente = request.get_json()
    cliente['taller_id'] = ID_TALLER_PRO
    cliente['fecha'] = datetime.now().isoformat()
    cliente['matricula'] = cliente['matricula'].upper().strip()

    # 1. LANZAR GUARDADO A LA NUBE (En paralelo, no esperas)
    threading.Thread(target=guardar_en_nube_async, args=(cliente,)).start()

    # 2. GUARDADO LOCAL (Rápido)
    data = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f: data = json.load(f)
    
    data = [c for c in data if c['matricula'] != cliente['matricula']]
    data.append(cliente)
    
    # Limpieza local (máximo 10 registros para velocidad)
    if len(data) > 10:
        data = sorted(data, key=lambda x: x['fecha'], reverse=True)[:10]
        
    with open(DATA_FILE, 'w') as f: json.dump(data, f, indent=4)
    
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    # threaded=True permite atender a varios a la vez
    app.run(host='0.0.0.0', port=80, threaded=True)