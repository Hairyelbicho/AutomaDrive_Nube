# 🔄 GUÍA DE SINCRONIZACIÓN CON VPS

## 📋 OPCIONES PARA SINCRONIZAR

### **OPCIÓN 1: Usando Git (Recomendado)**

Si tu proyecto está en un repositorio Git:

```bash
# 1. En tu PC local (C:\AutomaDrive)
git add .
git commit -m "Actualización: Botones Telegram y Video Foso corregidos"
git push origin main

# 2. En el VPS (SSH)
cd /ruta/a/tu/proyecto
git pull origin main
# Reiniciar el servidor
```

### **OPCIÓN 2: Usando SCP/SFTP (Copia directa)**

```powershell
# Desde PowerShell en tu PC
# Reemplaza con tus datos del VPS:
$VPS_USER = "tu_usuario"
$VPS_HOST = "tu_vps_ip_o_dominio"
$VPS_PATH = "/ruta/del/proyecto"

# Copiar archivos modificados
scp C:\AutomaDrive\admin.html ${VPS_USER}@${VPS_HOST}:${VPS_PATH}/admin.html
scp C:\AutomaDrive\templates\admin.html ${VPS_USER}@${VPS_HOST}:${VPS_PATH}/templates/admin.html
scp C:\AutomaDrive\app.py ${VPS_USER}@${VPS_HOST}:${VPS_PATH}/app.py
```

### **OPCIÓN 3: Usando WinSCP o FileZilla (Interfaz gráfica)**

1. Conecta a tu VPS con WinSCP/FileZilla
2. Sube estos archivos:
   - `admin.html`
   - `templates/admin.html`
   - `app.py`
3. Reinicia el servidor en el VPS

---

## 🚀 PASOS DETALLADOS

### **PASO 1: Identificar archivos modificados**

Archivos que necesitas subir:
- ✅ `C:\AutomaDrive\admin.html`
- ✅ `C:\AutomaDrive\templates\admin.html`
- ✅ `C:\AutomaDrive\app.py`

### **PASO 2: Conectar al VPS**

```powershell
# SSH al VPS
ssh usuario@automadrivepro.online
# O
ssh usuario@tu_ip_vps
```

### **PASO 3: Navegar al directorio del proyecto**

```bash
cd /ruta/del/proyecto
# Ejemplo común:
# cd /var/www/automadrive
# cd /home/usuario/automadrive
# cd /opt/automadrive
```

### **PASO 4: Hacer backup (Recomendado)**

```bash
cp app.py app.py.backup
cp templates/admin.html templates/admin.html.backup
```

### **PASO 5: Subir archivos**

**Si usas Git:**
```bash
git pull
```

**Si usas SCP desde tu PC:**
```powershell
# Desde PowerShell en tu PC
scp C:\AutomaDrive\app.py usuario@automadrivepro.online:/ruta/del/proyecto/app.py
scp C:\AutomaDrive\templates\admin.html usuario@automadrivepro.online:/ruta/del/proyecto/templates/admin.html
scp C:\AutomaDrive\admin.html usuario@automadrivepro.online:/ruta/del/proyecto/admin.html
```

### **PASO 6: Reiniciar el servidor en el VPS**

**Si usas systemd (servicio):**
```bash
sudo systemctl restart automadrive
# O el nombre de tu servicio
```

**Si usas supervisor:**
```bash
sudo supervisorctl restart automadrive
```

**Si lo ejecutas manualmente:**
```bash
# Detener proceso actual
pkill -f "python app.py"
# O encontrar el PID
ps aux | grep "python app.py"
kill [PID]

# Iniciar de nuevo
cd /ruta/del/proyecto
python3 app.py
# O si usas gunicorn/uvicorn:
gunicorn app:app --bind 0.0.0.0:5000
```

**Si usas PM2:**
```bash
pm2 restart automadrive
# O
pm2 restart app.py
```

**Si usas screen/tmux:**
```bash
# Detener: Ctrl+C en la sesión
# Reiniciar:
screen -S automadrive
# O
tmux attach -t automadrive
python3 app.py
```

### **PASO 7: Verificar que funciona**

```bash
# En el VPS
curl http://localhost:5000/api/health
```

O abre en el navegador: https://automadrivepro.online/

---

## 🔧 CONFIGURACIÓN ESPECÍFICA PARA TU VPS

Para darte instrucciones más precisas, necesito saber:

1. **¿Cómo ejecutas el servidor en el VPS?**
   - systemd service
   - supervisor
   - PM2
   - screen/tmux
   - manualmente
   - Docker

2. **¿Qué ruta tiene el proyecto en el VPS?**
   - Ejemplo: `/var/www/automadrive`
   - Ejemplo: `/home/usuario/automadrive`

3. **¿Usas Git o subes archivos manualmente?**

---

## 📝 SCRIPT AUTOMÁTICO DE SINCRONIZACIÓN

Puedo crear un script que automatice todo el proceso. ¿Quieres que lo haga?

