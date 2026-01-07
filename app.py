from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import json
import logging
from datetime import datetime
import openai
from pathlib import Path

# =========================
# LOGGING
# =========================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =========================
# APP
# =========================
app = Flask(__name__)
CORS(app)

# =========================
# DIRECTORIOS / ARCHIVOS
# =========================
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

RECORDINGS_DIR = DATA_DIR / "recordings"
RECORDINGS_DIR.mkdir(exist_ok=True)

OCR_DIR = DATA_DIR / "ocr"
OCR_DIR.mkdir(exist_ok=True)

CONFIG_FILE = DATA_DIR / "config.json"
FICHAS_FILE = DATA_DIR / "fichas.json"
ACTIVIDAD_FILE = DATA_DIR / "actividad.json"


# =========================
# UTILIDADES JSON
# =========================
def cargar_json(archivo: Path, default):
    if archivo.exists():
        try:
            with open(archivo, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Error leyendo {archivo.name}: {e}")
            return default
    return default


def guardar_json(archivo: Path, datos):
    try:
        with open(archivo, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error guardando {archivo.name}: {e}")


def registrar_actividad(tipo: str, descripcion: str):
    actividades = cargar_json(ACTIVIDAD_FILE, [])
    actividades.insert(0, {
        "tipo": tipo,
        "descripcion": descripcion,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    guardar_json(ACTIVIDAD_FILE, actividades[:100])


def normalizar_matricula(s: str) -> str:
    return (s or "").strip().upper()


def normalizar_whatsapp(s: str) -> str:
    # dejamos como string tal cual, pero sin espacios raros
    return (s or "").strip().replace(" ", "")


# =========================
# SERVICIO IA (SYNC y estable)
# =========================
class ServicioIA:
    def __init__(self):
        self.openai_client = None
        self._last_key = None

    def inicializar(self, api_key: str | None):
        if not api_key:
            return
        api_key = api_key.strip()
        if not api_key:
            return

        # evita reinicializar si es la misma key
        if self.openai_client and self._last_key == api_key:
            return

        try:
            self.openai_client = openai.OpenAI(api_key=api_key)
            self._last_key = api_key
            logger.info("OpenAI inicializado correctamente.")
        except Exception as e:
            self.openai_client = None
            logger.error(f"Error inicializando OpenAI: {e}")

    def consultar(self, pregunta: str) -> str:
        config = cargar_json(CONFIG_FILE, {})
        api_key = (config.get("openai_key") or "").strip()

        if api_key:
            self.inicializar(api_key)

        if self.openai_client:
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "Eres un experto mecánico de taller. "
                                "Responde en español, breve, claro, por puntos, y directo. "
                                "Si hay códigos OBD/DTC, explica significado, gravedad, causas y pruebas."
                            )
                        },
                        {"role": "user", "content": pregunta}
                    ],
                    max_tokens=450
                )
                txt = response.choices[0].message.content or ""
                return txt.strip() if txt else "Sin respuesta."
            except Exception as e:
                return f"Error IA: {str(e)}"

        # fallback local
        return (
            "Respuesta local (sin OpenAI configurado):\n"
            "- Revisa códigos OBD2 y síntomas.\n"
            "- Comprueba fusibles, sensores, entradas de aire, fugas y valores en vivo.\n"
            "- Si me das códigos DTC (P0xxx) te guío paso a paso."
        )


servicio_ia = ServicioIA()


# =========================
# RUTAS HTML
# =========================
@app.route("/")
def landing():
    # index.html (asistente público)
    return render_template("index.html")


@app.route("/panel")
def panel():
    # admin.html (dashboard técnico)
    return render_template("admin.html", id_dispositivo="RASP-PRO-01")


# =========================
# API: ACTIVIDAD
# =========================
@app.route("/api/actividad")
def api_actividad():
    return jsonify(cargar_json(ACTIVIDAD_FILE, []))


# =========================
# API: CONSULTA IA
# Compatible con index.html y admin.html
# =========================
@app.route("/api/consulta-ia", methods=["POST"])
def consulta_ia():
    data = request.get_json(silent=True) or {}
    pregunta = (data.get("pregunta") or "").strip()

    if not pregunta:
        return jsonify({"error": "Pregunta vacía"}), 400

    respuesta = servicio_ia.consultar(pregunta)

    registrar_actividad("IA", f"Consulta: {pregunta[:80]}")
    return jsonify({"respuesta": respuesta})


