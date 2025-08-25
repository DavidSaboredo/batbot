import discord
from discord.ext import commands
import asyncio
from datetime import datetime
import os
from flask import Flask, render_template, jsonify
from threading import Thread

# Discord bot configuration
intents = discord.Intents.default()
intents.voice_states = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Voice channel configuration - UPDATE THESE WITH ACTUAL CHANNEL IDs
# To find channel IDs: Right-click on voice channel in Discord > Copy ID (Developer Mode must be enabled)
VALID_VOICE_CHANNELS = [
    123456789012345678,  # 🍗PUBG FPP CANAL #1
    123456789012345679,  # 🍗PUBG FPP CANAL #2  
    123456789012345680,  # 🍗PUBG TPP CANAL #1
    123456789012345681,  # 🍗PUBG TPP CANAL #2
]

# Progressive role system based on voice connection time
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
        "name": "Eco-Legend 📡",
        "time_seconds": 18000,  # 5 hours
        "description": "Usa el eco como radar, empieza a carrear y sobrevivir más que el resto.",
        "color": discord.Color.blue()
    },
    {
        "name": "Dark Commander 🎖️",
        "time_seconds": 36000,  # 10 hours
        "description": "El maestro murciélago, líder supremo de la BatCompany, el que reparte headshots en la oscuridad.",
        "color": discord.Color.purple()
    }
]

# User session tracking
# Structure: {user_id: datetime_object}
user_join_times = {}

# Bot statistics
bot_stats = {
    "start_time": datetime.now(),
    "roles_assigned": 0,
    "total_sessions": 0,
    "guilds_count": 0
}

# ===== FLASK WEB SERVER FOR REPLIT KEEPALIVE =====
app = Flask(__name__)

@app.route('/')
def home():
    """Main dashboard showing bot status"""
    uptime = datetime.now() - bot_stats["start_time"]
    uptime_str = f"{uptime.days}d {uptime.seconds//3600}h {(uptime.seconds//60)%60}m"
    
    return render_template('index.html', 
                         bot_user=bot.user.name if bot.user else "Not connected",
                         uptime=uptime_str,
                         stats=bot_stats,
                         users_connected=len(user_join_times),
                         monitored_channels=len(VALID_VOICE_CHANNELS),
                         role_system=ROLE_SYSTEM)

@app.route('/api/status')
def api_status():
    """API endpoint for bot status"""
    uptime = datetime.now() - bot_stats["start_time"]
    
    return jsonify({
        "bot_status": "online" if bot.is_ready() else "offline",
        "bot_user": bot.user.name if bot.user else None,
        "uptime_seconds": uptime.total_seconds(),
        "users_connected": len(user_join_times),
        "monitored_channels": len(VALID_VOICE_CHANNELS),
        "roles_system": len(ROLE_SYSTEM),
        "stats": bot_stats,
        "current_sessions": [
            {
                "user_id": user_id,
                "duration_seconds": (datetime.now() - join_time).total_seconds()
            }
            for user_id, join_time in user_join_times.items()
        ]
    })

def run_flask():
    """Run Flask server for Replit keepalive"""
    app.run(host='0.0.0.0', port=5000, debug=False)

def keep_alive():
    """Maintains bot active on Replit using Flask server"""
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    print("🌐 Flask server started on port 5000 for Replit keepalive")

# ===== DISCORD BOT EVENTS =====

@bot.event
async def on_ready():
    """Event triggered when bot is ready and connected"""
    print(f'✅ {bot.user} has logged in and is ready!')
    print(f'📊 Connected to {len(bot.guilds)} server(s)')
    print(f'🎤 Monitoring {len(VALID_VOICE_CHANNELS)} voice channel(s)')
    
    # Update bot stats
    bot_stats["guilds_count"] = len(bot.guilds)
    
    # Display role system configuration
    print('\n=== 🎖️ PROGRESSIVE ROLE SYSTEM ===')
    for i, role in enumerate(ROLE_SYSTEM, 1):
        minutes = role["time_seconds"] / 60
        hours = minutes / 60
        time_str = f"{hours:.1f}h" if hours >= 1 else f"{minutes:.0f}min"
        print(f'{i}. {role["name"]} - {time_str}')
        print(f'   → {role["description"]}')
    print('=' * 50)
    
    # Warn if no channels configured
    if not VALID_VOICE_CHANNELS:
        print("⚠️  WARNING: No voice channels configured! Update VALID_VOICE_CHANNELS with actual channel IDs.")

