# 🚀 Migración de BatBot a Railway

## 📋 Checklist de Migración

### ✅ Archivos Preparados
- [x] `main.py` - Código principal del bot
- [x] `requirements.txt` - Dependencias de Python
- [x] `pyproject.toml` - Configuración del proyecto
- [x] `templates/` - Plantillas HTML para dashboard
- [x] `static/` - Archivos CSS
- [x] `.gitignore` - Archivos a ignorar en Git

### 🔧 Pasos de Migración

#### 1. Subir a GitHub

**Opción A: Usando Git (si está instalado correctamente)**
```bash
git init
git add .
git commit -m "Initial commit - BatBot for Railway"
git branch -M main
git remote add origin https://github.com/tu-usuario/batbot.git
git push -u origin main
```

**Opción B: Subida Manual (Recomendada si Git tiene problemas)**
1. Ir a [GitHub.com](https://github.com) y crear un nuevo repositorio
2. Nombrar el repositorio "batbot" o "BatBot"
3. NO inicializar con README (ya tenemos archivos)
4. Comprimir todos los archivos del proyecto en un ZIP
5. En GitHub: "uploading an existing file" → Arrastrar el ZIP
6. O usar GitHub Desktop para sincronizar la carpeta

**Opción C: GitHub Desktop (Más fácil)**
1. Descargar [GitHub Desktop](https://desktop.github.com/)
2. "Add an Existing Repository from your Hard Drive"
3. Seleccionar la carpeta `BatBot`
4. Publish repository to GitHub

#### 2. Configurar Railway
1. Ir a [Railway.app](https://railway.app) <mcreference link="https://railway.app" index="0">0</mcreference>
2. Registrarse con GitHub
3. Crear nuevo proyecto → "Deploy from GitHub repo"
4. Seleccionar el repositorio de BatBot

#### 3. Variables de Entorno en Railway
Agregar estas variables en Railway Dashboard:

```
DISCORD_TOKEN=tu_token_de_discord_aqui
PORT=8080
```

#### 4. Configuración Automática
Railway detectará automáticamente:
- `requirements.txt` → Instalará dependencias Python
- `main.py` → Ejecutará como punto de entrada
- Puerto 8080 → Para el servidor Flask

### 🎯 Configuración Específica de BatBot

#### Variables de Entorno Requeridas:
- `DISCORD_TOKEN`: Token del bot de Discord

#### Canales de Voz a Configurar:
Actualizar los IDs en `main.py` línea 18-25:
```python
VALID_VOICE_CHANNELS = [
    1405053196443062336,  # BATCAVE
    1405377739829022720,  # 🛡️[BAT-COMPANY] CLAN #1
    380104919124017155,   # 🍗PUBG TPP CHANNEL #1
    1405377302430220350,  # 🍗PUBG TPP CHANNEL #2
    1405423954474172498,  # 🍗PUBG FPP CHANNEL #1
    1405424126876975227,  # 🍗PUBG FPP CHANNEL #2
]
```

### 🔍 Verificación Post-Deploy

1. **Bot Online**: Verificar que el bot aparezca online en Discord
2. **Comandos**: Probar `!voice_stats`, `!config`
3. **Dashboard**: Acceder a la URL de Railway para ver el dashboard web
4. **Roles**: Verificar que el sistema de roles progresivos funcione

### 💰 Costos Railway
- **Plan Gratuito**: $5 USD de crédito mensual
- **Suficiente para**: Bot 24/7 + Dashboard web
- **Uso estimado**: ~$3-4 USD/mes para este bot

### 🆘 Troubleshooting

#### Bot no se conecta:
- Verificar `DISCORD_TOKEN` en variables de entorno
- Revisar logs en Railway Dashboard

#### Roles no se asignan:
- Verificar permisos del bot en Discord
- Bot debe estar por encima de los roles progresivos

#### Dashboard no carga:
- Verificar que Flask esté corriendo en puerto 8080
- Revisar logs de la aplicación

### 📞 Comandos de Admin Disponibles
- `!voice_stats` - Estadísticas de canales de voz
- `!config` - Configuración del bot
- `!roletest <minutos>` - Probar sistema de roles
- `!scan` - Escanear usuarios conectados
- `!history` - Historial de actividad

---

**¡Tu BatBot estará corriendo 24/7 en Railway! 🦇**