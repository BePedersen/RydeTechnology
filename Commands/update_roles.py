import csv
import discord
import logging
from discord.ext import commands

async def update_roles(ctx, csv_file_path: str, role_name: str = "Ops på jobb"):
    """
    Updates the roles of users in a Discord server based on a CSV file.

    Args:
        ctx: The command context (for sending messages and accessing the guild).
        csv_file_path (str): Path to the CSV file containing a list of names.
        role_name (str): The name of the role to assign. Defaults to "Ops på jobb".
    """
    guild = ctx.guild

    try:
        # Check if the role exists in the server
        role = discord.utils.get(guild.roles, name=role_name)
        if not role:
            logging.error(f"Role '{role_name}' not found in the server.")
            await ctx.send(f"Role '{role_name}' not found in the server.")
            return

        # Remove the role from all members
        logging.info("Removing the role from all members...")
        for member in guild.members:
            if role in member.roles:
                try:
                    await member.remove_roles(role)
                    logging.info(f"Role '{role_name}' removed from '{member.display_name}'.")
                except discord.Forbidden:
                    logging.error(f"Missing permissions to remove role '{role_name}' from '{member.display_name}'.")
                except Exception as e:
                    logging.error(f"An error occurred while removing role from '{member.display_name}': {e}")

        # Read the CSV file
        with open(csv_file_path, mode='r', encoding='utf-8') as file:
            csv_reader = csv.reader(file)
            names = [row[0].strip() for row in csv_reader]  # Assuming names are in the first column

        if not names:
            logging.error("No names found in the CSV file.")
            return

        # Assign the role to members listed in the CSV
        logging.info("Assigning roles based on the CSV file...")
        for member in guild.members:
            if member.display_name in names or member.name in names:
                if role in member.roles:
                    logging.info(f"User '{member.display_name}' already has the role '{role_name}'. Skipping.")
                else:
                    try:
                        await member.add_roles(role)
                        logging.info(f"Role '{role_name}' assigned to '{member.display_name}'.")
                    except discord.Forbidden:
                        logging.error(f"Missing permissions to assign role '{role_name}' to '{member.display_name}'.")
                    except Exception as e:
                        logging.error(f"An error occurred for '{member.display_name}': {e}")

        logging.info("Role update process completed.")

    except FileNotFoundError:
        logging.error(f"File '{csv_file_path}' not found.")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")