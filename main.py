import discord
from discord import app_commands
from discord.ext import commands, tasks
import os
import re
import random
import json
import sqlite3
import time
import aiohttp
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

# Cargar variables del archivo .env
load_dotenv()

# Discord bot configuration
TOKEN = os.getenv("DISCORD_TOKEN")
# En el hosting, apuntar DB_PATH a un disco persistente (ej: /data/batbot.db)
DB_PATH = os.getenv("DB_PATH", "batbot.db")
LEGACY_JSON = "user_progress.json"

# Cada cuántos segundos se guarda el tiempo de quienes están en voz.
# Si el bot se cae, se pierde como máximo este intervalo.
CHECKPOINT_SECONDS = 120

# Cada cuántos minutos se buscan juegos gratis y novedades de PUBG
FEEDS_MINUTES = 30

# Canal de texto por defecto para juegos gratis y novedades (se puede cambiar con /canal)
DEFAULT_CHANNELS = {"juegos": 1404895214266482821, "pubg": 1404895214266482821, "resumen": 1404895214266482821, "comunidad": 1404895214266482821}

# Rol que se le da cada semana a quien más estuvo en voz
TOP_ROLE_NAME = "🔥 Más activo de la semana"

# Argentina no tiene horario de verano: UTC-3 todo el año
AR_TZ = timezone(timedelta(hours=-3))
# Los resúmenes y el respaldo salen los domingos / el día 1 a partir de esta hora (hora argentina)
REPORT_HOUR = 20
PUBG_STEAM_APPID = 578080
EPIC_FREE_URL = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions?locale=es-AR&country=AR&allowCountries=AR"
GAMERPOWER_URL = "https://www.gamerpower.com/api/giveaways?platform=pc&type=game"
PUBG_NEWS_URL = f"https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/?appid={PUBG_STEAM_APPID}&count=15&maxlength=500"
# Títulos de Steam que no interesan (transmisiones de torneos y listas de baneos)
PUBG_NEWS_SKIP = ("is live", "bans notice")

intents = discord.Intents.default()
intents.voice_states = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix=commands.when_mentioned, intents=intents)

# Voice channel configuration
VALID_VOICE_CHANNELS = [
    1539422445348462612,  # RECLUTANDO
    380104919124017155,   # 🍗 PUBG CANAL A
    1475163837941678293,  # 🍗 PUBG CANAL B
    1475163916807180349,  # 🍗 PUBG CANAL C
    1475164009979449495,  # 🍗 PUBG CANAL D
    1547695715239600260,  # 🍗 PUBG CANAL E
    1554292614428233838,  # STAR CITIZEN
    1563676251812790343,  # DOTA
    1517994898501013697,  # Aprendiendo
    1553963582885204018,  # NO MAN S SKY
    1557222871443578960,  # ARC RIDERS
    1497791695578726400,  # Multiples juegos
    1557444224671154367,  # Helldivers 2
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
        "time_seconds": 7200,  # 2 hours = 120 minutes
        "description": "Ya sabe moverse, pero todavía vuela torcido y se manda sus fails en PUBG.",
        "color": discord.Color.orange()
    },
    {
        "name": "Murci-Veterano 🦇💪",
        "time_seconds": 28800,  # 8 hours = 480 minutes
        "description": "El veterano que ya domina el vuelo nocturno y reparte headshots como caramelos.",
        "color": discord.Color.blue()
    },
    {
        "name": "Bat-Commander 🦇⚡",
        "time_seconds": 72000,  # 20 hours = 1200 minutes
        "description": "El maestro murciélago, líder supremo de la BatCompany, el que reparte headshots en la oscuridad.",
        "color": discord.Color.purple()
    }
]

# Quién está en voz ahora: user_id -> {"since": epoch, "guild": guild_id, "channel": nombre}
active_sessions = {}
activity_history = []
MAX_HISTORY_SIZE = 50

bot_stats = {
    "start_time": datetime.now(),
    "roles_assigned": 0,
    "total_sessions": 0,
}


# ---------- Base de datos ----------

def db_connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with db_connect() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, total_seconds REAL NOT NULL DEFAULT 0)")
        conn.execute("CREATE TABLE IF NOT EXISTS sessions (user_id INTEGER NOT NULL, ended_at REAL NOT NULL, seconds REAL NOT NULL)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_ended ON sessions (ended_at)")
        conn.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        conn.execute("CREATE TABLE IF NOT EXISTS seen (kind TEXT NOT NULL, item_id TEXT NOT NULL, PRIMARY KEY (kind, item_id))")
        conn.execute("CREATE TABLE IF NOT EXISTS streaks (user_id INTEGER PRIMARY KEY, last_day TEXT NOT NULL, current INTEGER NOT NULL, best INTEGER NOT NULL)")
        conn.execute("CREATE TABLE IF NOT EXISTS birthdays (user_id INTEGER PRIMARY KEY, day INTEGER NOT NULL, month INTEGER NOT NULL)")
    migrate_legacy_json()


def get_setting(key):
    with db_connect() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row[0] if row else None


def set_setting(key, value):
    with db_connect() as conn:
        conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, str(value)),
        )


def tracked_channels():
    """IDs de los canales de voz que cuentan tiempo. Se cambian con /canalvoz; si no hay nada guardado, usa la lista fija."""
    raw = get_setting("voice_channels")
    if raw:
        try:
            return [int(x) for x in json.loads(raw)]
        except (ValueError, TypeError):
            pass
    return list(VALID_VOICE_CHANNELS)


def save_tracked_channels(ids):
    set_setting("voice_channels", json.dumps(list(ids)))


def seen_any(kind):
    with db_connect() as conn:
        return conn.execute("SELECT 1 FROM seen WHERE kind = ? LIMIT 1", (kind,)).fetchone() is not None


