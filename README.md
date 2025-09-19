# 🦇 BatCompany Discord Bot | Bot de Discord BatCompany

**English** | [Español](#español)

---

## English

A Discord bot with progressive role system and cumulative time tracking for PUBG voice channel monitoring. Automatically assigns roles based on accumulated time spent in voice channels across multiple sessions.

### 🎯 Features

- **Voice Channel Monitoring**: Tracks user activity in specified PUBG voice channels
- **Progressive Role System**: Automatically assigns roles based on cumulative connection time
- **Cumulative Time Tracking**: Saves and accumulates time across bot restarts and sessions
- **Data Persistence**: User progress is saved in JSON format and persists between sessions
- **Admin Commands**: Statistics, configuration, and management commands
- **User Commands**: Check personal time and reset progress
- **24/7 Uptime**: Deployed on Bot-Hosting.net for continuous operation

### 🎖️ Progressive Role System

| Role | Time Required | Description |
|------|---------------|--------------|
| Murci-Casual 🍼 | 30 minutes | The newbie who just entered, still crashes into walls like a bat with broken GPS. |
| Ala Chueca 🦇 | 2 hours | Already knows how to move, but still flies crooked and makes fails in PUBG. |
| Eco-Legend 📡 | 5 hours | Uses echo as radar, starts to carry and survive more than the rest. |
| Dark Commander 🎖️ | 10 hours | The master bat, supreme leader of BatCompany, the one who distributes headshots in the dark. |

### 🤖 Commands

#### User Commands
- `!mytime` - Check your accumulated voice channel time and current role
- `!resettime` - Reset your accumulated time (requires confirmation)

#### Admin Commands
- `!voice_stats` - Display voice channel statistics for all users
- `!config` - Show current bot configuration
- `!roletest @user` - Test role assignment for a specific user
- `!scan` - Scan and assign roles to all current voice channel users
- `!history @user` - Show activity history for a specific user

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
- **Persistencia de Datos**: El progreso del usuario se guarda en formato JSON y persiste entre sesiones
- **Comandos de Administrador**: Estadísticas, configuración y comandos de gestión
- **Comandos de Usuario**: Verificar tiempo personal y reiniciar progreso
- **Disponibilidad 24/7**: Desplegado en Bot-Hosting.net para operación continua

### 🎖️ Sistema de Roles Progresivos

| Rol | Tiempo Requerido | Descripción |
|-----|------------------|--------------|
| Murci-Casual 🍼 | 30 minutos | El novato que acaba de entrar, todavía se estrella contra las paredes como un murciélago con GPS roto. |
| Ala Chueca 🦇 | 2 horas | Ya sabe moverse, pero aún vuela torcido y comete fallos en PUBG. |
| Eco-Legend 📡 | 5 horas | Usa el eco como radar, comienza a cargar y sobrevivir más que el resto. |
| Dark Commander 🎖️ | 10 horas | El murciélago maestro, líder supremo de BatCompany, el que reparte headshots en la oscuridad. |

### 🤖 Comandos

#### Comandos de Usuario
- `!mytime` - Verifica tu tiempo acumulado en canales de voz y rol actual
- `!resettime` - Reinicia tu tiempo acumulado (requiere confirmación)

#### Comandos de Administrador
- `!voice_stats` - Muestra estadísticas de canales de voz para todos los usuarios
- `!config` - Muestra la configuración actual del bot
- `!roletest @usuario` - Prueba la asignación de roles para un usuario específico
- `!scan` - Escanea y asigna roles a todos los usuarios actuales en canales de voz
- `!history @usuario` - Muestra el historial de actividad para un usuario específico

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
