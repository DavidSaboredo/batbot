# 🦇 BatCompany Discord Bot | Bot de Discord BatCompany

**English** | [Español](#español)

---

## English

A Discord bot with progressive role system and cumulative time tracking for PUBG voice channel monitoring. Automatically assigns roles based on accumulated time spent in voice channels across multiple sessions.

### 🎯 Features

- **Voice Channel Monitoring**: Tracks user activity in specified PUBG voice channels
- **Progressive Role System**: Automatically assigns roles based on cumulative connection time
- **Cumulative Time Tracking**: Saves and accumulates time across bot restarts and sessions
- **Data Persistence**: User progress is saved in SQLite and persists between sessions
- **Admin Commands**: Statistics, configuration, and management commands
- **User Commands**: Check personal time and reset progress
- **24/7 Uptime**: Deployed on Bot-Hosting.net for continuous operation

### 🎖️ Progressive Role System

| Role | Time Required | Description |
|------|---------------|--------------|
| Murci-Casual 🍼 | 30 minutes | The newbie who just entered, still crashes into walls like a bat with broken GPS. |
| Ala Chueca 🦇 | 2 hours | Already knows how to move, but still flies crooked and makes fails in PUBG. |
| Murci-Veterano 🦇💪 | 8 hours | The veteran who already masters night flight and distributes headshots like candy. |
| Bat-Commander 🦇⚡ | 20 hours | The master bat, supreme leader of BatCompany, the one who distributes headshots in the dark. |

### 🤖 Commands (slash commands)

#### Everyone
- `/tiempo [usuario]` - Accumulated voice time, current session and next role
- `/ranking [periodo]` - Top 10 by voice time: all-time, last 7 days or last 30 days

#### Admins
- `/canal` - Choose the channel for free games, PUBG news and new-role announcements
- `/estadisticas` - Bot and voice statistics
- `/configuracion` - Monitored channels and role thresholds
- `/resettiempo @usuario` - Reset a user's time
- `/historial [cantidad]` - Recent activity

### 🎁 Free games and PUBG news

Every 30 minutes the bot posts new free games (Epic Games, Steam, GOG) and official PUBG announcements from Steam. Set the channels with `/canal`.

### 💾 Data

Time is stored in SQLite (`batbot.db`, path configurable with `DB_PATH`) and checkpointed every 2 minutes, so a crash loses almost nothing. Point `DB_PATH` to a persistent disk on your host. An old `user_progress.json` is imported automatically the first time.

### 🚀 Setup Instructions

#### 1. Discord Bot Setup

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application and bot
3. Copy the bot token
4. Enable the following intents:
   - Server Members Intent
   - Message Content Intent
   - Presence Intent

#### 2. Bot-Hosting.net Deployment

1. Create an account on [Bot-Hosting.net](https://bot-hosting.net)
2. Connect your GitHub repository
3. Add environment variable:
   - Key: `DISCORD_TOKEN`
   - Value: `your_bot_token_here`
4. Deploy the bot

#### 3. Discord Server Setup

1. Invite the bot to your Discord server with the following permissions:
   - View Channels
   - Send Messages
   - Manage Roles
   - View Voice Channels
   - Connect to Voice Channels
   - Read Message History

2. Ensure the bot's role is positioned above the progressive roles in the role hierarchy

3. Configure voice channels in `main.py`:
   ```python
   VALID_VOICE_CHANNELS = [
       "your-voice-channel-1",
       "your-voice-channel-2"
   ]
   ```

---

<a name="español"></a>
## Español

Un bot de Discord con sistema de roles progresivos y seguimiento de tiempo acumulativo para monitorear canales de voz de PUBG. Asigna roles automáticamente basado en el tiempo acumulado en canales de voz a través de múltiples sesiones.

### 🎯 Características

- **Monitoreo de Canales de Voz**: Rastrea la actividad del usuario en canales de voz específicos de PUBG
- **Sistema de Roles Progresivos**: Asigna roles automáticamente basado en el tiempo de conexión acumulativo
- **Seguimiento de Tiempo Acumulativo**: Guarda y acumula tiempo a través de reinicios y sesiones del bot
- **Persistencia de Datos**: El progreso del usuario se guarda en SQLite y persiste entre sesiones
- **Comandos de Administrador**: Estadísticas, configuración y comandos de gestión
- **Comandos de Usuario**: Verificar tiempo personal y reiniciar progreso
- **Disponibilidad 24/7**: Desplegado en Bot-Hosting.net para operación continua

### 🎖️ Sistema de Roles Progresivos

| Rol | Tiempo Requerido | Descripción |
|-----|------------------|--------------|
| Murci-Casual 🍼 | 30 minutos | El novato que acaba de entrar, todavía se estrella contra las paredes como un murciélago con GPS roto. |
| Ala Chueca 🦇 | 2 horas | Ya sabe moverse, pero aún vuela torcido y comete fallos en PUBG. |
| Murci-Veterano 🦇💪 | 8 horas | El veterano que ya domina el vuelo nocturno y reparte headshots como caramelos. |
| Bat-Commander 🦇⚡ | 20 horas | El murciélago maestro, líder supremo de BatCompany, el que reparte headshots en la oscuridad. |

### 🤖 Comandos (con `/`)

#### Para todos
- `/tiempo [usuario]` - Tiempo acumulado en voz, sesión actual y próximo rol
- `/ranking [periodo]` - Top 10 por tiempo en voz: histórico, últimos 7 días o últimos 30 días

#### Para administradores
- `/canal` - Elegí el canal de juegos gratis, novedades de PUBG y avisos de roles
- `/estadisticas` - Estadísticas del bot y de la voz
- `/configuracion` - Canales monitoreados y tiempos de cada rol
- `/resettiempo @usuario` - Resetea el tiempo de un usuario
- `/historial [cantidad]` - Actividad reciente

### 🎁 Juegos gratis y novedades de PUBG

Cada 30 minutos el bot publica los juegos gratis nuevos (Epic Games, Steam, GOG) y los anuncios oficiales de PUBG desde Steam. Los canales se eligen con `/canal`.

### 💾 Datos

El tiempo se guarda en SQLite (`batbot.db`, ruta configurable con `DB_PATH`) y se registra cada 2 minutos, así que si el bot se cae casi no se pierde nada. Apuntá `DB_PATH` a un disco persistente del hosting. Si existe un `user_progress.json` viejo, se importa solo la primera vez.

### 🔊 Canales de Voz Monitoreados

El bot actualmente monitorea los siguientes canales de voz:

- 🍗PUBG TTPP CANAL #1
- 🍗PUBG TTPP CANAL #2
- 🍗PUBG TTPP CANAL #3
- 🍗PUBG TTPP CANAL #4
- 🍗PUBG TTPP CANAL #5
- 🛡️[BAT-COMPANY] CLAN #1

### 🚀 Instrucciones de Configuración

#### 1. Configuración del Bot de Discord

1. Ve al [Portal de Desarrolladores de Discord](https://discord.com/developers/applications)
2. Crea una nueva aplicación y bot
3. Copia el token del bot
4. Habilita los siguientes intents:
   - Server Members Intent
   - Message Content Intent
   - Presence Intent

#### 2. Despliegue en Bot-Hosting.net

1. Crea una cuenta en [Bot-Hosting.net](https://bot-hosting.net)
2. Conecta tu repositorio de GitHub
3. Añade la variable de entorno:
   - Clave: `DISCORD_TOKEN`
   - Valor: `tu_token_del_bot_aquí`
4. Despliega el bot

#### 3. Configuración del Servidor de Discord

1. Invita al bot a tu servidor de Discord con los siguientes permisos:
   - Ver Canales
   - Enviar Mensajes
   - Gestionar Roles
   - Ver Canales de Voz
   - Conectarse a Canales de Voz
   - Leer Historial de Mensajes

2. Asegúrate de que el rol del bot esté posicionado por encima de los roles progresivos en la jerarquía de roles

### 🔧 Solución de Problemas

- **Error 403 Forbidden**: Verifica que el bot tenga los permisos correctos en el servidor
- **Bot no responde**: Asegúrate de que el token sea válido y que los intents estén habilitados
- **Roles no se asignan**: Verifica la jerarquía de roles en tu servidor
- **Tiempo no se acumula**: Confirma que los IDs de los canales de voz sean correctos
