# 🍓 SINCRONIZACIÓN DESDE RASPBERRY PI AL VPS

## 📋 PASOS PARA ACTUALIZAR DESDE TU RASPBERRY PI

### **PASO 1: Copiar archivos actualizados a tu Raspberry Pi**

Primero, necesitas copiar los archivos modificados desde tu PC a la Raspberry Pi:

**Opción A: Usando SCP desde tu PC**
```powershell
# Desde PowerShell en tu PC (C:\AutomaDrive)
scp app.py pi@IP_RASPBERRY:/home/pi/AutomaDrive/app.py
scp admin.html pi@IP_RASPBERRY:/home/pi/AutomaDrive/admin.html
scp templates/admin.html pi@IP_RASPBERRY:/home/pi/AutomaDrive/templates/admin.html
```

**Opción B: Usando USB/Red compartida**
- Copia los archivos a una USB
- O usa una carpeta compartida en red

**Opción C: Usando Git (si tienes repositorio)**
```bash
# En Raspberry Pi
cd /home/pi/AutomaDrive
git pull origin main
```

---

### **PASO 2: Conectar a tu Raspberry Pi**

```bash
ssh pi@IP_RASPBERRY
# O
ssh pi@raspberrypi.local
```

---

### **PASO 3: Configurar el script de sincronización**

```bash
cd /home/pi/AutomaDrive

# Editar el script con tus datos del VPS
nano sync_raspberry_to_vps.sh
```

**Edita estas líneas:**
```bash
VPS_USER="tu_usuario"           # Tu usuario SSH del VPS
VPS_HOST="automadrivepro.online" # Tu dominio o IP del VPS
VPS_PATH="/var/www/automadrive"  # Ruta exacta en el VPS
```

**Guardar:** `Ctrl+X`, luego `Y`, luego `Enter`

---

### **PASO 4: Dar permisos de ejecución**

```bash
chmod +x sync_raspberry_to_vps.sh
```

---

### **PASO 5: Ejecutar la sincronización**

```bash
./sync_raspberry_to_vps.sh
```

---

## 🔧 CONFIGURACIÓN MANUAL (Si prefieres hacerlo paso a paso)

### **1. Subir archivos desde Raspberry Pi al VPS**

```bash
# Desde tu Raspberry Pi
scp /home/pi/AutomaDrive/app.py usuario@automadrivepro.online:/ruta/del/proyecto/app.py

scp /home/pi/AutomaDrive/admin.html usuario@automadrivepro.online:/ruta/del/proyecto/admin.html

scp /home/pi/AutomaDrive/templates/admin.html usuario@automadrivepro.online:/ruta/del/proyecto/templates/admin.html
```

### **2. Conectar al VPS y reiniciar**

```bash
# Conectar al VPS
ssh usuario@automadrivepro.online

# Ir al directorio del proyecto
cd /ruta/del/proyecto

# Reiniciar el servidor (elige el método que uses):

# Método 1: systemd
sudo systemctl restart automadrive

# Método 2: supervisor
sudo supervisorctl restart automadrive

# Método 3: PM2
pm2 restart automadrive

# Método 4: Manual (detener y reiniciar)
pkill -f "python.*app.py"
nohup python3 app.py > /dev/null 2>&1 &

# Método 5: gunicorn
pkill -f gunicorn
nohup gunicorn app:app --bind 0.0.0.0:5000 > /dev/null 2>&1 &
```

---

## 🔑 CONFIGURAR SSH SIN CONTRASEÑA (Opcional, más cómodo)

Para no tener que escribir la contraseña cada vez:

```bash
# En tu Raspberry Pi
ssh-keygen -t rsa
ssh-copy-id usuario@automadrivepro.online
```

Ahora podrás conectarte sin contraseña.

---

## 📝 VERIFICAR QUE FUNCIONA

```bash
# Desde el VPS
curl http://localhost:5000/api/health

# O desde tu navegador
# https://automadrivepro.online/
```

---

## 🚀 AUTOMATIZACIÓN CON CRON (Opcional)

Para sincronizar automáticamente cada cierto tiempo:

```bash
# Editar crontab
crontab -e

# Añadir esta línea (sincroniza cada hora):
0 * * * * /home/pi/AutomaDrive/sync_raspberry_to_vps.sh >> /home/pi/sync.log 2>&1
```

---

## ❓ ¿NECESITAS AYUDA?

Para darte instrucciones más precisas, necesito saber:

1. **¿Cuál es la IP o hostname de tu Raspberry Pi?**
2. **¿Cuál es el usuario SSH del VPS?**
3. **¿Cuál es la ruta exacta del proyecto en el VPS?**
   - Ejemplo: `/var/www/automadrive`
   - Ejemplo: `/home/usuario/automadrive`
4. **¿Cómo ejecutas el servidor en el VPS?**
   - systemd service
   - supervisor
   - PM2
   - manualmente
   - gunicorn/uvicorn

Con esta información puedo crear un script personalizado para ti.