@bot.event
async def on_voice_state_update(member, before, after):
    """Event triggered when user's voice state changes"""
    
    # User joined a monitored voice channel
    if after.channel and after.channel.id in VALID_VOICE_CHANNELS:
        if member.id not in user_join_times:
            user_join_times[member.id] = datetime.now()
            bot_stats["total_sessions"] += 1
            print(f'🎤 {member.display_name} joined {after.channel.name} at {user_join_times[member.id].strftime("%H:%M:%S")}')
    
    # User left a monitored voice channel
    if before.channel and before.channel.id in VALID_VOICE_CHANNELS:
        if member.id in user_join_times:
            # Calculate connection duration
            join_time = user_join_times[member.id]
            leave_time = datetime.now()
            connection_duration = (leave_time - join_time).total_seconds()
            
            minutes = connection_duration / 60
            print(f'🚪 {member.display_name} left {before.channel.name} after {minutes:.1f} minutes')
            
            # Check and assign appropriate role
            await check_and_assign_role(member, connection_duration)
            
            # Remove from tracking
            del user_join_times[member.id]
    
    # User moved between monitored channels (keep original join time)
    if (before.channel and before.channel.id in VALID_VOICE_CHANNELS and 
        after.channel and after.channel.id in VALID_VOICE_CHANNELS and 
        before.channel.id != after.channel.id):
        print(f'🔄 {member.display_name} moved from {before.channel.name} to {after.channel.name}')

async def check_and_assign_role(member, connection_duration):
    """Determines and assigns appropriate role based on connection time"""
    # Find the highest eligible role
    eligible_role = None
    for role_config in reversed(ROLE_SYSTEM):  # Start with highest role
        if connection_duration >= role_config["time_seconds"]:
            eligible_role = role_config
            break
    
    if eligible_role:
        await assign_progressive_role(member, eligible_role, connection_duration)
    else:
        min_time = ROLE_SYSTEM[0]["time_seconds"]
        min_minutes = min_time / 60
        current_minutes = connection_duration / 60
        print(f'⏱️  {member.display_name} needs {min_minutes:.0f} minutes for first role (current: {current_minutes:.1f}min)')

async def assign_progressive_role(member, role_config, connection_duration):
    """Assigns progressive role to user"""
    try:
        role_name = role_config["name"]
        
        # Find or create the role
        role = discord.utils.get(member.guild.roles, name=role_name)
        
        if not role:
            print(f'🔨 Creating role "{role_name}"...')
            role = await member.guild.create_role(
                name=role_name,
                color=role_config["color"],
                reason="Auto-created by BatCompany progressive role system"
            )
            print(f'✅ Role "{role_name}" created successfully')
        
        # Check if user already has this role or higher
        current_level = get_user_role_level(member)
        new_level = get_role_level(role_name)
        
        if current_level >= new_level:
            print(f'📋 {member.display_name} already has "{role_name}" or higher')
            return
        
        # Remove previous progressive roles
        await remove_previous_roles(member)
        
        # Assign new role
        await member.add_roles(role, reason=f'Progressive role: {connection_duration:.0f}s voice time')
        
        bot_stats["roles_assigned"] += 1
        minutes = connection_duration / 60
        print(f'🎖️  ROLE ASSIGNED: "{role_name}" to {member.display_name} ({minutes:.1f} minutes)')
        print(f'   → {role_config["description"]}')
        
    except discord.Forbidden:
        print(f'❌ Missing permissions to assign roles to {member.display_name}')
    except discord.HTTPException as e:
        print(f'❌ HTTP error assigning role to {member.display_name}: {e}')
    except Exception as e:
        print(f'❌ Unexpected error assigning role to {member.display_name}: {e}')

def get_role_level(role_name):
    """Gets role level in progressive system"""
    for i, role_config in enumerate(ROLE_SYSTEM):
        if role_config["name"] == role_name:
            return i
    return -1

def get_user_role_level(member):
    """Gets user's highest progressive role level"""
    max_level = -1
    for role in member.roles:
        level = get_role_level(role.name)
        if level > max_level:
            max_level = level
    return max_level

async def remove_previous_roles(member):
    """Removes previous progressive roles from user"""
    roles_to_remove = []
    for role in member.roles:
        if any(role.name == role_config["name"] for role_config in ROLE_SYSTEM):
            roles_to_remove.append(role)
    
    if roles_to_remove:
        await member.remove_roles(*roles_to_remove, reason="Progressive role update")
        removed_names = [r.name for r in roles_to_remove]
        print(f'🗑️  Removed old roles from {member.display_name}: {", ".join(removed_names)}')

# ===== BOT COMMANDS =====

@bot.command(name='voice_stats')
@commands.has_permissions(administrator=True)
async def voice_stats(ctx):
    """Shows current voice channel statistics (Admin only)"""
    if not user_join_times:
        await ctx.send('📊 No users currently in monitored voice channels.')
        return
    
    embed = discord.Embed(
        title="🎤 Voice Channel Statistics",
        description="Users currently in monitored PUBG channels:",
        color=discord.Color.blue()
    )
    
    current_time = datetime.now()
    
    for user_id, join_time in user_join_times.items():
        user = bot.get_user(user_id)
        if user:
            duration = (current_time - join_time).total_seconds()
            minutes = duration / 60
            embed.add_field(
                name=user.display_name,
                value=f"{minutes:.1f} minutes",
                inline=True
            )
    
    await ctx.send(embed=embed)

