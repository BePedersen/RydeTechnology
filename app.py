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

async def prepare_data(ctx,deputy_file, output_file):
    """
    Prepare data before executing commands.
    """
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
    update_ops()
    deputy_file = 'Data/Deputy/Bergen_ops.csv'
    output_file = 'Data/people_on_shift_ops.csv'
    await prepare_data(ctx,deputy_file, output_file)
    try:       
        #Pass ctx, deputy_file, and role_name explicitly to update_roles
        #await update_roles(ctx, output_file, role_name='Operations')
    
        bot_message = await ctx.send("This is your opsplan!")
        await save_message(ctx, bot_message)
        await opsplan(ctx)
    except Exception as e:
        logging.error(f"Error in opsplan command: {e}")
        await ctx.send("An error occurred while processing opsplan. Please try again.")

@bot.command(name='mechplan')
async def mechplan_command(ctx):
    """
    Execute the mechplan functionality.@
    """
    update_mech()
    deputy_file = 'Data/Deputy/Bergen_mech.csv'
    output_file = 'Data/people_on_shift_mech.csv'
    await prepare_data(ctx, deputy_file, output_file)

    try:
        # Pass ctx, deputy_file, and role_name explicitly to update_roles
        #await update_roles(ctx, output_file, role_name='Mekanisk')
        
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

async def update_roles(ctx, deputy_file: str, role_name: str):
    """
    Updates the roles of users in a Discord server based on a CSV file.

    Args:
        ctx: The command context.
        deputy_file (str): Path to the CSV file containing 'label' (name) and 'username'.
        role_name (str): The name of the role to assign.
    """
    guild = ctx.guild

    try:
        # Read the deputy file
        users = []
        with open(deputy_file, mode='r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                users.append({
                    'name': row['label'].strip(),
                    'value': row['value'].strip()
                })

        # Find the role in the guild
        role = discord.utils.get(guild.roles, name=role_name)
        if not role:
            logging.error(f"Role '{role_name}' not found in the server.")
            await ctx.send(f"Role '{role_name}' not found in the server.")
            return

        for user in users:
            # Find member by username
            member = guild.get_member_named(user['value'])
            if not member:
                logging.warning(f"User '{user['value']}' not found in the server.")
                await ctx.send(f"User '{user['value']}' not found in the server.")
                continue

            try:
                if role in member.roles:
                    logging.info(f"User '{member.display_name}' already has the role '{role_name}'. Skipping.")
                    continue

                # Check if the bot's role is higher than the user's top role
                if guild.me.top_role <= member.top_role:
                    logging.warning(f"Cannot update role for '{member.display_name}' due to hierarchy restrictions. Skipping.")
                    continue

                # Add the role
                await member.add_roles(role)
                logging.info(f"Role '{role_name}' assigned to '{member.display_name}'.")
                await ctx.send(f"Role '{role_name}' assigned to '{member.display_name}'.")

            except discord.Forbidden:
                logging.error(f"Missing permissions to assign role '{role_name}' to '{member.display_name}'.")
                await ctx.send(f"Missing permissions to assign role '{role_name}' to '{member.display_name}'.")
            except Exception as e:
                logging.error(f"An unexpected error occurred for user '{member.display_name}': {e}")
                await ctx.send(f"An unexpected error occurred for user '{member.display_name}': {e}")

    except FileNotFoundError:
        logging.error(f"File '{deputy_file}' not found.")
        await ctx.send(f"File '{deputy_file}' not found.")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        await ctx.send(f"An unexpected error occurred: {e}")

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
