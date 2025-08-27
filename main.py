import discord
from discord.ext import commands
import asyncio
from datetime import datetime
import os

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
activity_history = []
MAX_HISTORY_SIZE = 50

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
    
    # User joined a valid voice channel
    if after.channel and after.channel.id in VALID_VOICE_CHANNELS:
        if member.id not in user_join_times:
            user_join_times[member.id] = datetime.now()
            add_activity_log("JOIN", member.display_name, after.channel.name)
            print(f"🎤 {member.display_name} joined {after.channel.name}")
    
    # User left a valid voice channel
    elif before.channel and before.channel.id in VALID_VOICE_CHANNELS:
        if member.id in user_join_times:
            join_time = user_join_times[member.id]
            connection_duration = (datetime.now() - join_time).total_seconds()
            
            add_activity_log(
                "LEAVE", 
                member.display_name, 
                before.channel.name,
                f"Duration: {int(connection_duration//60)} minutes"
            )
            
            await check_and_assign_role(member, connection_duration)
            del user_join_times[member.id]
            bot_stats["total_sessions"] += 1
            
            print(f"👋 {member.display_name} left {before.channel.name} after {int(connection_duration//60)} minutes")

async def check_and_assign_role(member, connection_duration):
    """Check if user qualifies for a role upgrade"""
    for role_config in reversed(ROLE_SYSTEM):
        if connection_duration >= role_config["time_seconds"]:
            await assign_progressive_role(member, role_config, connection_duration)
            break

async def assign_progressive_role(member, role_config, connection_duration):
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
        await member.add_roles(role, reason=f"Earned after {int(connection_duration//60)} minutes in voice")
        
        bot_stats["roles_assigned"] += 1
        
        add_activity_log(
            "ROLE_ASSIGNED", 
            member.display_name, 
            "System",
            f"Earned {role_name} after {int(connection_duration//60)} minutes"
        )
        
        print(f"🏆 {member.display_name} earned role: {role_name}")
        
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

# Bot Commands
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
        print("\n📋 Setup Instructions for Railway:")
        print("   1. Go to Railway Dashboard")
        print("   2. Select your project")
        print("   3. Go to Variables tab")
        print("   4. Add new variable:")
        print("      - Key: DISCORD_TOKEN")
        print("      - Value: [Your actual Discord bot token]")
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