def is_seen(kind, item_id):
    with db_connect() as conn:
        return conn.execute("SELECT 1 FROM seen WHERE kind = ? AND item_id = ?", (kind, item_id)).fetchone() is not None


def mark_seen(kind, item_id):
    with db_connect() as conn:
        conn.execute("INSERT OR IGNORE INTO seen (kind, item_id) VALUES (?, ?)", (kind, item_id))


def migrate_legacy_json():
    """Importa las horas del user_progress.json viejo la primera vez que se crea la base."""
    if not os.path.exists(LEGACY_JSON):
        return
    with db_connect() as conn:
        if conn.execute("SELECT 1 FROM users LIMIT 1").fetchone():
            return
        try:
            with open(LEGACY_JSON, "r") as f:
                data = json.load(f)
            conn.executemany(
                "INSERT INTO users (user_id, total_seconds) VALUES (?, ?)",
                [(int(k), float(v)) for k, v in data.items()],
            )
            print(f"📦 Migrados {len(data)} usuarios desde {LEGACY_JSON}")
        except Exception as e:
            print(f"Error migrando {LEGACY_JSON}: {e}")


def today_ar():
    return datetime.now(AR_TZ).date()


def update_streak(conn, user_id):
    """Cuenta días seguidos con tiempo en voz (día argentino)."""
    today = today_ar()
    row = conn.execute("SELECT last_day, current, best FROM streaks WHERE user_id = ?", (user_id,)).fetchone()
    if row is None:
        conn.execute("INSERT INTO streaks (user_id, last_day, current, best) VALUES (?, ?, 1, 1)", (user_id, today.isoformat()))
        return
    last = datetime.strptime(row["last_day"], "%Y-%m-%d").date()
    if last == today:
        return
    current = row["current"] + 1 if last == today - timedelta(days=1) else 1
    conn.execute(
        "UPDATE streaks SET last_day = ?, current = ?, best = ? WHERE user_id = ?",
        (today.isoformat(), current, max(current, row["best"]), user_id),
    )


def get_streak(user_id):
    """(racha actual, mejor racha). La actual vale 0 si ya pasó más de un día sin entrar."""
    with db_connect() as conn:
        row = conn.execute("SELECT last_day, current, best FROM streaks WHERE user_id = ?", (user_id,)).fetchone()
    if row is None:
        return 0, 0
    last = datetime.strptime(row["last_day"], "%Y-%m-%d").date()
    alive = last >= today_ar() - timedelta(days=1)
    return (row["current"] if alive else 0), row["best"]


def add_time(user_id, seconds):
    """Suma tiempo al total del usuario y lo registra como sesión. Devuelve el total nuevo."""
    if seconds <= 0:
        return get_total(user_id)
    with db_connect() as conn:
        conn.execute(
            "INSERT INTO users (user_id, total_seconds) VALUES (?, ?) "
            "ON CONFLICT(user_id) DO UPDATE SET total_seconds = total_seconds + excluded.total_seconds",
            (user_id, seconds),
        )
        conn.execute("INSERT INTO sessions (user_id, ended_at, seconds) VALUES (?, ?, ?)", (user_id, time.time(), seconds))
        update_streak(conn, user_id)
        return conn.execute("SELECT total_seconds FROM users WHERE user_id = ?", (user_id,)).fetchone()[0]


def get_total(user_id):
    with db_connect() as conn:
        row = conn.execute("SELECT total_seconds FROM users WHERE user_id = ?", (user_id,)).fetchone()
        return row[0] if row else 0


