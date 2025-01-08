import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import logging
from Commands.opsplan import opsplan
from Commands.mechplan import mechplan
from Data_extraction.Deputy.match_names_from_deputy import match_and_update  # Import match_and_update


# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

# Define intents for the bot
intents = discord.Intents.default()
intents.messages = True  # Allow reading messages
intents.message_content = True  # Allow access to message content
intents.guilds = True  # Allow interaction within guilds
intents.members = True  # Enable fetching member details

# Initialize the bot
bot = commands.Bot(command_prefix="!", intents=intents)

# Function to prepare data
async def prepare_data(ctx, output_file):
    """
    Prepares data before executing commands:
    - Matches names from Stavanger_Deputy.csv to Discord members.
    Writes results to the specified output file.
    """
    deputy_file = 'Data/Deputy/Stavanger_Deputy.csv'

    try:
        logging.info("Preparing data...")

        # Match names dynamically using Discord members and write to the specified file
        await match_and_update(ctx, deputy_file, output_file)
        logging.info(f"Name matching completed successfully and written to {output_file}.")

    except Exception as e:
        logging.error(f"Error during data preparation: {e}")
        await ctx.send(f"An error occurred during data preparation. Please try again.\n{e}")

# Command: Opsplan
@bot.command(name='opsplan')
async def opsplan_command(ctx):
    """
    Executes the opsplan functionality after preparing data.
    """
    output_file = 'Data/people_on_shift_ops.csv'  # File to write to for opsplan
    await prepare_data(ctx, output_file)  # Prepare data before running opsplan
    try:
        logging.info(f"Opsplan command triggered by {ctx.author.name}.")
        await opsplan(ctx)  # Call the opsplan function from opsplan.py
    except Exception as e:
        logging.error(f"Error in opsplan command: {e}")
        await ctx.send("An error occurred while processing opsplan. Please try again.")

# Command: Mechplan
@bot.command(name='mechplan')
async def mechplan_command(ctx):
    """
    Executes the mechplan functionality after preparing data.
    """
    output_file = 'Data/people_on_shift_mech.csv'  # File to write to for mechplan
    await prepare_data(ctx, output_file)  # Prepare data before running mechplan
    try:
        logging.info(f"Mechplan command triggered by {ctx.author.name}.")
        await mechplan(ctx)  # Call the mechplan function from mechplan.py
    except Exception as e:
        logging.error(f"Error in mechplan command: {e}")
        await ctx.send("An error occurred while processing mechplan. Please try again.")

# Run the bot
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
