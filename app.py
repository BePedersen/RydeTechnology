import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import logging
from Commands.opsplan import opsplan
from Commands.mechplan import mechplan
from Commands.edit import save_message, edit_last_message  # Import from edit.py
from Data_extraction.Deputy.match_names_from_deputy import match_and_update

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

# Define intents for the bot
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.members = True

# Initialize the bot
bot = commands.Bot(command_prefix="!", intents=intents)

async def prepare_data(ctx, output_file):
    """
    Prepare data before executing commands.
    """
    deputy_file = 'Data/Deputy/Stavanger_Deputy.csv'

    try:
        logging.info("Preparing data...")
        await match_and_update(ctx, deputy_file, output_file)
        logging.info(f"Name matching completed successfully and written to {output_file}.")
    except Exception as e:
        logging.error(f"Error during data preparation: {e}")
        await ctx.send(f"An error occurred during data preparation. Please try again.\n{e}")

@bot.command(name='opsplan')
async def opsplan_command(ctx):
    """
    Execute the opsplan functionality.
    """
    output_file = 'Data/people_on_shift_ops.csv'
    await prepare_data(ctx, output_file)

    try:
        bot_message = await ctx.send("This is your opsplan!")
        await save_message(ctx, bot_message)
        await opsplan(ctx)
    except Exception as e:
        logging.error(f"Error in opsplan command: {e}")
        await ctx.send("An error occurred while processing opsplan. Please try again.")

@bot.command(name='mechplan')
async def mechplan_command(ctx):
    """
    Execute the mechplan functionality.
    """
    output_file = 'Data/people_on_shift_mech.csv'
    await prepare_data(ctx, output_file)

    try:
        bot_message = await ctx.send("This is your mechplan!")
        await save_message(ctx, bot_message)
        await mechplan(ctx)
    except Exception as e:
        logging.error(f"Error in mechplan command: {e}")
        await ctx.send("An error occurred while processing mechplan. Please try again.")

@bot.command(name='editplan')
async def editplan_command(ctx, *, new_content=None):
    """
    Command to edit the last message sent by the bot for the user.
    """
    await edit_last_message(ctx, new_content)

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
