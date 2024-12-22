import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import logging
from Commands.opsplan import opsplan


# Define the intents your bot will use
intents = discord.Intents.default()
intents.messages = True  # To allow reading messages (used in chat reading)
intents.message_content = True  # To access message content
intents.guilds = True  # To allow interaction within guilds


# Initialize the bot with intents
bot = commands.Bot(command_prefix="!", intents=intents)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


# Command for opsplan
@bot.command(name='opsplan')
async def opsplan_command(ctx):

    # Command to make sure that all the data files are up to date

    await opsplan(ctx)  # Call the opsplan function from opsplan.py


# Command for mechplan


# Command for question - AI bot


if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logging.error("DISCORD_TOKEN is not set in the environment.")
    else:
        try:
            logging.info("Starting the bot...")
            bot.run(token)
        except Exception as e:
            logging.exception("An error occurred while running the bot.")