def reset_user(user_id):
    with db_connect() as conn:
        row = conn.execute("SELECT total_seconds FROM users WHERE user_id = ?", (user_id,)).fetchone()
        if not row:
            return None
        conn.execute("UPDATE users SET total_seconds = 0 WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
        return row[0]


def get_ranking(period_seconds=None, limit=10):
    """Top de usuarios. period_seconds=None usa el total histórico."""
    with db_connect() as conn:
        if period_seconds is None:
            rows = conn.execute(
                "SELECT user_id, total_seconds AS secs FROM users WHERE total_seconds > 0 ORDER BY secs DESC LIMIT ?",
                (limit,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT user_id, SUM(seconds) AS secs FROM sessions WHERE ended_at >= ? "
                "GROUP BY user_id ORDER BY secs DESC LIMIT ?",
                (time.time() - period_seconds, limit),
            ).fetchall()
    return [(r["user_id"], r["secs"]) for r in rows]


def count_users():
    with db_connect() as conn:
        return conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]


def format_duration(total_seconds):
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    return f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"


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


# ---------- Seguimiento de voz ----------

def start_session(member, channel):
    active_sessions[member.id] = {"since": time.time(), "guild": member.guild.id, "channel": channel.name}


async def close_session(member, channel_name, log=True):
    """Cierra la sesión del usuario, guarda el tiempo y revisa si gana un rol."""
    session = active_sessions.pop(member.id, None)
    if not session:
        return
    duration = time.time() - session["since"]
    total = add_time(member.id, duration)
    await check_and_assign_role(member, total)
    bot_stats["total_sessions"] += 1
    if log:
        add_activity_log(
            "LEAVE", member.display_name, channel_name,
            f"Sesión: {int(duration // 60)}m, Total: {int(total // 60)}m"
        )
        print(f"👋 {member.display_name} left {channel_name}. Total acumulado: {int(total // 60)} minutos")


async def scan_existing_users():
    """Scan existing users in voice channels and start tracking them"""
    print("🔍 Scanning existing users in voice channels...")

    for guild in bot.guilds:
        for channel_id in tracked_channels():
            channel = guild.get_channel(channel_id)
            if channel and isinstance(channel, discord.VoiceChannel):
                for member in channel.members:
                    if not member.bot and member.id not in active_sessions:
                        start_session(member, channel)
                        add_activity_log(
                            "SCAN_FOUND",
                            member.display_name,
                            channel.name,
                            "Found in voice channel during startup scan"
                        )
                        print(f"📍 Found {member.display_name} in {channel.name}")

    print(f"✅ Scan complete. Tracking {len(active_sessions)} users.")


@tasks.loop(seconds=CHECKPOINT_SECONDS)
async def checkpoint():
    """Guarda el tiempo corrido de todos los que siguen en voz, así un corte no lo pierde."""
    now = time.time()
    for user_id, session in list(active_sessions.items()):
        elapsed = now - session["since"]
        session["since"] = now
        total = add_time(user_id, elapsed)
        guild = bot.get_guild(session["guild"])
        member = guild.get_member(user_id) if guild else None
        if member:
            await check_and_assign_role(member, total)


@bot.event
async def setup_hook():
    init_db()
    await bot.tree.sync()
    print("✅ Comandos / sincronizados")


@bot.event
async def on_ready():
    print(f'🦇 {bot.user} has landed in the Batcave!')
    print(f'🏰 Connected to {len(bot.guilds)} server(s)')

    for guild in bot.guilds:
        print(f'   - {guild.name} (ID: {guild.id})')

    print(f'🎯 Monitoring {len(tracked_channels())} voice channels')
    print(f'🏆 {len(ROLE_SYSTEM)} progressive roles configured')
    print(f'📊 {count_users()} usuarios con progreso guardado')

    await scan_existing_users()
    if not checkpoint.is_running():
        checkpoint.start()
    if not check_feeds.is_running():
        check_feeds.start()
    if not scheduled_jobs.is_running():
        scheduled_jobs.start()

    activity = discord.Activity(
        type=discord.ActivityType.watching,
        name="the Batcave 🦇"
    )
    await bot.change_presence(activity=activity)

    print("🚀 BatCompany Bot is ready for action!")


@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot or before.channel == after.channel:
        return  # mute/deafen y otros cambios que no mueven de canal

    tracked = tracked_channels()
    was_tracked = before.channel is not None and before.channel.id in tracked
    is_tracked = after.channel is not None and after.channel.id in tracked

    if was_tracked:
        await close_session(member, before.channel.name, log=not is_tracked)

    if is_tracked:
        start_session(member, after.channel)
        if was_tracked:
            print(f"🔄 {member.display_name} cambió de {before.channel.name} a {after.channel.name}")
        else:
            add_activity_log("JOIN", member.display_name, after.channel.name)
            print(f"🎤 {member.display_name} joined {after.channel.name}")


# ---------- Roles ----------

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
            value=format_duration(total_seconds),
            inline=True
        )
        embed.add_field(
            name="Descripción",
            value=role_config["description"],
            inline=False
        )
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)

        # Canal elegido con /canal; si no hay, "general" o el primero disponible
        channel = get_configured_channel(guild, "roles")
        if not channel:
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


# ---------- Juegos gratis y novedades de PUBG ----------

def get_configured_channel(guild, kind):
    """Canal de texto configurado con /canal para 'roles', 'juegos' o 'pubg'."""
    channel_id = get_setting(f"channel_{kind}") or DEFAULT_CHANNELS.get(kind)
    channel = guild.get_channel(int(channel_id)) if channel_id else None
    return channel if isinstance(channel, discord.TextChannel) else None


async def fetch_json(url):
    timeout = aiohttp.ClientTimeout(total=20)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url) as response:
            response.raise_for_status()
            return await response.json(content_type=None)


async def fetch_epic_free_games():
    data = await fetch_json(EPIC_FREE_URL)
    games = []
    for el in data["data"]["Catalog"]["searchStore"]["elements"]:
        offers = (el.get("promotions") or {}).get("promotionalOffers") or []
        if not offers or el["price"]["totalPrice"]["discountPrice"] != 0:
            continue
        slug = el.get("productSlug") or el.get("urlSlug")
        image = next((i["url"] for i in el.get("keyImages", []) if i["type"] in ("OfferImageWide", "Thumbnail")), None)
        games.append({
            "id": f"epic:{el['id']}",
            "title": el["title"],
            "platform": "Epic Games",
            "url": f"https://store.epicgames.com/es-AR/p/{slug}" if slug else "https://store.epicgames.com/es-AR/free-games",
            "image": image,
            "ends": offers[0]["promotionalOffers"][0]["endDate"][:10],
        })
    return games


async def fetch_other_free_games():
    """Juegos gratis de Steam y GOG (Epic ya viene de su API oficial)."""
    data = await fetch_json(GAMERPOWER_URL)
    games = []
    if not isinstance(data, list):
        return games
    for g in data:
        platforms = g.get("platforms", "")
        if "Epic" in platforms or not ("Steam" in platforms or "GOG" in platforms):
            continue
        games.append({
            "id": f"gp:{g['id']}",
            "title": re.sub(r"\s*\((Steam|GOG)\)\s*(Key\s*)?Giveaway", "", g["title"]),
            "platform": "Steam" if "Steam" in platforms else "GOG",
            "url": g["open_giveaway_url"],
            "image": g.get("image"),
            "ends": g["end_date"][:10] if g.get("end_date") and g["end_date"] != "N/A" else None,
        })
    return games


