#!/bin/bash
# AutomaDrive Pro - Script de Sincronización Real

# ============================================
# CONFIGURACIÓN REAL ACTUALIZADA
# ============================================
VPS_USER="hairy"
VPS_HOST="82.223.107.251"
VPS_PATH="/home/hairy/AutomaDrive"
RASPBERRY_PATH="/home/hairy/AutomaDrive"

# ============================================
# SCRIPT DE SINCRONIZACIÓN
# ============================================

echo "🔄 Sincronizando AutomaDrive Pro al VPS (82.223.107.251)..."

# 1. Subir archivos (app.py y la carpeta de plantillas)
echo "📤 Subiendo archivos actualizados..."
rsync -avz --progress "$RASPBERRY_PATH/app.py" "${VPS_USER}@${VPS_HOST}:${VPS_PATH}/app.py"
rsync -avz --progress "$RASPBERRY_PATH/templates/" "${VPS_USER}@${VPS_HOST}:${VPS_PATH}/templates/"

if [ $? -eq 0 ]; then
    echo "✅ Archivos subidos correctamente."
else
    echo "❌ Error en la subida. Revisa la conexión."
    exit 1
fi

# 2. Reiniciar el servidor en el VPS remotamente
echo "🔄 Reiniciando servidor en la nube..."

ssh "${VPS_USER}@${VPS_HOST}" << 'ENDSSH'
    cd /home/hairy/AutomaDrive
    # Matar cualquier proceso que use el puerto 5000
    sudo fuser -k 5000/tcp || true
    sleep 1
    # Arrancar de nuevo con el nuevo código
    nohup python3 app.py > vps_server.log 2>&1 &
    echo "✅ Servidor Flask reiniciado en el VPS."
ENDSSH

echo "🚀 ¡Todo listo! Verifica en: http://82.223.107.251:5000"