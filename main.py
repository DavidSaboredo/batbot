import discord
from discord.ext import commands
import asyncio
from datetime import datetime
import os
import json
from dotenv import load_dotenv

# Cargar variables del archivo .env
load_dotenv()

# Discord bot configuration
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Voice channel configuration
VALID_VOICE_CHANNELS = [
    1405053196443062336,  # BATCAVE
    1405377739829022720,  # 🛡️[BAT-COMPANY] CLAN #1
    380104919124017155,   # 🍗PUBG TPP CHANNEL #1
    1405377302430220350,  # 🍗PUBG TPP CHANNEL #2
    1405423954474172498,  # 🍗PUBG FPP CHANNEL #1
    1405424126876975227,  # 🍗PUBG FPP CHANNEL #2
    1418642134155923546,  # 🍗PUBG TTPP CANAL #3
    1418642218247393370,  # 🍗PUBG TTPP CANAL #4
    1418722685113995315,  # 🍗PUBG TTPP CANAL #5
]

# Progressive role system
ROLE_SYSTEM = [
    {
        "name": "Murci-Casual 🍼",
        "time_seconds": 1800,  # 30 minutes
        "description": "El novato que recién entra, todavía se choca contra las paredes como un murciélago con GPS roto.",
        "color": discord.Color.light_grey()
    },
    {
        "name": "Ala Chueca 🦇",
        "time_seconds": 7200,  # 2 hours
        "description": "Ya sabe moverse, pero todavía vuela torcido y se manda sus fails en PUBG.",
        "color": discord.Color.orange()
    },
    {
        "name": "Murci-Veterano 🦇💪",
        "time_seconds": 18000,  # 5 hours
        "description": "El veterano que ya domina el vuelo nocturno y reparte headshots como caramelos.",
        "color": discord.Color.blue()
    },
    {
        "name": "Bat-Commander 🦇⚡",
        "time_seconds": 36000,  # 10 hours
        "description": "El maestro murciélago, líder supremo de la BatCompany, el que reparte headshots en la oscuridad.",
        "color": discord.Color.purple()
    }
]

# Global variables
user_join_times = {}
user_accumulated_time = {}  # Nuevo: tiempo acumulado por usuario
activity_history = []
MAX_HISTORY_SIZE = 50

# Funciones para persistencia de datos
def load_user_progress():
    global user_accumulated_time
    if os.path.exists('user_progress.json'):
        try:
            with open('user_progress.json', 'r') as f:
                data = json.load(f)
                user_accumulated_time = {int(k): v for k, v in data.items()}
            print(f"📊 Cargados datos de {len(user_accumulated_time)} usuarios")
        except Exception as e:
            print(f"Error cargando progreso de usuarios: {e}")
            user_accumulated_time = {}
    else:
        user_accumulated_time = {}
        print("📊 Archivo de progreso no encontrado, iniciando desde cero")