# =========================
# API: GUARDAR CLIENTE (UPSERT POR MATRÍCULA)
# Compatible con admin.html (nuevaFicha)
# =========================
@app.route("/guardar_cliente", methods=["POST"])
def guardar_cliente():
    data = request.get_json(silent=True) or {}
    fichas = cargar_json(FICHAS_FILE, [])

    matricula = normalizar_matricula(data.get("matricula", ""))
    if not matricula:
        return jsonify({"status": "fail", "error": "Falta matrícula"}), 400

    cliente = (data.get("cliente") or "").strip()
    whatsapp = normalizar_whatsapp(data.get("whatsapp", ""))
    notas = (data.get("notas") or "").strip()
    estado = (data.get("estado") or "En curso").strip()

    # Buscar si ya existe por matrícula
    existente = next((f for f in fichas if normalizar_matricula(f.get("matricula")) == matricula), None)

    if existente:
        # actualizar
        existente["cliente"] = cliente
        existente["whatsapp"] = whatsapp
        existente["notas"] = notas
        existente["estado"] = estado
        existente["fecha"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        registrar_actividad("CLIENTE", f"Actualizado: {matricula} ({cliente})")
    else:
        # crear nuevo con id incremental
        max_id = max([int(f.get("id", 0)) for f in fichas], default=0)
        ficha = {
            "id": max_id + 1,
            "matricula": matricula,
            "cliente": cliente,
            "whatsapp": whatsapp,
            "notas": notas,
            "estado": estado,
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        fichas.append(ficha)
        registrar_actividad("CLIENTE", f"Nuevo ingreso: {matricula} ({cliente})")

    guardar_json(FICHAS_FILE, fichas)
    return jsonify({"status": "ok"})


# =========================
# API: BUSCAR EXPEDIENTE
# ✅ Ahora devuelve whatsapp/telefono/notas/estado y sugerencias
# Compatible con admin.html (buscarDesdeWidget + autollenado presupuesto)
# =========================
def generar_sugerencias_por_notas(notas: str):
    n = (notas or "").lower()
    sug = []

    # heurística simple: si aparece la palabra en notas, sugiere líneas típicas
    if "aceite" in n:
        sug.append({"title": "Cambio de aceite + filtro", "qty": 1, "hours": 0.8, "parts": 55})
    if "pastillas" in n or "freno" in n:
        sug.append({"title": "Revisión sistema de frenos", "qty": 1, "hours": 0.6, "parts": 0})
    if "bateria" in n or "batería" in n:
        sug.append({"title": "Comprobación / sustitución batería", "qty": 1, "hours": 0.4, "parts": 95})
    if "neumatic" in n or "neumát" in n or "rueda" in n:
        sug.append({"title": "Revisión neumáticos + presión", "qty": 1, "hours": 0.4, "parts": 0})
    if "obd" in n or "diagnos" in n or "testigo" in n:
        sug.append({"title": "Diagnóstico OBD (lectura + informe)", "qty": 1, "hours": 0.4, "parts": 0})

    return sug[:10]


@app.route("/api/buscar")
def buscar():
    q = normalizar_matricula(request.args.get("q", ""))
    if not q:
        return jsonify({"encontrado": False, "error": "Falta parámetro q"}), 400

    fichas = cargar_json(FICHAS_FILE, [])
    ficha = next((f for f in fichas if normalizar_matricula(f.get("matricula")) == q), None)

    if ficha:
        cliente = ficha.get("cliente", "") or ""
        whatsapp = ficha.get("whatsapp", "") or ""
        notas = ficha.get("notas", "") or ""
        estado = ficha.get("estado", "En curso") or "En curso"

        registrar_actividad("BUSCAR", f"Encontrado: {q} ({cliente})")

        return jsonify({
            "encontrado": True,
            "matricula": q,
            "cliente": cliente,
            "whatsapp": whatsapp,
            "telefono": whatsapp,   # compatibilidad extra
            "notas": notas,
            "estado": estado,
            "sugerencias": generar_sugerencias_por_notas(notas)
        })

    registrar_actividad("BUSCAR", f"No encontrado: {q}")
    return jsonify({"encontrado": False})


# =========================
# API: AUDIO (CAJA NEGRA)
# Compatible con admin.html (/api/upload-recording)
# =========================
@app.route("/api/upload-recording", methods=["POST"])
def upload_recording():
    if "audio" not in request.files:
        return jsonify({"error": "No audio"}), 400

    file = request.files["audio"]
    filename = f"REC_{datetime.now().strftime('%Y%m%d_%H%M%S')}.webm"
    file.save(RECORDINGS_DIR / filename)

    registrar_actividad("SEGURIDAD", f"Audio grabado: {filename}")
    return jsonify({"status": "ok", "file": filename})


# =========================
# API: OCR / IMAGEN (LANDING)
# Compatible con index.html (/api/upload-ocr)
# =========================
@app.route("/api/upload-ocr", methods=["POST"])
def upload_ocr():
    if "image" not in request.files:
        return jsonify({"error": "No image"}), 400

    file = request.files["image"]
    filename = f"OCR_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    file.save(OCR_DIR / filename)

    registrar_actividad("OCR", f"Imagen subida: {filename}")
    return jsonify({"result": "Imagen registrada en el historial.", "file": filename})


# =========================
# API: PEDIDO RÁPIDO
# (si luego conectas al botón real)
# =========================
@app.route("/api/pedido-rapido")
def pedido_rapido():
    registrar_actividad("PEDIDO", "Solicitud Castrol Pro")
    return jsonify({"url": "https://www.castrol.com"})


# =========================
# MAIN
# =========================
if __name__ == "__main__":
    cfg = cargar_json(CONFIG_FILE, {})
    if (cfg.get("openai_key") or "").strip():
        servicio_ia.inicializar(cfg["openai_key"])

    app.run(host="0.0.0.0", port=5000, debug=True)
