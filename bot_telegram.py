# -*- coding: utf-8 -*-
import telebot
import threading
import os
from dotenv import load_dotenv
from datetime import datetime
from supabase import create_client, Client

# 1. CARGAR CONFIGURACIÓN
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")  # <--- Esta línea es la que te faltaba
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
ID_TALLER_PRO = "68b4f064-657d-47a0-b95f-732356ffc5c1"

# 2. VERIFICACIÓN DE SEGURIDAD
if not TOKEN:
    print("❌ ERROR: No se encuentra TELEGRAM_TOKEN en el .env")
    exit()

# 3. INICIAR BOT Y CLIENTE
bot = telebot.TeleBot(TOKEN)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def guardar_nube_async(datos):
    try:
        supabase.table("clientes").insert(datos).execute()
        print(f"☁️ Sincronizado: {datos['matricula']}")
    except Exception as e:
        print(f"❌ Error Nube: {e}")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🤖 AutomaDrive Pro Activo. Envíame: MATRICULA NOTAS")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    partes = message.text.split(" ", 1)
    matricula = partes[0].upper()
    notas = partes[1] if len(partes) > 1 else "Ingreso desde Telegram"
    
    datos = {
        "taller_id": ID_TALLER_PRO,
        "matricula": matricula,
        "notas": notas,
        "fecha": datetime.now().isoformat()
    }
    
    bot.reply_to(message, f"✅ Registrada matrícula: {matricula}")
    threading.Thread(target=guardar_nube_async, args=(datos,)).start()

print("🚀 Bot de Telegram en marcha...")
bot.infinity_polling()
