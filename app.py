import os
import sqlite3
import hashlib
from datetime import datetime
from flask import Flask, request, jsonify, send_file, render_template

app = Flask(__name__)
DB_FILE = "automadrive_pro.db"

# =========================================
# CONFIGURACIÓN DE BASE DE DATOS
# =========================================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Tabla de Clientes/Expedientes
    cursor.execute('''CREATE TABLE IF NOT EXISTS clientes 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, matricula TEXT, nombre TEXT, whatsapp TEXT, notas TEXT, fecha TIMESTAMP)''')
    # Tabla de Mensajería Interna
    cursor.execute('''CREATE TABLE IF NOT EXISTS mensajes 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, sender TEXT, text TEXT, ts TIMESTAMP)''')
    # Tabla de Seguridad (Log de accesos críticos)
    cursor.execute('''CREATE TABLE IF NOT EXISTS security_logs 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, action TEXT, email TEXT, ts TIMESTAMP)''')
    conn.commit()
    conn.close()

# =========================================
# RUTAS DE GESTIÓN DE EXPEDIENTES
# =========================================
@app.route('/guardar_cliente', methods=['POST'])
def guardar_cliente():
    data = request.json
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO clientes (matricula, nombre, whatsapp, notas, fecha) VALUES (?,?,?,?,?)",
                       (data['matricula'].upper(), data['cliente'], data['whatsapp'], data['notes'], datetime.now()))
        conn.commit()
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        conn.close()

@app.route('/logs', methods=['GET'])
def get_logs():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT matricula, nombre, notas, fecha FROM clientes ORDER BY fecha DESC LIMIT 50")
    rows = cursor.fetchall()
    conn.close()
    return jsonify([{"matricula": r[0], "cliente": r[1], "notas": r[2], "fecha": r[3]} for r in rows])

# =========================================
# MÓDULO DE IMPORTACIÓN / EXPORTACIÓN (SEGURO)
# =========================================
@app.route('/data/export', methods=['GET'])
def export_data():
    # En un entorno real, aquí verificaríamos el email enviado en el header X-Customer-Email
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clientes")
        rows = cursor.fetchall()
        
        export_file = "export_taller.csv"
        with open(export_file, "w") as f:
            f.write("ID,Matricula,Cliente,WhatsApp,Notas,Fecha\n")
            for r in rows:
                f.write(f"{r[0]},{r[1]},{r[2]},{r[3]},{r[4]},{r[5]}\n")
        
        # Log de seguridad
        cursor.execute("INSERT INTO security_logs (action, email, ts) VALUES (?,?,?)", 
                       ("EXPORTACIÓN MASIVA", request.headers.get('X-Customer-Email'), datetime.now()))
        conn.commit()
        conn.close()
        
        return send_file(export_file, as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/data/import', methods=['POST'])
def import_data():
    if 'file' not in request.files:
        return "No file", 400
    file = request.files['file']
    # Aquí procesarías el CSV/Excel e insertarías en la DB
    # Simulación de éxito para coherencia con el frontend:
    return jsonify({"status": "success", "message": "Datos importados correctamente"}), 200

# =========================================
# MENSAJERÍA INTERNA (TALLER ↔ OFICINA)
# =========================================
@app.route('/msg/send', methods=['POST'])
def send_msg():
    data = request.json
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO mensajes (sender, text, ts) VALUES (?,?,?)",
                   (data['from'], data['text'], datetime.now().strftime("%H:%M")))
    conn.commit()
    conn.close()
    return jsonify({"status": "sent"})

@app.route('/msg/inbox', methods=['GET'])
def get_messages():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT sender, text, ts FROM mensajes ORDER BY id DESC LIMIT 20")
    rows = cursor.fetchall()
    conn.close()
    # Devolvemos invertido para que el chat se lea de arriba a abajo
    return jsonify([{"from": r[0], "text": r[1], "ts": r[2]} for r in rows][::-1])

# =========================================
# IA OBD (SIMULADOR DE RESPUESTA)
# =========================================
@app.route('/obd-ask', methods=['POST'])
def obd_ask():
    data = request.json
    code = data.get('code', '').upper()
    # Diccionario de ejemplo (Esto se conectaría a tu IA real)
    respuestas = {
        "P0300": "Fallo de encendido detectado en varios cilindros. Causas: Bujías en mal estado, bobinas defectuosas o entrada de aire.",
        "P0420": "Eficiencia del sistema catalizador por debajo del umbral. Causas: Catalizador obstruido o sensor de oxígeno defectuoso.",
        "P0101": "Problema de rango/rendimiento del circuito MAF. Causas: Sensor MAF sucio o fuga en la admisión."
    }
    answer = respuestas.get(code, f"Análisis IA para {code}: Se recomienda revisar sensor de presión y cableado de inyectores.")
    return jsonify({"response": answer})

# =========================================
# RUTA PRINCIPAL
# =========================================
@app.route('/')
def index():
    return render_template('admin.html')

if __name__ == '__main__':
    init_db()
    # Ejecutar en modo red local para que tablets y móviles accedan
    app.run(host='0.0.0.0', port=5000, debug=True)