@bot.command(name='config')
@commands.has_permissions(administrator=True)
async def show_config(ctx):
    """Shows bot configuration (Admin only)"""
    embed = discord.Embed(
        title="🦇 BatCompany Bot Configuration",
        color=discord.Color.purple()
    )
    
    # Monitored channels
    if VALID_VOICE_CHANNELS:
        channels_info = []
        for channel_id in VALID_VOICE_CHANNELS:
            channel = bot.get_channel(channel_id)
            if channel:
                channels_info.append(f"• {channel.name} (ID: {channel_id})")
            else:
                channels_info.append(f"• Unknown Channel (ID: {channel_id})")
        embed.add_field(
            name="🎤 Monitored PUBG Channels",
            value="\n".join(channels_info) if channels_info else "None configured",
            inline=False
        )
    else:
        embed.add_field(
            name="🎤 Monitored PUBG Channels",
            value="⚠️ No channels configured",
            inline=False
        )
    
    # Role system
    roles_info = []
    for role in ROLE_SYSTEM:
        minutes = role["time_seconds"] / 60
        hours = minutes / 60
        time_str = f"{hours:.1f}h" if hours >= 1 else f"{minutes:.0f}min"
        roles_info.append(f"• **{role['name']}** - {time_str}")
    
    embed.add_field(
        name="🎖️ Progressive Role System",
        value="\n".join(roles_info),
        inline=False
    )
    
    # Current stats
    embed.add_field(
        name="📊 Current Stats",
        value=f"Users connected: {len(user_join_times)}\nTotal sessions: {bot_stats['total_sessions']}\nRoles assigned: {bot_stats['roles_assigned']}",
        inline=True
    )
    
    await ctx.send(embed=embed)

@bot.command(name='roletest')
@commands.has_permissions(administrator=True)
async def role_test(ctx, time_minutes: int = None):
    """Test role assignment with custom time (Admin only)"""
    if time_minutes is None:
        await ctx.send("Usage: !roletest <minutes>\nExample: !roletest 60")
        return
    
    time_seconds = time_minutes * 60
    await check_and_assign_role(ctx.author, time_seconds)
    await ctx.send(f"✅ Role test completed for {time_minutes} minutes ({time_seconds} seconds)")

# ===== ERROR HANDLING =====

@bot.event
async def on_command_error(ctx, error):
    """Handle bot command errors"""
    if isinstance(error, commands.MissingPermissions):
        await ctx.send('❌ You do not have permission to use this command.')
    elif isinstance(error, commands.CommandNotFound):
        pass  # Ignore unknown commands
    elif isinstance(error, commands.BadArgument):
        await ctx.send('❌ Invalid argument provided. Check command usage.')
    else:
        print(f'Command error: {error}')
        await ctx.send('❌ An error occurred while executing the command.')

@bot.event
async def on_error(event, *args, **kwargs):
    """Handle general bot errors"""
    print(f'Bot error in {event}: {args}')

# ===== MAIN EXECUTION =====

if __name__ == '__main__':
    print("🦇 Starting BatCompany Discord Bot...")
    print("\n📋 SETUP CHECKLIST:")
    print("1. ✅ Create Discord Application at https://discord.com/developers/applications")
    print("2. ✅ Copy bot token to Replit Secrets as 'DISCORD_TOKEN'")
    print("3. ✅ Enable Developer Mode in Discord and copy voice channel IDs")
    print("4. ✅ Update VALID_VOICE_CHANNELS in this file with actual IDs")
    print("5. ✅ Invite bot to server with 'Manage Roles' permission")
    print("6. ✅ Ensure bot role is above progressive roles in role hierarchy")
    print("\n🎖️ Progressive Role System:")
    for role in ROLE_SYSTEM:
        minutes = role['time_seconds'] / 60
        hours = minutes / 60
        time_str = f"{hours:.1f}h" if hours >= 1 else f"{minutes:.0f}min"
        print(f"   • {role['name']} - {time_str}")
    print("-" * 60)
    
    # Start Flask keepalive server
    keep_alive()
    
    # Get Discord token from environment
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("❌ ERROR: DISCORD_TOKEN not found in environment variables!")
        print("   Please add your Discord bot token to Replit Secrets:")
        print("   1. Go to Replit Secrets (lock icon)")
        print("   2. Add key: DISCORD_TOKEN")
        print("   3. Add value: your_bot_token_here")
        exit(1)
    
    print("✅ Discord token loaded from environment variables")
    print("🚀 Starting bot...")
    
    # Run the bot
    try:
        bot.run(token)
    except discord.LoginFailure:
        print("❌ Invalid Discord token! Please check your DISCORD_TOKEN in Replit Secrets.")
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
