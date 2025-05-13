import os
import csv
import string
import datetime
from zoneinfo import ZoneInfo
import random

import discord
from discord.ext import commands

from core.logger import setup_error_handling
from config import DISCORD_TOKEN, LOG_GUILD_ID
from user_utils import update_known_users

# ----- Database (CSV) setup -----
DB_DIR = "db"
DB_FILE = os.path.join(DB_DIR, "counter.csv")
os.makedirs(DB_DIR, exist_ok=True)

# In-memory stats keyed by (user_id, guild_id)
stats = {}
max_id = 0

# Load existing data or initialize file
if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "entry_id", "user_id", "guild_id", "messages", "words", "characters"])
else:
    with open(DB_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                record_id = int(row["id"])
                uid = row["user_id"]
                gid = row["guild_id"]
                stats[(uid, gid)] = {
                    "id": record_id,
                    "entry_id": row["entry_id"],
                    "user_id": uid,
                    "guild_id": gid,
                    "messages": int(row["messages"]),
                    "words": int(row["words"]),
                    "characters": int(row["characters"]),
                }
                if record_id > max_id:
                    max_id = record_id
            except (KeyError, ValueError):
                continue

# Persist stats to CSV
def save_stats():
    with open(DB_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["id", "entry_id", "user_id", "guild_id", "messages", "words", "characters"]
        )
        writer.writeheader()
        for rec in stats.values():
            writer.writerow(rec)

# ----- Bot setup -----
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
bot = commands.AutoShardedBot(command_prefix="!", intents=intents)

# ----- Event: track every user message -----
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or message.guild is None:
        return

    uid = str(message.author.id)
    gid = str(message.guild.id)
    key = (uid, gid)

    global max_id
    if key not in stats:
        max_id += 1
        entry_id = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
        stats[key] = {
            "id": max_id,
            "entry_id": entry_id,
            "user_id": uid,
            "guild_id": gid,
            "messages": 0,
            "words": 0,
            "characters": 0,
        }

    rec = stats[key]
    rec["messages"] += 1
    content = message.content or ""
    rec["words"] += len(content.split())
    rec["characters"] += len(content)

    save_stats()
    await bot.process_commands(message)

# ----- Session-ID generation & logging -----
SESSION_FILE = "sessions.csv"

def generate_session_id():
    chars = string.ascii_lowercase + string.digits
    return "".join(random.choice(chars) for _ in range(8))

# Create file + header if it doesn't exist
if not os.path.exists(SESSION_FILE):
    with open(SESSION_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "session_id", "datetime_now"])

# Read existing IDs & find max row-ID
existing = set()
max_id = 0
with open(SESSION_FILE, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        existing.add(row["session_id"])
        try:
            row_id = int(row["id"])
            max_id = max(max_id, row_id)
        except ValueError:
            pass

# Pick a fresh session_id
session_id = generate_session_id()
while session_id in existing:
    session_id = generate_session_id()

# Append new row
new_id = max_id + 1
now_iso = datetime.datetime.now().isoformat()
with open(SESSION_FILE, "a", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow([new_id, session_id, now_iso])

# ----- Activity updater -----
async def update_activity():
    # set a custom status with an emoji
    await bot.change_presence(
        activity=discord.CustomActivity(name=f"Hello, chat! (Session ID: {session_id})", emoji=":wave:")
    )

# ----- Load extensions, events, etc. -----
async def load_cogs():
    extensions = [
        "bot.commands.general",
        "bot.commands.info",
        "bot.commands.admin",
    ]
    for ext in extensions:
        if ext not in bot.extensions:
            try:
                await bot.load_extension(ext)
                print(f"Loaded extension: {ext}")
            except commands.ExtensionAlreadyLoaded:
                print(f"Extension already loaded, skipping: {ext}")

# Function to fetch and display command IDs
async def fetch_command_ids():
    commands = await bot.tree.fetch_commands()
    print("\n=== Registered Slash Commands ===")
    for cmd in commands:
        print(f"/{cmd.name} - ID: {cmd.id}")
    print("================================\n")

# Event to update known users when the bot is ready
@bot.event
async def on_ready():
    global cogs_loaded
    if not globals().get("cogs_loaded", False):
        await load_cogs()
        globals()["cogs_loaded"] = True
    await bot.tree.sync()
    await bot.tree.sync(guild=discord.Object(id=LOG_GUILD_ID))
    await fetch_command_ids()  # Fetch and display command IDs
    await update_known_users(bot)  # Update known users with all guild members
    await update_activity()  # Update the status on startup
    print(f"Logged in as {bot.user} (ID: {bot.user.id}) "
          f"with {bot.shard_count} shard(s) [Session ID: {session_id}]")

# Update known users and activity when joining a new guild
@bot.event
async def on_guild_join(guild):
    print(f"Joined new guild: {guild.name} (ID: {guild.id})")
    await update_known_users(bot)
    await update_activity()

# Update known users and activity when leaving a guild
@bot.event
async def on_guild_remove(guild):
    print(f"Left guild: {guild.name} (ID: {guild.id})")
    await update_known_users(bot)
    await update_activity()

# ----- Error handling & run bot -----
setup_error_handling(bot)
bot.run(DISCORD_TOKEN)