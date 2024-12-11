import discord
from discord.ext import commands
import os
from Commands import opsplan
from dotenv import load_dotenv

# Load environment variables (like bot token)
from dotenv import load_dotenv
load_dotenv()

# Initialize bot
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Opsplan
@bot.command(name='opsplan')
async def opsplan_command(ctx):
    if ctx.message.content == "!opsplan":
        # This is where we run the logic for the !opsplan command
        await opsplan.run()  # Run the opsplan code

# Run the bot
if __name__ == "__main__":
    bot.run(os.getenv("DISCORD_TOKEN"))
