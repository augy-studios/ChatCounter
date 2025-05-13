import asyncio
import time
import datetime
import json
import os
import random
import re
import sys
import csv
from datetime import datetime

import lxml
import requests
from config import BOT_OWNER_ID, LOG_GUILD_ID
import discord
import psutil
from discord.ext import commands
from discord import app_commands

from core.logger import log_action
from main import stats
from shared import stats, max_id, words_stats, max_word_id

class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="leaderboard", description="Show the global message leaderboard")
    async def leaderboard(self, interaction: discord.Interaction):
        # Ensure there's data to show
        if not stats:
            await interaction.response.send_message("No message data yet.")
            return

        # Aggregate totals per user across all guilds
        user_totals: dict[str, dict[str, int]] = {}
        for (uid, _), rec in stats.items():
            totals = user_totals.setdefault(uid, {"messages": 0, "words": 0, "characters": 0})
            totals["messages"] += rec["messages"]
            totals["words"] += rec["words"]
            totals["characters"] += rec["characters"]

        # Take top 10 by message count
        top = sorted(
            user_totals.items(),
            key=lambda kv: kv[1]["messages"],
            reverse=True
        )[:10]

        # Build embed
        embed = discord.Embed(
            title="🏆 Global Message Leaderboard",
            description="Top 10 users by message count",
            color=discord.Color.blurple(),
            timestamp=datetime.datetime.utcnow()
        )
        for rank, (uid, tot) in enumerate(top, start=1):
            member = self.bot.get_user(int(uid))
            name = member.name if member else f"Unknown User ({uid})"
            embed.add_field(
                name=f"{rank}. {name}",
                value=(
                    f"{tot['messages']} messages | "
                    f"{tot['words']} words | "
                    f"{tot['characters']} characters"
                ),
                inline=False
            )

        await interaction.response.send_message(embed=embed)
        await log_action(self.bot, interaction)

async def setup(bot):
    await bot.add_cog(Stats(bot))
