import os
import datetime
import re
import pytesseract
import asyncio
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel
from supabase import create_client, Client
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# --- CARGAR VARIABLES DE ENTORNO ---
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

# Conexión profesional a Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI(title="AutomaDrive Pro SaaS")

# Middleware para permitir conexiones desde cualquier sitio
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MODELOS DE DATOS ---
class ClienteData(BaseModel):
    matricula: str
    modelo: str
    propietario: str
    km: str
    notas: str
    proxima_itv: str = ""
    telefono: str = ""

class AvisoData(BaseModel):
    telefono: str
    matricula: str
    propietario: str = ""
    fecha_itv: str = ""

# --- MOTOR DE IA DE DIAGNÓSTICO ---
def motor_ia_diagnostico(c):
    sugerencias = []
    hoy = datetime.datetime.now()
    
    # Análisis de ITV
    if c.get('proxima_itv'):
        try:
            f_itv = datetime.datetime.strptime(c['proxima_itv'], "%Y-%m-%d")
            dias = (f_itv - hoy).days
            if 0 <= dias <= 15:
                sugerencias.append(f"🚨 *ITV PRÓXIMA:* Vence en {dias} días.")
            elif dias < 0:
                sugerencias.append(f"⛔ *ITV CADUCADA:* Venció hace {abs(dias)} días.")
        except: pass

    # Análisis de Kilometraje (Correa de distribución)
    try:
        km_num = int(re.sub(r'\D', '', str(c.get('km', '0'))))
        if km_num > 150000 and "distribucion" not in c.get('notas', '').lower():
            sugerencias.append("⚠️ *IA AVISO:* Sugerir revisión de Correa de Distribución.")
    except: pass

    return "\n".join(sugerencias) if sugerencias else "✅ *IA:* Vehículo al día."

# --- RUTAS DE LA API (SUPABASE CLOUD) ---

@app.get("/logs")
async def obtener_logs():
    try:
        # Consulta a la tabla 'entradas' en Supabase
        res = supabase.table("entradas").select("fecha, matricula").order("id", desc=True).limit(15).execute()
        # Formateamos para que el admin.html lo entienda (fecha, matricula, propietario, modelo)
        logs_formateados = []
        for item in res.data:
            # Buscamos datos del cliente para enriquecer el log
            cli = supabase.table("clientes").select("propietario, modelo").eq("matricula", item['matricula']).execute()
            prop = cli.data[0]['propietario'] if cli.data else "Nuevo"
            mod = cli.data[0]['modelo'] if cli.data else "Registrar"
            logs_formateados.append([item['fecha'], item['matricula'], prop, mod])
        return {"logs": logs_formateados}
    except Exception as e:
        print(f"Error en logs: {e}")
        return {"logs": []}

@app.get("/datos_cliente/{matricula}")
async def datos(matricula: str):
    res = supabase.table("clientes").select("*").eq("matricula", matricula.upper()).execute()
    if res.data:
        return {"encontrado": True, **res.data[0]}
    return {"encontrado": False}

@app.post("/guardar_cliente")
async def guardar(data: ClienteData):
    supabase.table("clientes").upsert({
        "matricula": data.matricula.upper(),
        "modelo": data.modelo,
        "propietario": data.propietario,
        "km": data.km,
        "notas": data.notas,
        "proxima_itv": data.proxima_itv,
        "telefono": data.telefono
    }).execute()
    return {"status": "ok"}

# --- RUTAS DE AVISOS WHATSAPP ---

@app.post("/avisar_terminado")
async def avisar_terminado(data: AvisoData):
    msg = f"Hola, su vehículo con matrícula *{data.matricula}* ya está listo en AutomaDrive. ✅ Puede pasar a recogerlo."
    link_wa = f"https://wa.me/{data.telefono}?text={msg.replace(' ', '%20')}"
    await app.state.bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"📢 *LISTO:* {data.matricula}\n[ENVIAR WHATSAPP]({link_wa})", parse_mode='Markdown')
    return {"status": "ok"}

@app.post("/avisar_proxima_itv")
async def avisar_proxima_itv(data: AvisoData):
    msg = f"Hola {data.propietario}, le recordamos que su ITV ({data.matricula}) vence el {data.fecha_itv}. 🗓️ Estaciones cercanas: http://googleusercontent.com/maps.google.com/5"
    link_wa = f"https://wa.me/{data.telefono}?text={msg.replace(' ', '%20')}"
    await app.state.bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"🗓️ *AVISO ITV:* {data.matricula}\n[ENVIAR CON MAPA]({link_wa})", parse_mode='Markdown')
    return {"status": "ok"}

# --- LÓGICA DE TELEGRAM ---

async def handle_telegram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or str(update.effective_chat.id) != ADMIN_CHAT_ID: return
    
    if update.message.photo:
        foto = await update.message.photo[-1].get_file()
        fb = await foto.download_as_bytearray()
        txt = pytesseract.image_to_string(Image.open(BytesIO(fb)).convert('L'), config='--psm 7')
        matricula = "".join(filter(str.isalnum, txt)).upper()
    else:
        matricula = update.message.text.upper().strip().replace(" ", "")

    if len(matricula) < 4: return

    # Registrar entrada en la nube
    supabase.table("entradas").insert({"matricula": matricula, "fecha": datetime.datetime.now().strftime("%H:%M:%S")}).execute()

    # Buscar cliente
    res = supabase.table("clientes").select("*").eq("matricula", matricula).execute()
    
    if res.data:
        c = res.data[0]
        analisis = motor_ia_diagnostico(c)
        msg = f"🚀 *VEHÍCULO:* {matricula}\n👤 *Cliente:* {c['propietario']}\n🚘 *Modelo:* {c['modelo']}\n\n{analisis}"
        kb = [[InlineKeyboardButton("📞 WhatsApp", url=f"https://wa.me/{c['telefono']}")]]
        await update.message.reply_text(msg, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(kb))
    else:
        await update.message.reply_text(f"🆕 *NUEVO:* {matricula}\nFicha no encontrada. Regístrala en el panel.")

@app.on_event("startup")
async def startup():
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.state.bot = application.bot
    application.add_handler(MessageHandler(filters.PHOTO | filters.TEXT, handle_telegram))
    await application.initialize(); await application.start(); await application.updater.start_polling()
    print("⚡ SISTEMA SAAS ONLINE - CONECTADO A SUPABASE")

@app.get("/")
async def root(): return RedirectResponse(url="/admin.html")

@app.get("/admin.html")
async def servir_admin(): return FileResponse("admin.html")

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)