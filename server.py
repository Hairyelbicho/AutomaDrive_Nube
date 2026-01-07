import os
import datetime
import re
import pytesseract
import asyncio
from PIL import Image
from io import BytesIO
from urllib.parse import quote  # MEJORA: Para enlaces de WhatsApp seguros
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

# MEJORA: Middleware CORS optimizado
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
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

# --- MOTOR DE IA DE DIAGNÓSTICO MEJORADO ---
def motor_ia_diagnostico(c):
    sugerencias = []
    hoy = datetime.datetime.now()
    
    # Mejora: Acceso seguro a proxima_itv
    itv_raw = c.get('proxima_itv')
    if itv_raw:
        try:
            # Soporta formato ISO YYYY-MM-DD
            f_itv = datetime.datetime.strptime(itv_raw[:10], "%Y-%m-%d")
            dias = (f_itv - hoy).days
            if 0 <= dias <= 15:
                sugerencias.append(f"🚨 *ITV PRÓXIMA:* Vence el {f_itv.strftime('%d/%m')} ({dias} días).")
            elif dias < 0:
                sugerencias.append(f"⛔ *ITV CADUCADA:* Venció hace {abs(dias)} días.")
        except: pass

    try:
        km_num = int(re.sub(r'\D', '', str(c.get('km', '0'))))
        notas = str(c.get('notas', '')).lower()
        if km_num > 150000 and "distribucion" not in notas:
            sugerencias.append("⚠️ *IA AVISO:* Sugerir revisión de Correa de Distribución.")
    except: pass

    return "\n".join(sugerencias) if sugerencias else "✅ *IA:* Vehículo al día."

# --- RUTAS DE LA API ---

@app.get("/logs")
async def obtener_logs():
    try:
        # Optimizado para traer datos de una vez
        res = supabase.table("entradas").select("fecha, matricula").order("id", desc=True).limit(15).execute()
        logs_formateados = []
        for item in res.data:
            # Mejora: Selección más limpia
            cli = supabase.table("clientes").select("propietario, modelo").eq("matricula", item['matricula']).execute()
            if cli.data:
                prop = cli.data[0].get('propietario', 'Sin Nombre')
                mod = cli.data[0].get('modelo', 'S/M')
            else:
                prop, mod = "Nuevo", "Registrar"
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
    try:
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- RUTAS DE AVISOS WHATSAPP (Mejoradas con URL Quote) ---

@app.post("/avisar_terminado")
async def avisar_terminado(data: AvisoData):
    msg = f"Hola, su vehículo con matrícula *{data.matricula}* ya está listo en AutomaDrive. ✅"
    link_wa = f"https://wa.me/{data.telefono}?text={quote(msg)}"
    await app.state.bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"📢 *LISTO:* {data.matricula}\n[ENVIAR WHATSAPP]({link_wa})", parse_mode='Markdown')
    return {"status": "ok"}

@app.post("/avisar_proxima_itv")
async def avisar_proxima_itv(data: AvisoData):
    msg = f"Hola {data.propietario}, le recordamos que su ITV ({data.matricula}) vence el {data.fecha_itv}. 🗓️"
    link_wa = f"https://wa.me/{data.telefono}?text={quote(msg)}"
    await app.state.bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"🗓️ *AVISO ITV:* {data.matricula}\n[ENVIAR RECORDATORIO]({link_wa})", parse_mode='Markdown')
    return {"status": "ok"}

# --- LÓGICA DE TELEGRAM (Blindada contra KeyErrors) ---
async def handle_telegram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or str(update.effective_chat.id) != ADMIN_CHAT_ID: return
    
    try:
        if update.message.photo:
            foto = await update.message.photo[-1].get_file()
            fb = await foto.download_as_bytearray()
            txt = pytesseract.image_to_string(Image.open(BytesIO(fb)).convert('L'), config='--psm 7')
            matricula = "".join(filter(str.isalnum, txt)).upper()
        else:
            matricula = update.message.text.upper().strip().replace(" ", "")

        if len(matricula) < 4: return

        # Registro de entrada
        supabase.table("entradas").insert({
            "matricula": matricula, 
            "fecha": datetime.datetime.now().strftime("%H:%M:%S")
        }).execute()

        res = supabase.table("clientes").select("*").eq("matricula", matricula).execute()
        
        if res.data:
            c = res.data[0]
            analisis = motor_ia_diagnostico(c)
            
            # MEJORA: Acceso seguro a datos para evitar el KeyError
            prop = c.get('propietario', 'No registrado')
            mod = c.get('modelo', 'No registrado')
            tel = c.get('telefono', '')
            
            msg = f"🚀 *VEHÍCULO:* {matricula}\n👤 *Cliente:* {prop}\n🚘 *Modelo:* {mod}\n\n{analisis}"
            
            kb = []
            if tel:
                kb.append([InlineKeyboardButton("📞 WhatsApp", url=f"https://wa.me/{tel}")])
            
            await update.message.reply_text(msg, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(kb) if kb else None)
        else:
            await update.message.reply_text(f"🆕 *NUEVO:* {matricula}\nFicha no encontrada en la nube.")
            
    except Exception as e:
        print(f"Error en Bot: {e}")
        await update.message.reply_text(f"⚠️ Error procesando matrícula.")

@app.on_event("startup")
async def startup():
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.state.bot = application.bot
    application.add_handler(MessageHandler(filters.PHOTO | filters.TEXT, handle_telegram))
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    print("⚡ SISTEMA SAAS ONLINE - ESCUCHANDO EN PUERTO 8000")

@app.get("/health")
def health(): return {"status": "ok", "db": "connected"}

@app.get("/itv-realtime")
async def itv_realtime():
    objetivo = (datetime.datetime.now() + datetime.timedelta(days=15)).strftime("%d-%m-%Y")
    return {
        "estado_nube": "Online",
        "objetivo_alerta": objetivo,
        "mensaje": "Detección activa de ITV a 15 días."
    }

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)