async def post_free_games(channel):
    games = []
    for fetcher in (fetch_epic_free_games, fetch_other_free_games):
        try:
            games += await fetcher()
        except Exception as e:
            print(f"⚠️ No se pudo consultar juegos gratis ({fetcher.__name__}): {e}")

    for game in games:
        if is_seen("games", game["id"]):
            continue
        embed = discord.Embed(
            title=f"🎁 ¡Gratis en {game['platform']}: {game['title']}!",
            url=game["url"],
            description="Reclamalo antes de que termine la promo.",
            color=discord.Color.green(),
        )
        if game["ends"]:
            embed.add_field(name="Hasta", value=game["ends"], inline=True)
        if game["image"]:
            embed.set_image(url=game["image"])
        await channel.send(embed=embed)
        mark_seen("games", game["id"])


def clean_steam_text(text):
    text = re.sub(r"\{STEAM_CLAN_IMAGE\}\S+", "", text)
    text = re.sub(r"\[/?[a-zA-Z0-9=_*\- ]+\]", "", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


async def post_pubg_news(channel):
    data = await fetch_json(PUBG_NEWS_URL)
    items = [
        n for n in data["appnews"]["newsitems"]
        if n["feedname"] == "steam_community_announcements"
        and not any(skip in n["title"].lower() for skip in PUBG_NEWS_SKIP)
    ]

    # Primera vez: se marcan como vistas para no llenar el canal con noticias viejas
    first_run = not seen_any("pubg")
    for item in reversed(items):  # de la más vieja a la más nueva
        if is_seen("pubg", item["gid"]):
            continue
        mark_seen("pubg", item["gid"])
        if first_run:
            continue
        embed = discord.Embed(
            title=f"📰 {item['title']}",
            url=f"https://store.steampowered.com/news/app/{PUBG_STEAM_APPID}/view/{item['gid']}",
            description=clean_steam_text(item["contents"])[:400],
            color=discord.Color.dark_gold(),
            timestamp=datetime.fromtimestamp(item["date"]),
        )
        embed.set_footer(text="PUBG: BATTLEGROUNDS · Steam")
        await channel.send(embed=embed)


@tasks.loop(minutes=FEEDS_MINUTES)
async def check_feeds():
    for guild in bot.guilds:
        games_channel = get_configured_channel(guild, "juegos")
        if games_channel:
            try:
                await post_free_games(games_channel)
            except Exception as e:
                print(f"⚠️ Error publicando juegos gratis: {e}")

        pubg_channel = get_configured_channel(guild, "pubg")
        if pubg_channel:
            try:
                await post_pubg_news(pubg_channel)
            except Exception as e:
                print(f"⚠️ Error publicando noticias de PUBG: {e}")


# ---------- Comandos / ----------

@bot.tree.command(name="canal", description="Elegí en qué canal publica el bot (solo administradores)")
@app_commands.describe(tipo="Qué publicaciones van a ese canal", canal="Canal de texto")
@app_commands.choices(tipo=[
    app_commands.Choice(name="Juegos gratis", value="juegos"),
    app_commands.Choice(name="Novedades de PUBG", value="pubg"),
    app_commands.Choice(name="Avisos de roles nuevos", value="roles"),
    app_commands.Choice(name="Resumen semanal y mensual", value="resumen"),
    app_commands.Choice(name="Bienvenidas, cumpleaños y aniversarios", value="comunidad"),
])
@app_commands.default_permissions(administrator=True)
@app_commands.checks.has_permissions(administrator=True)
async def canal(interaction: discord.Interaction, tipo: app_commands.Choice[str], canal: discord.TextChannel):
    set_setting(f"channel_{tipo.value}", canal.id)
    await interaction.response.send_message(f"✅ **{tipo.name}** se van a publicar en {canal.mention}.", ephemeral=True)
    if tipo.value == "juegos":
        await post_free_games(canal)
    elif tipo.value == "pubg":
        await post_pubg_news(canal)  # la primera vez solo marca las noticias actuales como vistas

def current_total(user_id):
    """Total guardado más la sesión que todavía está corriendo."""
    total = get_total(user_id)
    session = active_sessions.get(user_id)
    session_seconds = time.time() - session["since"] if session else 0
    return total + session_seconds, session_seconds


@bot.tree.command(name="tiempo", description="Mirá tu tiempo acumulado en los canales de voz")
@app_commands.describe(usuario="De quién ver el tiempo (por defecto, el tuyo)")
async def tiempo(interaction: discord.Interaction, usuario: discord.Member = None):
    member = usuario or interaction.user
    total_seconds, session_seconds = current_total(member.id)

    embed = discord.Embed(
        title=f"⏰ Tiempo en voz de {member.display_name}",
        color=discord.Color.blue()
    )
    embed.add_field(name="Tiempo Total Acumulado", value=format_duration(total_seconds), inline=True)

    if session_seconds > 0:
        embed.add_field(name="Sesión Actual", value=format_duration(session_seconds), inline=True)

    # Mostrar próximo rol
    current_level = get_user_role_level(member)
    if current_level + 1 < len(ROLE_SYSTEM):
        next_role = ROLE_SYSTEM[current_level + 1]
        time_needed = next_role["time_seconds"] - total_seconds
        if time_needed > 0:
            embed.add_field(
                name="Próximo Rol",
                value=f"{next_role['name']} (faltan {format_duration(time_needed)})",
                inline=False
            )
    else:
        embed.add_field(name="Rol", value="¡Ya tenés el rango máximo! 🦇⚡", inline=False)

    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
    await interaction.response.send_message(embed=embed)


RANKING_PERIODS = {
    "total": ("🏆 Ranking histórico", None),
    "semana": ("📅 Ranking de los últimos 7 días", 7 * 86400),
    "mes": ("🗓️ Ranking de los últimos 30 días", 30 * 86400),
}


@bot.tree.command(name="ranking", description="Top de quienes más tiempo pasaron en voz")
@app_commands.describe(periodo="Qué período mostrar")
@app_commands.choices(periodo=[
    app_commands.Choice(name="Histórico", value="total"),
    app_commands.Choice(name="Últimos 7 días", value="semana"),
    app_commands.Choice(name="Últimos 30 días", value="mes"),
])
async def ranking(interaction: discord.Interaction, periodo: app_commands.Choice[str] = None):
    key = periodo.value if periodo else "total"
    title, period_seconds = RANKING_PERIODS[key]
    top = get_ranking(period_seconds)

    if not top:
        await interaction.response.send_message("📭 Todavía no hay tiempo registrado en ese período.")
        return

    medals = ["🥇", "🥈", "🥉"]
    lines = []
    for i, (user_id, secs) in enumerate(top):
        member = interaction.guild.get_member(user_id) if interaction.guild else None
        name = member.display_name if member else f"Usuario {user_id}"
        prefix = medals[i] if i < 3 else f"`{i + 1}.`"
        lines.append(f"{prefix} **{name}** — {format_duration(secs)}")

    embed = discord.Embed(title=title, description="\n".join(lines), color=discord.Color.gold())
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="resettiempo", description="Resetea el tiempo acumulado de un usuario (solo administradores)")
@app_commands.describe(usuario="A quién resetearle el tiempo")
@app_commands.default_permissions(administrator=True)
@app_commands.checks.has_permissions(administrator=True)
async def resettiempo(interaction: discord.Interaction, usuario: discord.Member):
    old_seconds = reset_user(usuario.id)

    if old_seconds is None:
        await interaction.response.send_message(f"{usuario.mention} no tiene tiempo registrado.", ephemeral=True)
        return

    if usuario.id in active_sessions:
        active_sessions[usuario.id]["since"] = time.time()

    embed = discord.Embed(
        title="🔄 Tiempo Reseteado",
        description=f"El tiempo de {usuario.mention} ha sido reseteado.",
        color=discord.Color.orange()
    )
    embed.add_field(name="Tiempo Anterior", value=format_duration(old_seconds), inline=True)
    embed.add_field(name="Tiempo Actual", value="0m", inline=True)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="estadisticas", description="Estadísticas del bot y de los canales de voz (solo administradores)")