def save_user_progress():
    try:
        data = {str(k): v for k, v in user_accumulated_time.items()}
        with open('user_progress.json', 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error guardando progreso de usuarios: {e}")

def add_activity_log(event_type, username, channel_name, details=""):
    """Add activity to history log"""
    activity_history.append({
        "timestamp": datetime.now(),
        "type": event_type,
        "user": username,
        "channel": channel_name,
        "details": details
    })
    
    if len(activity_history) > MAX_HISTORY_SIZE:
        activity_history.pop(0)

bot_stats = {
    "start_time": datetime.now(),
    "roles_assigned": 0,
    "total_sessions": 0,
    "guilds_count": 0
}

async def scan_existing_users():
    """Scan existing users in voice channels and start tracking them"""
    print("🔍 Scanning existing users in voice channels...")
    
    for guild in bot.guilds:
        bot_stats["guilds_count"] = len(bot.guilds)
        
        for channel_id in VALID_VOICE_CHANNELS:
            channel = guild.get_channel(channel_id)
            if channel and isinstance(channel, discord.VoiceChannel):
                for member in channel.members:
                    if not member.bot:
                        user_join_times[member.id] = datetime.now()
                        add_activity_log(
                            "SCAN_FOUND", 
                            member.display_name, 
                            channel.name,
                            "Found in voice channel during startup scan"
                        )
                        print(f"📍 Found {member.display_name} in {channel.name}")
    
    print(f"✅ Scan complete. Tracking {len(user_join_times)} users.")

@bot.event
async def on_ready():
    print(f'🦇 {bot.user} has landed in the Batcave!')
    print(f'🏰 Connected to {len(bot.guilds)} server(s)')
    
    # Cargar progreso guardado
    load_user_progress()
    
    for guild in bot.guilds:
        print(f'   - {guild.name} (ID: {guild.id})')
    
    print(f'🎯 Monitoring {len(VALID_VOICE_CHANNELS)} voice channels')
    print(f'🏆 {len(ROLE_SYSTEM)} progressive roles configured')
    
    await scan_existing_users()
    
    activity = discord.Activity(
        type=discord.ActivityType.watching,
        name="the Batcave 🦇"
    )
    await bot.change_presence(activity=activity)
    
    print("🚀 BatCompany Bot is ready for action!")

@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return
    
    # Usuario se unió a un canal de voz válido
    if after.channel and after.channel.id in VALID_VOICE_CHANNELS:
        if member.id not in user_join_times:
            user_join_times[member.id] = datetime.now()
            add_activity_log("JOIN", member.display_name, after.channel.name)
            print(f"🎤 {member.display_name} joined {after.channel.name}")
    
    # Usuario salió de un canal de voz válido
    elif before.channel and before.channel.id in VALID_VOICE_CHANNELS:
        if member.id in user_join_times:
            join_time = user_join_times[member.id]
            connection_duration = (datetime.now() - join_time).total_seconds()
            
            # Agregar tiempo a acumulado
            if member.id not in user_accumulated_time:
                user_accumulated_time[member.id] = 0
            
            user_accumulated_time[member.id] += connection_duration
            save_user_progress()  # Guardar progreso
            
            # Verificar rol con tiempo total acumulado
            total_time = user_accumulated_time[member.id]
            await check_and_assign_role(member, total_time)
            
            add_activity_log(
                "LEAVE", 
                member.display_name, 
                before.channel.name,
                f"Sesión: {int(connection_duration//60)}m, Total: {int(total_time//60)}m"
            )
            
            del user_join_times[member.id]
            bot_stats["total_sessions"] += 1
            
            print(f"👋 {member.display_name} left {before.channel.name}. Total acumulado: {int(total_time//60)} minutos")
    
    # Usuario cambió de canal (salió de uno válido y entró a otro válido)
    elif (before.channel and before.channel.id in VALID_VOICE_CHANNELS and 
          after.channel and after.channel.id in VALID_VOICE_CHANNELS):
        if member.id in user_join_times:
            join_time = user_join_times[member.id]
            connection_duration = (datetime.now() - join_time).total_seconds()
            
            # Agregar tiempo del canal anterior
            if member.id not in user_accumulated_time:
                user_accumulated_time[member.id] = 0
            
            user_accumulated_time[member.id] += connection_duration
            save_user_progress()
            
            # Verificar rol con tiempo acumulado
            total_time = user_accumulated_time[member.id]
            await check_and_assign_role(member, total_time)
        
        # Registrar nuevo tiempo de entrada
        user_join_times[member.id] = datetime.now()
        print(f"🔄 {member.display_name} cambió de {before.channel.name} a {after.channel.name}")

async def check_and_assign_role(member, total_seconds):
    """Check if user qualifies for a role upgrade based on accumulated time"""
    for role_config in reversed(ROLE_SYSTEM):
        if total_seconds >= role_config["time_seconds"]:
            await assign_progressive_role(member, role_config, total_seconds)
            break

async def assign_progressive_role(member, role_config, total_seconds):
    """Assign progressive role to member"""
    try:
        guild = member.guild
        role_name = role_config["name"]
        
        # Find or create the role
        role = discord.utils.get(guild.roles, name=role_name)
        if not role:
            role = await guild.create_role(
                name=role_name,
                color=role_config["color"],
                reason="BatCompany progressive role system"
            )
            print(f"🎭 Created new role: {role_name}")
        
        # Check if user already has this role or higher
        current_level = get_user_role_level(member)
        new_level = get_role_level(role_name)
        
        if current_level >= new_level:
            return
        
        # Remove previous BatCompany roles
        await remove_previous_roles(member)
        
        # Assign new role
        await member.add_roles(role, reason=f"Earned after {int(total_seconds//60)} total minutes in voice")
        
        bot_stats["roles_assigned"] += 1
        
        add_activity_log(
            "ROLE_ASSIGNED", 
            member.display_name, 
            "System",
            f"Earned {role_name} after {int(total_seconds//60)} total minutes"
        )
        
        print(f"🏆 {member.display_name} earned role: {role_name} (Total: {int(total_seconds//60)} min)")
        
        # Enviar notificación al canal
        embed = discord.Embed(
            title="🎉 ¡Nuevo Rol Desbloqueado!",
            description=f"{member.mention} ha ganado el rol **{role_name}**!",
            color=role_config["color"]
        )
        embed.add_field(
            name="Tiempo Total Acumulado", 
            value=f"{int(total_seconds//3600)}h {int((total_seconds%3600)//60)}m", 
            inline=True
        )
        embed.add_field(
            name="Descripción", 
            value=role_config["description"], 
            inline=False
        )
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        
        # Enviar a canal general
        channel = discord.utils.get(guild.text_channels, name="general")
        if not channel:
            channel = guild.text_channels[0] if guild.text_channels else None
        
        if channel:
            await channel.send(embed=embed)
        
    except Exception as e:
        print(f"❌ Error assigning role to {member.display_name}: {e}")

def get_role_level(role_name):
    """Get the level of a role (higher number = higher rank)"""
    for i, role_config in enumerate(ROLE_SYSTEM):
        if role_config["name"] == role_name:
            return i
    return -1

def get_user_role_level(member):
    """Get the highest BatCompany role level of a user"""
    max_level = -1
    for role in member.roles:
        level = get_role_level(role.name)
        if level > max_level:
            max_level = level
    return max_level

async def remove_previous_roles(member):
    """Remove all BatCompany roles from member"""
    roles_to_remove = []
    for role in member.roles:
        if any(role.name == role_config["name"] for role_config in ROLE_SYSTEM):
            roles_to_remove.append(role)
    
    if roles_to_remove:
        await member.remove_roles(*roles_to_remove, reason="BatCompany role upgrade")

# Comando para que los usuarios vean su tiempo
@bot.command(name='mytime')
async def my_time(ctx):
    """Mostrar tiempo acumulado del usuario"""
    user_id = ctx.author.id
    
    # Obtener tiempo acumulado
    accumulated_seconds = user_accumulated_time.get(user_id, 0)
    
    # Si está actualmente en un canal, agregar tiempo de sesión actual
    current_session_seconds = 0
    if user_id in user_join_times:
        current_session = datetime.now() - user_join_times[user_id]
        current_session_seconds = current_session.total_seconds()
    
    total_seconds = accumulated_seconds + current_session_seconds
    total_minutes = total_seconds / 60
    hours = int(total_minutes // 60)
    minutes = int(total_minutes % 60)
    
    embed = discord.Embed(
        title="⏰ Tu Tiempo en Canales de Voz",
        color=discord.Color.blue()
    )
    
    if hours > 0:
        time_str = f"{hours}h {minutes}m"
    else:
        time_str = f"{minutes}m"
    
    embed.add_field(name="Tiempo Total Acumulado", value=time_str, inline=True)
    
    if current_session_seconds > 0:
        session_minutes = int(current_session_seconds / 60)
        embed.add_field(name="Sesión Actual", value=f"{session_minutes}m", inline=True)
    
    # Mostrar próximo rol
    current_level = get_user_role_level(ctx.author)
    if current_level + 1 < len(ROLE_SYSTEM):
        next_role = ROLE_SYSTEM[current_level + 1]
        time_needed = next_role["time_seconds"] - total_seconds
        if time_needed > 0:
            needed_minutes = int(time_needed / 60)
            embed.add_field(
                name="Próximo Rol", 
                value=f"{next_role['name']} (faltan {needed_minutes}m)", 
                inline=False
            )
    
    embed.set_thumbnail(url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
    
    await ctx.send(embed=embed)

# Comando para administradores para resetear tiempo de usuario
@bot.command(name='resettime')
@commands.has_permissions(administrator=True)
async def reset_time(ctx, member: discord.Member):
    """Resetear tiempo acumulado de un usuario (Solo administradores)"""
    user_id = member.id
    
    if user_id in user_accumulated_time:
        old_time = user_accumulated_time[user_id] / 60  # en minutos
        user_accumulated_time[user_id] = 0
        save_user_progress()
        
        embed = discord.Embed(
            title="🔄 Tiempo Reseteado",
            description=f"El tiempo de {member.mention} ha sido reseteado.",
            color=discord.Color.orange()
        )
        embed.add_field(name="Tiempo Anterior", value=f"{old_time:.1f} minutos", inline=True)
        embed.add_field(name="Tiempo Actual", value="0 minutos", inline=True)
        
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"{member.mention} no tiene tiempo registrado.")

@reset_time.error
async def reset_time_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ No tienes permisos de administrador para usar este comando.")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("❌ Usuario no encontrado.")

# Bot Commands (comandos administrativos existentes)
@bot.command(name='voice_stats')
@commands.has_permissions(administrator=True)
async def voice_stats(ctx):
    """Show voice channel statistics"""
    embed = discord.Embed(
        title="🦇 BatCompany Voice Statistics",
        color=discord.Color.dark_purple(),
        timestamp=datetime.now()
    )
    
    # Current users in voice
    current_users = len(user_join_times)
    embed.add_field(name="👥 Users Currently in Voice", value=current_users, inline=True)
    embed.add_field(name="🏆 Total Roles Assigned", value=bot_stats["roles_assigned"], inline=True)
    embed.add_field(name="📊 Total Sessions", value=bot_stats["total_sessions"], inline=True)
    embed.add_field(name="💾 Users with Saved Progress", value=len(user_accumulated_time), inline=True)
    
    # Uptime
    uptime = datetime.now() - bot_stats["start_time"]
    hours = int(uptime.total_seconds() // 3600)
    minutes = int((uptime.total_seconds() % 3600) // 60)
    embed.add_field(name="⏰ Bot Uptime", value=f"{hours}h {minutes}m", inline=True)
    
    await ctx.send(embed=embed)

@bot.command(name='config')
@commands.has_permissions(administrator=True)
async def show_config(ctx):
    """Show bot configuration"""
    embed = discord.Embed(
        title="🦇 BatCompany Configuration",
        color=discord.Color.gold(),
        timestamp=datetime.now()
    )
    
    # Voice channels
    channel_list = []
    for channel_id in VALID_VOICE_CHANNELS:
        channel = ctx.guild.get_channel(channel_id)
        if channel:
            channel_list.append(f"• {channel.name}")
        else:
            channel_list.append(f"• Channel ID: {channel_id} (Not found)")
    
    embed.add_field(
        name="🎤 Monitored Voice Channels",
        value="\n".join(channel_list) if channel_list else "None configured",
        inline=False
    )
    
    # Role system
    role_list = []
    for role_config in ROLE_SYSTEM:
        time_str = f"{role_config['time_seconds']//60} min"
        role_list.append(f"• {role_config['name']} - {time_str}")
    
    embed.add_field(
        name="🏆 Progressive Role System",
        value="\n".join(role_list),
        inline=False
    )
    
    await ctx.send(embed=embed)

@bot.command(name='roletest')
@commands.has_permissions(administrator=True)
async def role_test(ctx, time_minutes: int = None):
    """Test role assignment (Admin only)"""
    if time_minutes is None:
        await ctx.send("❌ Please specify time in minutes: `!roletest 30`")
        return
    
    time_seconds = time_minutes * 60
    await check_and_assign_role(ctx.author, time_seconds)
    await ctx.send(f"✅ Tested role assignment for {time_minutes} minutes of voice time")

@bot.command(name='scan')
@commands.has_permissions(administrator=True)
async def manual_scan(ctx):
    """Manually scan voice channels for existing users"""
    await scan_existing_users()
    await ctx.send("✅ Manual scan completed")

@bot.command(name='history')
@commands.has_permissions(administrator=True)
async def show_activity_history(ctx, limit: int = 10):
    """Show recent activity history"""
    if not activity_history:
        await ctx.send("📝 No activity history available")
        return
    
    limit = min(limit, 20)  # Max 20 entries
    recent_activities = activity_history[-limit:]
    
    embed = discord.Embed(
        title="📋 Recent Activity History",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    
    activity_text = []
    for activity in reversed(recent_activities):
        time_str = activity["timestamp"].strftime("%H:%M:%S")
        icon = {
            "JOIN": "🎤",
            "LEAVE": "👋",
            "ROLE_ASSIGNED": "🏆",
            "SCAN_FOUND": "🔍"
        }.get(activity["type"], "📝")
        
        activity_line = f"{icon} `{time_str}` **{activity['user']}** - {activity['channel']}"
        if activity["details"]:
            activity_line += f" ({activity['details']})"
        
        activity_text.append(activity_line)
    
    embed.description = "\n".join(activity_text)
    await ctx.send(embed=embed)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don't have permission to use this command.")
    elif isinstance(error, commands.CommandNotFound):
        pass  # Ignore unknown commands
    else:
        print(f"Command error: {error}")
        await ctx.send("❌ An error occurred while executing the command.")

if __name__ == '__main__':
    print("🦇 Starting BatCompany Discord Bot...")
    
    if not TOKEN:
        print("❌ ERROR: DISCORD_TOKEN not found in environment variables!")
        print("\n📋 Setup Instructions for Bot-Hosting.net:")
        print("   1. Create .env file with DISCORD_TOKEN=your_token_here")
        print("   2. Or configure environment variable in hosting panel")
        print("\n🔗 Get your token at: https://discord.com/developers/applications")
        exit(1)
    
    print("✅ Discord token loaded from environment variables")
    try:
        print("🚀 Starting bot...")
        bot.run(TOKEN)
    except discord.LoginFailure:
        print("❌ Invalid Discord token! Please check your DISCORD_TOKEN variable.")
        exit(1)
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        exit(1)
