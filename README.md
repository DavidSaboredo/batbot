# 🦇 BatCompany Discord Bot

A Discord bot with progressive role system for PUBG voice channel monitoring. Automatically assigns roles based on time spent in voice channels.

## 🎯 Features

- **Voice Channel Monitoring**: Tracks user activity in specified PUBG voice channels
- **Progressive Role System**: Automatically assigns roles based on connection time
- **Admin Commands**: Statistics and configuration commands for server administrators
- **Web Dashboard**: Live status dashboard accessible via web browser
- **24/7 Uptime**: Flask keepalive server for Replit hosting

## 🎖️ Role System

| Role | Time Required | Description |
|------|---------------|-------------|
| Murci-Casual 🍼 | 30 minutes | El novato que recién entra, todavía se choca contra las paredes como un murciélago con GPS roto. |
| Ala Chueca 🦇 | 2 hours | Ya sabe moverse, pero todavía vuela torcido y se manda sus fails en PUBG. |
| Eco-Legend 📡 | 5 hours | Usa el eco como radar, empieza a carrear y sobrevivir más que el resto. |
| Dark Commander 🎖️ | 10 hours | El maestro murciélago, líder supremo de la BatCompany, el que reparte headshots en la oscuridad. |

## 🚀 Setup Instructions

### 1. Discord Bot Setup

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application and bot
3. Copy the bot token
4. Enable the following intents:
   - Server Members Intent
   - Message Content Intent (if using message commands)

### 2. Replit Configuration

1. Fork/import this project to Replit
2. Add your Discord bot token to Replit Secrets:
   - Key: `DISCORD_TOKEN`
   - Value: `your_bot_token_here`

### 3. Discord Server Setup

1. Invite the bot to your Discord server with the following permissions:
   - View Channels
   - Send Messages
   - Manage Roles
   - View Voice Channels
   - Connect to Voice Channels

2. Ensure the bot's role is positioned above the progressive roles in the role hierarchy

### 4. Voice Channel Configuration

1. Enable Developer Mode in Discord (User Settings > Advanced > Developer Mode)
2. Right-click on your PUBG voice channels and select "Copy ID"
3. Update the `VALID_VOICE_CHANNELS` list in `main.py`:

```python
VALID_VOICE_CHANNELS = [
    123456789012345678,  # 🍗PUBG FPP CANAL #1
    123456789012345679,  # 🍗PUBG FPP CANAL #2
    123456789012345680,  # 🍗PUBG TPP CANAL #1
    123456789012345681   # 🍗PUBG TPP CANAL #2
]