@app_commands.default_permissions(administrator=True)
@app_commands.checks.has_permissions(administrator=True)
async def estadisticas(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🦇 BatCompany Voice Statistics",
        color=discord.Color.dark_purple(),
        timestamp=datetime.now()
    )

    embed.add_field(name="👥 En voz ahora", value=len(active_sessions), inline=True)
    embed.add_field(name="🏆 Roles entregados", value=bot_stats["roles_assigned"], inline=True)
    embed.add_field(name="📊 Sesiones cerradas", value=bot_stats["total_sessions"], inline=True)
    embed.add_field(name="💾 Usuarios con progreso", value=count_users(), inline=True)

    uptime = datetime.now() - bot_stats["start_time"]
    embed.add_field(name="⏰ Bot Uptime", value=format_duration(uptime.total_seconds()), inline=True)

    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="configuracion", description="Muestra la configuración del bot (solo administradores)")
@app_commands.default_permissions(administrator=True)
@app_commands.checks.has_permissions(administrator=True)
async def configuracion(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🦇 BatCompany Configuration",
        color=discord.Color.gold(),
        timestamp=datetime.now()
    )

    channel_list = []
    for channel_id in tracked_channels():
        channel = interaction.guild.get_channel(channel_id)
        if channel:
            channel_list.append(f"• {channel.name}")
        else:
            channel_list.append(f"• Channel ID: {channel_id} (Not found)")

    embed.add_field(
        name="🎤 Monitored Voice Channels",
        value="\n".join(channel_list) if channel_list else "None configured",
        inline=False
    )

    role_list = [f"• {r['name']} - {r['time_seconds']//60} min" for r in ROLE_SYSTEM]
    embed.add_field(name="🏆 Progressive Role System", value="\n".join(role_list), inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="historial", description="Actividad reciente del bot (solo administradores)")
@app_commands.describe(cantidad="Cuántas entradas mostrar (máximo 20)")
@app_commands.default_permissions(administrator=True)
@app_commands.checks.has_permissions(administrator=True)
async def historial(interaction: discord.Interaction, cantidad: app_commands.Range[int, 1, 20] = 10):
    if not activity_history:
        await interaction.response.send_message("📝 No activity history available", ephemeral=True)
        return

    embed = discord.Embed(
        title="📋 Recent Activity History",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )

    activity_text = []
    for activity in reversed(activity_history[-cantidad:]):
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
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="canalvoz", description="Elegí qué canales de voz cuentan tiempo (solo administradores)")
@app_commands.describe(accion="Qué hacer", canal="Canal de voz (no hace falta para ver la lista)")
@app_commands.choices(accion=[
    app_commands.Choice(name="Agregar", value="agregar"),
    app_commands.Choice(name="Quitar", value="quitar"),
    app_commands.Choice(name="Ver lista", value="ver"),
])
@app_commands.default_permissions(administrator=True)
@app_commands.checks.has_permissions(administrator=True)
async def canalvoz(interaction: discord.Interaction, accion: app_commands.Choice[str], canal: discord.VoiceChannel = None):
    ids = tracked_channels()
    if accion.value == "ver":
        lines = []
        for channel_id in ids:
            ch = interaction.guild.get_channel(channel_id)
            lines.append(f"• {ch.name}" if ch else f"• (no existe) {channel_id}")
        await interaction.response.send_message("🎤 **Canales que cuentan tiempo:**\n" + "\n".join(lines), ephemeral=True)
        return
    if canal is None:
        await interaction.response.send_message("❌ Elegí un canal de voz.", ephemeral=True)
        return
    if accion.value == "agregar":
        if canal.id in ids:
            await interaction.response.send_message(f"ℹ️ {canal.mention} ya cuenta tiempo.", ephemeral=True)
            return
        ids.append(canal.id)
        save_tracked_channels(ids)
        for member in canal.members:  # los que ya están adentro empiezan a contar
            if not member.bot and member.id not in active_sessions:
                start_session(member, canal)
        await interaction.response.send_message(f"✅ {canal.mention} ahora cuenta tiempo.", ephemeral=True)
    else:
        if canal.id not in ids:
            await interaction.response.send_message(f"ℹ️ {canal.mention} no estaba en la lista.", ephemeral=True)
            return
        ids.remove(canal.id)
        save_tracked_channels(ids)
        for member in canal.members:  # se cierra lo que llevaban hasta ahora
            await close_session(member, canal.name, log=False)
        await interaction.response.send_message(f"✅ {canal.mention} dejó de contar tiempo.", ephemeral=True)


