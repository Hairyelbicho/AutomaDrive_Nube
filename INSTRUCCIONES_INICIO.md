# 🚀 GUÍA DE INICIO RÁPIDO - AutomaDrive Pro

## 📍 UBICACIÓN DEL PROYECTO

**Ruta completa:** `C:\AutomaDrive\`

## ✅ ESTADO ACTUAL

✅ **TODO ESTÁ LISTO Y FUNCIONAL** - Solo necesitas seguir estos pasos:

---

## 📋 PASOS PARA INICIAR EL PROYECTO

### **PASO 1: Abrir Terminal/PowerShell**

1. Presiona `Windows + R`
2. Escribe: `powershell` o `cmd`
3. Presiona Enter

### **PASO 2: Navegar al directorio del proyecto**

```powershell
cd C:\AutomaDrive
```

### **PASO 3: Crear entorno virtual (Recomendado)**

```powershell
python -m venv venv
```

Luego activarlo:
```powershell
.\venv\Scripts\activate
```

### **PASO 4: Instalar dependencias**

```powershell
pip install -r requirements.txt
```

**Esto instalará:**
- Flask (servidor web)
- OpenAI (para IA avanzada)
- aiohttp (para Telegram/WhatsApp)
- flask-cors (para CORS)
- twilio (para WhatsApp Business)

### **PASO 5: Crear carpeta de templates (si no existe)**

El archivo `admin.html` debe estar en:
- `C:\AutomaDrive\admin.html` (archivo original)
- `C:\AutomaDrive\templates\admin.html` (para Flask)

**Si no existe la carpeta templates:**
```powershell
mkdir templates
copy admin.html templates\admin.html
```

### **PASO 6: Crear carpeta static (para el logo)**

```powershell
mkdir static
```

**Opcional:** Coloca tu logo en `static\ia-logo.png` (si no está, no pasa nada, simplemente no se mostrará)

### **PASO 7: Iniciar el servidor**

```powershell
python app.py
```

**Deberías ver algo como:**
```
 * Running on http://127.0.0.1:5000
 * Running on http://0.0.0.0:5000
```

### **PASO 8: Abrir en el navegador**

Abre tu navegador y ve a:
```
http://localhost:5000
```

O
```
http://127.0.0.1:5000
```

---

## 🎯 ESTRUCTURA DE ARCHIVOS CREADOS

```
C:\AutomaDrive\
├── admin.html              ✅ Frontend principal (corregido y mejorado)
├── app.py                  ✅ Backend Flask completo
├── requirements.txt        ✅ Dependencias Python
├── templates\
│   └── admin.html          ✅ Template para Flask
├── static\                 📁 (se crea automáticamente)
│   └── ia-logo.png        (opcional)
└── data\                   📁 (se crea automáticamente)
    ├── config.json        (se crea al guardar configuración)
    ├── fichas.json        (se crea al crear fichas)
    └── actividad.json     (se crea automáticamente)
```

---

## ⚙️ CONFIGURACIÓN INICIAL (OPCIONAL)

Una vez que el servidor esté corriendo:

1. **Abre el dashboard** en `http://localhost:5000`
2. **Haz clic en "CONFIG"** (botón dorado arriba a la derecha)
3. **Configura (opcional):**
   - **Telegram Bot Token:** Obtener de @BotFather en Telegram
   - **Telegram Chat ID:** ID del chat/grupo
   - **WhatsApp Business:** Número y token (si usas Twilio)
   - **OpenAI API Key:** Para IA avanzada (opcional)

**NOTA:** El sistema funciona SIN configuración inicial. Solo algunas funciones estarán limitadas.

---

## 🔧 SOLUCIÓN DE PROBLEMAS

### **Error: "No module named 'flask'"**
```powershell
pip install -r requirements.txt
```

### **Error: "Template not found"**
Asegúrate de que existe:
```
C:\AutomaDrive\templates\admin.html
```

Si no existe:
```powershell
mkdir templates
copy admin.html templates\admin.html
```

### **Error: "Port 5000 already in use"**
Cambia el puerto en `app.py` línea final:
```python
app.run(host='0.0.0.0', port=5001, debug=True)  # Cambia 5000 por 5001
```

### **El logo no aparece**
No es crítico. El sistema funciona sin logo. Si quieres añadirlo:
- Coloca `ia-logo.png` en `C:\AutomaDrive\static\`

---

## ✅ VERIFICACIÓN DE QUE TODO FUNCIONA

Una vez iniciado, verifica:

1. ✅ **Dashboard carga** - Ves la interfaz principal
2. ✅ **Reloj funciona** - Muestra la hora actual
3. ✅ **Búsqueda funciona** - Puedes buscar expedientes
4. ✅ **IA responde** - Puedes hacer consultas técnicas (funciona sin OpenAI, con conocimiento local)
5. ✅ **Crear fichas** - Botón "NUEVO INGRESO" funciona
6. ✅ **Configuración** - Botón "CONFIG" guarda datos
7. ✅ **Actividad** - Botón "ACTIVIDAD" muestra historial
8. ✅ **Política de Privacidad** - Enlace en el footer funciona

---

## 🎉 ¡LISTO PARA USAR!

**El proyecto está 100% funcional y listo para trabajar.**

### **Resumen:**
- ✅ Código corregido y mejorado
- ✅ Backend Flask completo
- ✅ IA integrada (funciona con o sin OpenAI)
- ✅ Integración Telegram (configurable)
- ✅ Integración WhatsApp (configurable)
- ✅ Política de privacidad añadida
- ✅ Todas las funciones implementadas

### **Solo necesitas:**
1. Instalar dependencias: `pip install -r requirements.txt`
2. Iniciar servidor: `python app.py`
3. Abrir navegador: `http://localhost:5000`

---

## 📞 SOPORTE

Si tienes algún problema:
- Revisa los logs en la consola donde ejecutaste `python app.py`
- Verifica que todas las dependencias estén instaladas
- Asegúrate de estar en el directorio correcto: `C:\AutomaDrive`

---

**¡Todo está listo para trabajar! 🚗✨**

