# ⚙️ Configuración Completa de Railway para BatBot

## 📋 Prerequisitos
- ✅ Proyecto subido a GitHub
- ✅ Cuenta en Railway.app creada
- ✅ Token de Discord bot disponible

---

## 🚀 Paso 1: Crear Proyecto en Railway

### 1.1 Acceder a Railway
1. Ir a [Railway.app](https://railway.app)
2. Hacer clic en "Login" → "Login with GitHub"
3. Autorizar Railway para acceder a tus repositorios

### 1.2 Crear Nuevo Proyecto
1. Clic en "New Project"
2. Seleccionar "Deploy from GitHub repo"
3. Buscar y seleccionar tu repositorio "BatBot"
4. Clic "Deploy Now"

---

## 🔧 Paso 2: Configurar Variables de Entorno

### 2.1 Acceder a Variables
1. En tu proyecto Railway, clic en el servicio desplegado
2. Ir a la pestaña "Variables"
3. Clic "+ New Variable"

### 2.2 Variables Requeridas

#### Variable 1: DISCORD_TOKEN
```
Key: DISCORD_TOKEN
Value: a6f4daabb68963e6c7c65beca88dbd63070d56357918117a4937f8df4e8f3690
``` 
**⚠️ IMPORTANTE:** 
- Este es tu token específico (ya proporcionado)
- NUNCA lo compartas públicamente
- Solo configúralo en Railway Variables (no en el código)
- El código ya está preparado para leerlo con `os.getenv('DISCORD_TOKEN')`

#### Variable 2: PORT (Opcional)
```
Key: PORT
Value: 8080
```
**Nota:** Railway asigna puerto automáticamente, pero BatBot usa 8080 por defecto.

### 2.3 Variables Adicionales (Si las necesitas)

#### Para Base de Datos (si agregas una)
```
Key: DATABASE_URL
Value: [URL_DE_TU_BASE_DE_DATOS]
```

#### Para Configuración Personalizada
```
Key: BOT_PREFIX
Value: !

Key: DEBUG_MODE
Value: false
```

---

## 🎯 Paso 3: Configurar Canales de Discord

### 3.1 Obtener IDs de Canales
1. En Discord, activar "Modo Desarrollador":
   - Configuración → Avanzado → Modo Desarrollador ✅
2. Clic derecho en cada canal de voz → "Copiar ID"

### 3.2 Actualizar IDs en el Código
En Railway, editar el archivo `main.py` (líneas 18-25):
```python
VALID_VOICE_CHANNELS = [
    1234567890123456789,  # TU_CANAL_1
    1234567890123456790,  # TU_CANAL_2
    1234567890123456791,  # TU_CANAL_3
    # Agregar más canales según necesites
]
```

---

## 🔄 Paso 4: Deploy y Verificación

### 4.1 Iniciar Deploy
1. Railway detectará cambios automáticamente
2. Ver logs en tiempo real en la pestaña "Deployments"
3. Esperar a que aparezca "Build successful" y "Deployment live"

### 4.2 Verificar Logs
```
✅ Logs exitosos deben mostrar:
🦇 Starting BatCompany Discord Bot...
✅ Discord token loaded from environment variables
🚀 Starting bot...
[BOT_NAME] ha iniciado sesión y está listo!
🌐 Servidor Flask iniciado para mantener el bot activo
```

### 4.3 Verificar Bot en Discord
1. **Bot Online:** Verificar que aparezca online en tu servidor
2. **Comandos:** Probar `!voice_stats` en un canal de texto
3. **Roles:** Conectarse a un canal de voz monitoreado
4. **Dashboard:** Acceder a la URL de Railway para ver el dashboard

---

## 🌐 Paso 5: Configurar Dominio (Opcional)

### 5.1 Obtener URL del Dashboard
1. En Railway → Tu servicio → "Settings"
2. Copiar la URL generada (ej: `https://batbot-production.up.railway.app`)
3. Esta URL mostrará el dashboard web del bot

### 5.2 Dominio Personalizado (Opcional)
1. En "Settings" → "Domains"
2. Clic "+ Custom Domain"
3. Ingresar tu dominio (ej: `batbot.tudominio.com`)
4. Configurar DNS según las instrucciones

---

## 🛠️ Paso 6: Configuración del Bot en Discord

### 6.1 Permisos Requeridos
El bot necesita estos permisos en tu servidor:
- ✅ **Ver Canales**
- ✅ **Enviar Mensajes**
- ✅ **Gestionar Roles**
- ✅ **Ver Canales de Voz**
- ✅ **Conectar a Canales de Voz**

### 6.2 Jerarquía de Roles
**IMPORTANTE:** El rol del bot debe estar **por encima** de los roles que asigna:
```
🔝 @BatBot (rol del bot)
   ⬇️
   🎖️ Dark Commander
   📡 Eco-Legend
   🦇 Ala Chueca
   🍼 Murci-Casual
   👥 @everyone
```

### 6.3 Crear Roles Progresivos
Crear manualmente estos roles en tu servidor:
1. **Murci-Casual 🍼** - Color: Gris claro
2. **Ala Chueca 🦇** - Color: Naranja
3. **Eco-Legend 📡** - Color: Azul
4. **Dark Commander 🎖️** - Color: Púrpura

---

## 🔍 Troubleshooting

### ❌ Bot no se conecta
**Problema:** "Invalid Discord token"
**Solución:**
1. Verificar `DISCORD_TOKEN` en Railway Variables
2. Regenerar token en Discord Developer Portal
3. Actualizar variable en Railway

### ❌ Roles no se asignan
**Problema:** Bot no puede asignar roles
**Solución:**
1. Verificar permisos "Gestionar Roles"
2. Mover rol del bot por encima de roles progresivos
3. Verificar que los roles existan en el servidor

### ❌ Dashboard no carga
**Problema:** Error 500 en la URL de Railway
**Solución:**
1. Verificar logs en Railway
2. Confirmar que Flask esté corriendo en puerto correcto
3. Revisar variables de entorno

### ❌ Comandos no responden
**Problema:** Bot no responde a `!voice_stats`
**Solución:**
1. Verificar que el bot tenga permisos "Enviar Mensajes"
2. Confirmar que el prefijo sea `!`
3. Probar en canal donde el bot tenga permisos

---

## 📊 Monitoreo y Mantenimiento

### Logs en Tiempo Real
1. Railway Dashboard → Tu servicio → "Logs"
2. Filtrar por tipo: `Error`, `Warning`, `Info`

### Métricas de Uso
1. Railway Dashboard → "Metrics"
2. Monitorear CPU, RAM, y tráfico de red
3. Verificar que esté dentro del límite de $5 USD

### Actualizaciones
1. Hacer cambios en GitHub
2. Railway redesplegará automáticamente
3. Verificar logs después de cada actualización

---

## 💰 Costos y Límites

- **Plan Gratuito:** $5 USD de crédito mensual
- **Uso Estimado BatBot:** $3-4 USD/mes
- **Incluye:** Hosting 24/7 + Base de datos pequeña
- **Límite:** 500 horas de ejecución/mes (suficiente para 24/7)

---

**🎉 ¡Tu BatBot estará corriendo 24/7 en Railway!**

Para soporte adicional, revisar:
- [Documentación Railway](https://docs.railway.app/)
- [Discord.py Documentación](https://discordpy.readthedocs.io/)