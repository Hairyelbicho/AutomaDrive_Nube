import os
import datetime
import re
import pytesseract
import asyncio
from PIL import Image
from io import BytesIO
from urllib.parse import quote # MEJORA: Para enlaces de WhatsApp seguros
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel
from supabase import create_client, Client
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
# Si tus plantillas “reales” están en /templates, usamos esa carpeta
templates = Jinja2Templates(directory="templates")

# Servir archivos estáticos (imágenes, css, js)
app.mount("/static", StaticFiles(directory="static"), name="static")
# --- CARGAR VARIABLES DE ENTORNO ---
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

# Conexión profesional a Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- CONFIGURACIÓN DE FASTAPI ---
app = FastAPI(title="AutomaDrive API")

# Configuración CORS básica (ajusta orígenes si tienes frontend concreto)
app.add_middleware(
 CORSMiddleware,
 allow_origins=["*"], # pon aquí tu dominio si quieres restringir
 allow_credentials=True,
 allow_methods=["*"],
 allow_headers=["*"],
)

# MODELOS Pydantic (si necesitas alguno para tus endpoints)
class ExamplePayload(BaseModel):
 data: str

# --- ENDPOINT RAÍZ PARA COMPROBACIÓN ---
@app.get("/")
async def read_root():
 return {"message": "AutomaDrive API OK", "status": "running"}

# -------------------------------------------------------------------
# A PARTIR DE AQUÍ, TU LÓGICA EXISTENTE (Telegram bot, OCR, rutas, etc.)
# -------------------------------------------------------------------

# EJEMPLO de endpoint para probar conexión con Supabase (opcional)
@app.get("/health")
async def health_check():
 try:
 # consulta muy ligera solo para verificar
 supabase.table("your_table_name").select("id").limit(1).execute()
 db_status = "ok"
 except Exception:
 db_status = "error"

 return {
 "service": "AutomaDrive",
 "api": "ok",
 "database": db_status,
 "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
 }

# Aquí irían tus endpoints reales, por ejemplo:
# @app.post("/procesar")
# async def procesar(payload: ExamplePayload):
# # tu lógica...
# return {"ok": True, "received": payload.data}

# ------------------------------------
# TELEGRAM BOT (si lo estás usando)
# ------------------------------------

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
 # tu lógica de respuesta aquí, usando Supabase, OCR, etc.
 text = update.message.text or ""
 await update.message.reply_text(f"Mensaje recibido: {text}")

async def start_telegram_bot():
 application = (
 ApplicationBuilder()
 .token(TELEGRAM_TOKEN)
 .build()
 )

 application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

 # Ejecutar el bot de forma asíncrona en segundo plano
 await application.initialize()
 await application.start()
 # NOTA: no llamamos a application.run_polling() para no bloquear FastAPI

# Lanzar el bot al arrancar la app
@app.on_event("startup")
async def on_startup():
 if TELEGRAM_TOKEN:
 asyncio.create_task(start_telegram_bot())
 else:
 # Si falta el token, simplemente no iniciamos el bot
 pass

# Si tienes más endpoints/funciones, déjalos debajo sin modificar su estructura original.

# Raíz del dominio: mostrar admin.html (el que está en /templates)
@app.get("/", response_class=HTMLResponse)
async def serve_admin_root(request: Request):
 return templates.TemplateResponse("admin.html", {"request": request})

# Opcional: ruta para index.html
@app.get("/index", response_class=HTMLResponse)
async def serve_index(request: Request):
 return templates.TemplateResponse("index.html", {"request": request})