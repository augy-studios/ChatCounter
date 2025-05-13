import os
from dotenv import load_dotenv

# Load all variables from token.env
load_dotenv("token.env")

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
LOG_GUILD_ID = int(os.getenv("LOG_GUILD_ID")) if os.getenv("LOG_GUILD_ID") else None
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID")) if os.getenv("LOG_CHANNEL_ID") else None
BOT_OWNER_ID = int(os.getenv("BOT_OWNER_ID")) if os.getenv("BOT_OWNER_ID") else None
DISCORD_CLIENT_ID = int(os.getenv("DISCORD_CLIENT_ID")) if os.getenv("DISCORD_CLIENT_ID") else None
SHARD_COUNT = int(os.getenv("SHARD_COUNT")) if os.getenv("SHARD_COUNT") else 1
SHARD_IDS = [int(x) for x in os.getenv("SHARD_IDS").split(",")] if os.getenv("SHARD_IDS") else [0]