# ---------- Resúmenes y respaldo ----------

def ranking_between(start_ts, end_ts, limit=5):
    """Top y totales de un rango de fechas (epoch)."""
    with db_connect() as conn:
        rows = conn.execute(
            "SELECT user_id, SUM(seconds) AS secs FROM sessions WHERE ended_at >= ? AND ended_at < ? "
            "GROUP BY user_id ORDER BY secs DESC",
            (start_ts, end_ts),
        ).fetchall()
    total = sum(r["secs"] for r in rows)
    return [(r["user_id"], r["secs"]) for r in rows[:limit]], total, len(rows)


async def post_report(channel, title, start_ts, end_ts):
    top, total, people = ranking_between(start_ts, end_ts)
    if not top:
        return False
    medals = ["🥇", "🥈", "🥉"]
    lines = []
    for i, (user_id, secs) in enumerate(top):
        member = channel.guild.get_member(user_id)
        name = member.display_name if member else f"Usuario {user_id}"
        prefix = medals[i] if i < 3 else f"`{i + 1}.`"
        lines.append(f"{prefix} **{name}** — {format_duration(secs)}")
    embed = discord.Embed(title=title, description="\n".join(lines), color=discord.Color.gold())
    embed.add_field(name="👥 Participaron", value=str(people))
    embed.add_field(name="⏱️ Tiempo total en voz", value=format_duration(total))
    await channel.send(embed=embed)
    return True


def month_bounds(now):
    """(inicio, fin, nombre) del mes calendario anterior a 'now', en epoch."""
    first_this = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_prev = first_this - timedelta(days=1)
    first_prev = last_prev.replace(day=1)
    meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
             "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    return first_prev.timestamp(), first_this.timestamp(), f"{meses[first_prev.month - 1]} {first_prev.year}"


async def send_backup(destination):
    """Copia consistente de la base y envío como archivo a 'destination' (usuario o interaction)."""
    stamp = datetime.now(AR_TZ).strftime("%Y-%m-%d")
    path = f"respaldo-{stamp}.db"
    src = sqlite3.connect(DB_PATH)
    dst = sqlite3.connect(path)
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()
    try:
        return await destination(file=discord.File(path))
    finally:
        os.remove(path)


@tasks.loop(minutes=10)
async def scheduled_jobs():
    """Resumen semanal (domingos), mensual (día 1) y respaldo semanal, con la hora de Argentina."""
    now = datetime.now(AR_TZ)
    week_key = f"{now.isocalendar().year}-W{now.isocalendar().week}"

    if now.weekday() == 6 and now.hour >= REPORT_HOUR:
        if get_setting("last_weekly") != week_key:
            set_setting("last_weekly", week_key)
            for guild in bot.guilds:
                await update_top_role(guild)
                channel = get_configured_channel(guild, "resumen")
                if channel:
                    try:
                        await post_report(channel, "📅 Resumen de la semana", time.time() - 7 * 86400, time.time())
                    except Exception as e:
                        print(f"⚠️ Error en el resumen semanal: {e}")
        if get_setting("last_backup") != week_key:
            set_setting("last_backup", week_key)
            try:
                owner = (await bot.application_info()).owner
                await send_backup(owner.send)
                print("💾 Respaldo enviado por mensaje privado")
            except Exception as e:
                print(f"⚠️ Error enviando el respaldo: {e}")

    if now.hour >= 10 and get_setting("last_daily") != now.date().isoformat():
        set_setting("last_daily", now.date().isoformat())
        for guild in bot.guilds:
            try:
                await post_daily_greetings(guild, now)
            except Exception as e:
                print(f"⚠️ Error en cumpleaños y aniversarios: {e}")

    if now.day == 1 and now.hour >= 12:
        month_key = now.strftime("%Y-%m")
        if get_setting("last_monthly") != month_key:
            set_setting("last_monthly", month_key)
            start_ts, end_ts, name = month_bounds(now)
            for guild in bot.guilds:
                channel = get_configured_channel(guild, "resumen")
                if channel:
                    try:
                        await post_report(channel, f"🗓️ Resumen de {name}", start_ts, end_ts)
                    except Exception as e:
                        print(f"⚠️ Error en el resumen mensual: {e}")


