import discord
import csv
from discord.ext import commands
import os
from dotenv import load_dotenv
import logging
from Commands.opsplan import opsplan
from Commands.mechplan import mechplan
from Commands.edit import save_message, edit_last_message  # Import from edit.py
from Data_extraction.Deputy.match_names_from_deputy import match_and_update
from Data_extraction.Deputy.update_ops_on_shift import update_ops
from Data_extraction.Deputy.update_mech_on_shift import update_mech


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


async def prepare_data(ctx, deputy_file, output_file):
    """
    Prepare data before executing commands.
    """
    try:
        logging.info("Preparing data...")
        await match_and_update(ctx, deputy_file, output_file)
        logging.info(
            f"Name matching completed successfully and written to {output_file}."
        )
    except Exception as e:
        logging.error(f"Error during data preparation: {e}")
        await ctx.send(
            f"An error occurred during data preparation. Please try again.\n{e}"
        )


@bot.command(name="opsplan")
async def opsplan_command(ctx):
    """
    Execute the opsplan functionality.
    """
    update_ops()
    deputy_file = "Data/Deputy/Bergen_ops.csv"
    output_file = "Data/people_on_shift_ops.csv"
    await prepare_data(ctx, deputy_file, output_file)
    try:
        bot_message = await ctx.send("This is your opsplan!")
        await save_message(ctx, bot_message)
        await opsplan(ctx)
    except Exception as e:
        logging.error(f"Error in opsplan command: {e}")
        await ctx.send("An error occurred while processing opsplan. Please try again.")


@bot.command(name="mechplan")
async def mechplan_command(ctx):
    """
    Execute the mechplan functionality.@
    """
    update_mech()
    deputy_file = "Data/Deputy/Bergen_mech.csv"
    output_file = "Data/people_on_shift_mech.csv"
    await prepare_data(ctx, deputy_file, output_file)

    try:
        bot_message = await ctx.send("This is your mechplan!")
        await save_message(ctx, bot_message)
        await mechplan(ctx)
    except Exception as e:
        logging.error(f"Error in mechplan command: {e}")
        await ctx.send("An error occurred while processing mechplan. Please try again.")


@bot.command(name="editplan")
async def editplan_command(ctx, *, new_content=None):
    """
    Command to edit the last message sent by the bot for the user.
    """
    await edit_last_message(ctx, new_content)


@bot.command(name="purge")
@commands.has_permissions(
    manage_messages=True
)  # Ensure the user has permission to manage messages
async def clear_channel(ctx):
    """
    Deletes all messages in the channel where the command is sent.
    """
    try:
        # Send a confirmation message before clearing messages
        confirmation_message = await ctx.send(
            "Clearing all messages in this channel..."
        )

        # Purge the channel
        await ctx.channel.purge()

        # Optionally, send a message after clearing (will delete itself)
        confirmation = await ctx.send("Channel cleared successfully!")
        await confirmation.delete(
            delay=5
        )  # Deletes the confirmation message after 5 seconds
    except discord.Forbidden:
        await ctx.send("I don't have permission to manage messages in this channel.")
    except Exception as e:
        logging.error(f"Error clearing channel: {e}")
        await ctx.send("An error occurred while clearing the channel.")


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
