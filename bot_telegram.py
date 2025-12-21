import telebot
import threading
from datetime import datetime
from supabase import create_client, Client

# --- CONFIGURACIÓN ---
TOKEN = "TU_TOKEN_DE_TELEGRAM"
SUPABASE_URL = "https://tu-proyecto.supabase.co"
SUPABASE_KEY = "tu-clave-anon"
ID_TALLER_PRO = "68b4f064-657d-47a0-b95f-732356ffc5c1"

bot = telebot.TeleBot(TOKEN)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Función para guardar en la nube sin detener el bot
def guardar_nube_async(datos):
    try:
        supabase.table("clientes").insert(datos).execute()
        print(f"?? Telegram: Sincronizado en la nube para {datos['matricula']}")
    except Exception as e:
        print(f"? Error nube desde Telegram: {e}")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "?? AutomaDrive Pro Activo. Envíame una matrícula y notas (Ej: 1234ABC Cambio de aceite)")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    texto = message.text
    print(f"?? Mensaje de Telegram: {texto}")

    # Simulamos procesar una matrícula (Primera palabra)
    partes = texto.split(" ", 1)
    matricula = partes[0].upper()
    notas = partes[1] if len(partes) > 1 else "Ingreso desde Telegram"

    datos_cliente = {
        "taller_id": ID_TALLER_PRO,
        "matricula": matricula,
        "notas": notas,
        "fecha": datetime.now().isoformat()
    }

    # RESPUESTA INSTANTÁNEA AL MÓVIL
    bot.reply_to(message, f"? Recibido. Matrícula {matricula} registrada en el sistema.")

    # GUARDADO EN SEGUNDO PLANO (HILO APARTE)
    threading.Thread(target=guardar_nube_async, args=(datos_cliente,)).start()

print("?? Bot de Telegram en marcha...")
bot.infinity_polling()