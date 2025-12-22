from flask import Flask, render_template, request, jsonify
import json
import os
import threading
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

DATA_FILE = 'clientes_local.json'

@app.before_request
def log_request():
    logger.info(f"📥 {request.method} {request.path} | {request.headers.get('Host', 'unknown')}")

@app.route('/')
def home():
    host = request.headers.get('Host', '').lower()
    if 'automadrivepro.com' in host:
        return render_template('admin.html')
    return render_template('index.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/ask', methods=['POST'])
def ask():
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'Mensaje no proporcionado'}), 400
            
        msg = data.get('message', '').lower().strip()
        logger.info(f"💬 {msg[:60]}")
        
        resp = None
        
        # HUMOS
        if "humo negro" in msg:
            resp = "⚫ HUMO NEGRO = Exceso combustible\n\n1. Filtro aire (15€)\n2. Inyectores (80-150€)\n3. Sensor MAF (10€)\n4. Sonda lambda (70-150€)"
        elif "humo blanco" in msg:
            resp = "⚪ HUMO BLANCO = Agua/refrigerante\n\nNORMAL: Vapor arranque frío\nGRAVE: Junta culata (600-1500€)\n🚨 Si persiste → PARA MOTOR"
        elif "humo azul" in msg:
            resp = "🔵 HUMO AZUL = Quema aceite\n\nRetenes: 400-900€\nTurbo: 700-2500€\nMotor: 2000€+"
        
        # PISTONES
        elif "piston" in msg:
            resp = "⚙️ PISTONES\n\nPieza que comprime la mezcla y transmite la explosión a la biela.\n\nPROBLEMAS:\n• Gripado → Sobrecalentamiento\n• Segmentos rotos → Pérdida compresión"
        
        # ACEITES
        elif "aceite" in msg:
            if any(x in msg for x in ["golf", "vw", "audi"]):
                resp = "🛢️ ACEITE VAG\n\nTSI/TDI: 5W-30 (VW 504.00/507.00)\nCantidad: 3.5-5.5L\nCada: 15.000 km\n\nMarcas:\n✓ Castrol Edge (~50€)\n✓ Mobil 1 ESP (~48€)"
            elif any(x in msg for x in ["moto", "yamaha", "honda"]):
                resp = "🏍️ ACEITE MOTOS\n\nDeportivas: 10W-40/50 JASO MA2\nCada: 5.000-6.000 km\n\nMotul 7100 (16€/L)\nCastrol Power1"
            else:
                resp = "🛢️ ACEITE\n\n¿Qué vehículo?\nEj: 'Aceite BMW 320d 2018'"
        
        # FRENOS
        elif "freno" in msg or "pastilla" in msg:
            resp = "🛑 FRENOS\n\nPastillas: 40.000-60.000 km\nDiscos: 80.000-120.000 km\nLíquido: Cada 2 años\n\nCOSTE: 80-450€"
        
        # SUSPENSIÓN
        elif "bieleta" in msg or "veleta" in msg:
            resp = "🔧 BIELETAS\n\nSÍNTOMAS:\n• Ruido en baches\n• Golpeteo curvas\n\nCOSTE: 70-160€"
        elif "amortiguador" in msg:
            resp = "🔧 AMORTIGUADORES\n\nVida: 80.000-120.000 km\n\nTEST: Presiona y suelta\n>2 rebotes = Gastado\n\nCOSTE: 150-400€"
        
        # MOTOR
        elif "temperatura" in msg or "sobrecalienta" in msg:
            resp = "🌡️ SOBRECALENTAMIENTO\n\n1. Refrigerante bajo\n2. Termostato (40-80€)\n3. Bomba agua (150-350€)\n4. Junta culata (600-1500€)\n\n🚨 ROJO → PARA"
        elif "bateria" in msg or "batería" in msg:
            resp = "🔋 BATERÍA\n\nVida: 4-6 años\n\n12.6V = OK\n<12V = Cambiar\n\nCOSTE: 70-150€"
        elif "bujia" in msg or "bujía" in msg:
            resp = "⚡ BUJÍAS\n\nNormales: 30.000-50.000 km\nIridio: 100.000 km\n\nCOSTE: 40-120€"
        elif "filtro" in msg:
            resp = "🔍 FILTROS\n\nAIRE: 20.000 km (15€)\nACEITE: Cada cambio (8€)\nHABITÁCULO: 15.000 km (12€)"
        
        # TRANSMISIÓN
        elif "embrague" in msg:
            resp = "⚙️ EMBRAGUE\n\nVida: 100.000-200.000 km\n\nSÍNTOMAS:\n• Patina\n• Olor quemado\n\nCOSTE: 400-1200€"
        elif "neumatico" in msg or "neumático" in msg:
            resp = "🛞 NEUMÁTICOS\n\nVida: 40.000-60.000 km\n\n>3mm = OK\n<1.6mm = MULTA 200€\n\nCOSTE: 60-150€/ud"
        elif "cadena moto" in msg:
            resp = "⛓️ CADENA MOTO\n\nLimpiar: Cada 500 km\nEngrasar: Cada 500 km\nCambiar: 15.000-25.000 km\n\nCOSTE: 100-250€"
        
        # BÚSQUEDA WEB
        else:
            logger.info("🌐 Búsqueda web...")
            try:
                import requests
                url = "https://api.duckduckgo.com/"
                params = {'q': f"mecánica {msg}", 'format': 'json', 'no_html': 1}
                res = requests.get(url, params=params, timeout=5)
                web = res.json()
                
                abstract = web.get('AbstractText', '')
                if abstract:
                    resp = f"🌐 {abstract}\n\n💡 Fuente: Web"
                else:
                    resp = f"🤖 '{msg[:60]}...'\n\nSoy experto en:\n• Diagnóstico humos\n• Aceites (coches/motos)\n• Frenos, suspensión\n• Mantenimiento\n\n¿Más detalles?"
            except:
                resp = f"🤖 '{msg[:60]}...'\n\nSoy experto en mecánica.\n\n¿Puedes ser más específico?"
        
        return jsonify({'response': resp})
        
    except Exception as e:
        logger.error(f"❌ {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/guardar_cliente', methods=['POST'])
def guardar_cliente():
    try:
        cliente = request.get_json()
        if not cliente or 'matricula' not in cliente:
            return jsonify({'status': 'error'}), 400
        
        cliente['fecha'] = datetime.now().isoformat()
        cliente['matricula'] = cliente['matricula'].upper().strip()
        
        data = []
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except:
                data = []
        
        data = [c for c in data if c.get('matricula') != cliente['matricula']]
        data.append(cliente)
        
        if len(data) > 100:
            data = sorted(data, key=lambda x: x.get('fecha', ''), reverse=True)[:100]
        
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        return jsonify({'status': 'success', 'matricula': cliente['matricula']})
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()}), 200

@app.route('/ping')
def ping():
    return jsonify({'pong': True}), 200

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Ruta no encontrada'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Error interno'}), 500

if __name__ == '__main__':
    logger.info("=" * 70)
    logger.info("🚀 AutoMaDrive Pro - Iniciando...")
    logger.info("📍 Puerto: 5000")
    logger.info("🌍 Routing:")
    logger.info("   automadrivepro.com → admin.html")
    logger.info("   automadrivepro.es → index.html (IA)")
    logger.info("=" * 70)
    
    app.run(host='0.0.0.0', port=5000, threaded=True, debug=False)