@bot.tree.command(name="resumen", description="Publica ahora el resumen semanal o mensual (solo administradores)")
@app_commands.describe(tipo="Qué resumen publicar")
@app_commands.choices(tipo=[
    app_commands.Choice(name="Semanal (últimos 7 días)", value="semana"),
    app_commands.Choice(name="Mensual (mes anterior)", value="mes"),
])
@app_commands.default_permissions(administrator=True)
@app_commands.checks.has_permissions(administrator=True)
async def resumen(interaction: discord.Interaction, tipo: app_commands.Choice[str]):
    channel = get_configured_channel(interaction.guild, "resumen")
    if not channel:
        await interaction.response.send_message("❌ No hay canal de resumen. Usá /canal.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    if tipo.value == "semana":
        ok = await post_report(channel, "📅 Resumen de la semana", time.time() - 7 * 86400, time.time())
    else:
        start_ts, end_ts, name = month_bounds(datetime.now(AR_TZ))
        ok = await post_report(channel, f"🗓️ Resumen de {name}", start_ts, end_ts)
    await interaction.followup.send(f"✅ Publicado en {channel.mention}." if ok else "📭 No hay tiempo registrado en ese período.", ephemeral=True)


@bot.tree.command(name="respaldo", description="Te manda una copia de la base de datos (solo administradores)")
@app_commands.default_permissions(administrator=True)
@app_commands.checks.has_permissions(administrator=True)
async def respaldo(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    await send_backup(lambda file: interaction.followup.send("💾 Respaldo de la base:", file=file, ephemeral=True))


# ---------- Comunidad: rol semanal, bienvenida, cumpleaños, racha ----------

async def update_top_role(guild):
    """Le da el rol de más activo a quien lideró los últimos 7 días y se lo saca a los demás."""
    top = get_ranking(7 * 86400, limit=1)
    if not top:
        return
    try:
        role = discord.utils.get(guild.roles, name=TOP_ROLE_NAME)
        if not role:
            role = await guild.create_role(name=TOP_ROLE_NAME, color=discord.Color.red(), reason="Más activo de la semana")
        winner = guild.get_member(top[0][0])
        for member in list(role.members):
            if not winner or member.id != winner.id:
                await member.remove_roles(role, reason="Terminó la semana")
        if winner and role not in winner.roles:
            await winner.add_roles(role, reason="Más activo de la semana")
    except Exception as e:
        print(f"⚠️ No se pudo actualizar el rol de más activo: {e}")


@bot.event
async def on_member_join(member):
    if member.bot:
        return
    channel = get_configured_channel(member.guild, "comunidad") or member.guild.system_channel
    if not channel:
        return
    roles = " → ".join(r["name"] for r in ROLE_SYSTEM)
    embed = discord.Embed(
        title=f"🦇 ¡Bienvenido a {member.guild.name}!",
        description=(
            f"{member.mention}, qué bueno que estés acá.\n\n"
            f"Pasá tiempo en los canales de voz y vas a ir ganando rangos solo:\n{roles}\n\n"
            "Probá `/tiempo` para ver tus horas."
        ),
        color=discord.Color.gold(),
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    try:
        await channel.send(embed=embed)
    except Exception as e:
        print(f"⚠️ No se pudo dar la bienvenida: {e}")


async def post_daily_greetings(guild, now):
    channel = get_configured_channel(guild, "comunidad")
    if not channel:
        return
    lines = []
    with db_connect() as conn:
        rows = conn.execute("SELECT user_id FROM birthdays WHERE day = ? AND month = ?", (now.day, now.month)).fetchall()
    for r in rows:
        member = guild.get_member(r["user_id"])
        if member:
            lines.append(f"🎂 ¡Hoy cumple años {member.mention}! Que lo pase genial 🦇🎉")
    for member in guild.members:
        if member.bot or not member.joined_at:
            continue
        joined = member.joined_at.astimezone(AR_TZ)
        years = now.year - joined.year
        if years >= 1 and (joined.day, joined.month) == (now.day, now.month):
            lines.append(f"🦇 {member.mention} cumple {years} {'año' if years == 1 else 'años'} en la BatCompany. ¡Gracias por quedarte!")
    if lines:
        await channel.send("\n".join(lines))


@bot.tree.command(name="cumple", description="Guardá tu cumpleaños para que el bot te salude")
@app_commands.describe(dia="Día (1 a 31)", mes="Mes (1 a 12)")
async def cumple(interaction: discord.Interaction, dia: app_commands.Range[int, 1, 31], mes: app_commands.Range[int, 1, 12]):
    try:
        datetime(2024, mes, dia)  # valida que el día exista en ese mes
    except ValueError:
        await interaction.response.send_message("❌ Esa fecha no existe.", ephemeral=True)
        return
    with db_connect() as conn:
        conn.execute(
            "INSERT INTO birthdays (user_id, day, month) VALUES (?, ?, ?) "
            "ON CONFLICT(user_id) DO UPDATE SET day = excluded.day, month = excluded.month",
            (interaction.user.id, dia, mes),
        )
    await interaction.response.send_message(f"🎂 Listo, anoté tu cumpleaños: {dia}/{mes}.", ephemeral=True)


@bot.tree.command(name="racha", description="Mirá tu racha de días seguidos en voz")
@app_commands.describe(usuario="Otro usuario (opcional)")
async def racha(interaction: discord.Interaction, usuario: discord.Member = None):
    target = usuario or interaction.user
    current, best = get_streak(target.id)
    if best == 0:
        await interaction.response.send_message(f"📭 {target.display_name} todavía no tiene racha.")
        return
    fire = "🔥" if current >= 3 else "📅"
    await interaction.response.send_message(
        f"{fire} **{target.display_name}** — racha actual: **{current}** {'día' if current == 1 else 'días'} seguidos · mejor racha: **{best}**"
    )


# ---------- PUBG: llaves, mapas, drop y tips ----------

MAPS_URL = "https://raw.githubusercontent.com/DavidSaboredo/batbot/mejoras/sqlite-slash/maps"

# mapa: (texto corto, imagen o None)
LLAVES = {
    "Erangel": ("Unas 15 salas secretas. La llave es botín al azar y abre una sola sala (se destruye al usarla).", "erangel.png"),
    "Taego": ("Unas 12-13 salas de seguridad (el mapa puede variar desde la actualización 42.2).", "taego.png"),
    "Vikendi": ("Llaves de seguridad: salen de las cajas amarillas de los Lab Camps. Las salas con palanca no necesitan llave.", "vikendi.png"),
}


@bot.tree.command(name="llaves", description="Mapa con las salas secretas de PUBG")
@app_commands.describe(mapa="Mapa")
@app_commands.choices(mapa=[app_commands.Choice(name=n, value=n) for n in LLAVES])
async def llaves(interaction: discord.Interaction, mapa: app_commands.Choice[str]):
    text, image = LLAVES[mapa.value]
    embed = discord.Embed(title=f"🔑 Salas secretas — {mapa.value}", description=text, color=discord.Color.dark_gold())
    if image:
        embed.set_image(url=f"{MAPS_URL}/{image}")
    embed.set_footer(text="Solo en partidas normales (no ranked) · Base de mapas: GGRecon")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="mapas", description="Mapas de PUBG en juego")
async def mapas(interaction: discord.Interaction):
    embed = discord.Embed(title="🗺️ Mapas de PUBG", color=discord.Color.blue())
    embed.add_field(name="🏅 Ranked", value="Erangel, Miramar, Taego y Rondo (25% cada uno, según la actualización 43.2).", inline=False)
    embed.add_field(name="🎯 Partidas normales", value="Erangel es fijo; el resto rota por semana. Mirá la lista de mapas dentro del juego.", inline=False)
    embed.set_footer(text="La rotación la define Krafton y cambia con los parches.")
    await interaction.response.send_message(embed=embed)


DROP_SPOTS = {
    "Erangel": [
        ("Pochinki", "🔥 alto riesgo"), ("School", "🔥 alto riesgo"), ("Georgopol", "🔥 alto riesgo"),
        ("Military Base", "🔥 alto riesgo"), ("Rozhok", "🔥 alto riesgo"), ("Yasnaya Polyana", "🟠 medio"),
        ("Novorepnoye", "🟠 medio"), ("Primorsk", "🟠 medio"), ("Mylta", "🟢 tranquilo"),
        ("Kameshki", "🟢 tranquilo"), ("Lipovka", "🟢 tranquilo"), ("Zharki", "🟢 tranquilo"),
        ("Severny", "🟢 tranquilo"), ("Stalber", "🟢 tranquilo"),
    ],
    "Miramar": [
        ("Pecado", "🔥 alto riesgo"), ("Hacienda del Patrón", "🔥 alto riesgo"), ("Los Leones", "🔥 alto riesgo"),
        ("El Pozo", "🟠 medio"), ("San Martín", "🟠 medio"), ("Monte Nuevo", "🟢 tranquilo"),
        ("Los Higos", "🟢 tranquilo"), ("Impala", "🟢 tranquilo"), ("Valle del Mar", "🟢 tranquilo"),
        ("Cruz del Valle", "🟢 tranquilo"),
    ],
    "Vikendi": [
        ("Castle", "🔥 alto riesgo"), ("Cosmodrome", "🔥 alto riesgo"), ("Dino Park", "🟠 medio"),
        ("Podvosto", "🟠 medio"), ("Villa", "🟠 medio"), ("Trevno", "🟢 tranquilo"),
        ("Goroka", "🟢 tranquilo"), ("Port", "🟢 tranquilo"),
    ],
}


@bot.tree.command(name="drop", description="Te sugiere dónde tirarte en PUBG")
@app_commands.describe(mapa="Mapa")
@app_commands.choices(mapa=[app_commands.Choice(name=n, value=n) for n in DROP_SPOTS])
async def drop(interaction: discord.Interaction, mapa: app_commands.Choice[str]):
    spot, risk = random.choice(DROP_SPOTS[mapa.value])
    await interaction.response.send_message(f"🪂 **{mapa.value}** → tirate en **{spot}** ({risk})")


TIPS = [
    "Escuchá siempre con auriculares: los pasos te avisan de dónde vienen antes de ver al enemigo.",
    "Antes de cruzar un campo abierto, fijate si hay cobertura (rocas, árboles, autos) cada 20 metros.",
    "Llevá al menos un humo por compañero: sirve para revivir y para cruzar zonas expuestas.",
    "No te quedes saqueando con un enemigo cerca: primero cubrite, después lootear.",
    "Mirá el mapa seguido: la zona azul no perdona a quien se queda lejos.",
    "Comunicá posiciones con referencias claras (\"edificio rojo al norte\") en vez de \"ahí\".",
    "Ajustá la sensibilidad con calma en el campo de entrenamiento hasta que apuntar te resulte cómodo.",
    "Si el equipo está dividido, juntense antes del círculo final: pelear 4 contra 1 gana partidas.",
    "Los vehículos hacen ruido: usalos para cruzar, no para llegar justo al lado del enemigo.",
    "Revivir en el medio del fuego casi siempre sale mal: primero tirá humo o eliminá la amenaza.",
    "Cambiá de posición después de disparar: el que se queda quieto es el que cae.",
]


@bot.tree.command(name="tips", description="Un consejo rápido para mejorar en PUBG")
async def tips(interaction: discord.Interaction):
    await interaction.response.send_message(f"💡 {random.choice(TIPS)}")


@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        message = "❌ No tenés permisos de administrador para usar este comando."
    else:
        print(f"Command error: {error}")
        message = "❌ Ocurrió un error al ejecutar el comando."
    if interaction.response.is_done():
        await interaction.followup.send(message, ephemeral=True)
    else:
        await interaction.response.send_message(message, ephemeral=True)


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
