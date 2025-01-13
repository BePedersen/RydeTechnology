import csv
import logging
import discord

async def match_and_update(ctx, deputy_file, output_file):
    """
    Matches nicknames from Stavanger_Deputy.csv to Discord members dynamically,
    and writes updated data to the specified output file.

    Args:
        ctx: The Discord context.
        deputy_file: Path to the Stavanger_Deputy.csv file.
        output_file: Path to the output CSV file.
    """
    guild = ctx.guild  # The server (guild) where the command is executed

    # Fetch all Discord members with nicknames
    discord_members = [
        {
            "nickname": member.display_name,  # Server-specific nickname
            "user_id": str(member.id),       # Plain user ID without @
            "username": f"@{member.id}"      # User ID with @ for username
        }
        for member in guild.members
    ]
    logging.info(f"Discord members in {guild.name}: {discord_members}")

    # Read Stavanger_Deputy.csv
    deputy_data = read_csv(deputy_file)
    logging.info(f"Read {len(deputy_data)} entries from {deputy_file}.")

    # Prepare the output data
    output_data = []

    for row in deputy_data:
        nickname = row['label']  # Nickname from Stavanger_Deputy.csv
        phone = row.get('phone', '')  # Get phone if provided, otherwise empty
        matched_member = next((m for m in discord_members if m['nickname'] == nickname), None)

        # Prepare the entry
        entry = {
            'label': nickname,
            'value': matched_member['user_id'] if matched_member else 'Not matched',  # No @
            'phone': phone if phone else '',  # Leave blank if phone is not provided
            'username': matched_member['username'] if matched_member else 'Not matched'  # With @
        }
        output_data.append(entry)

    # Log the data to be written
    logging.debug(f"Data to write to {output_file}: {output_data}")

    # Write to the specified output file
    write_csv(output_file, output_data, fieldnames=['label', 'value', 'phone', 'username'])
    logging.info(f"Data written to {output_file} successfully.")

def read_csv(file_path):
    """Reads a CSV file and returns a list of dictionaries."""
    options = []
    try:
        with open(file_path, mode='r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                options.append(row)
    except Exception as e:
        logging.error(f"Error reading CSV: {e}")
    return options

def write_csv(file_path, data, fieldnames):
    """Writes data to a CSV file."""
    try:
        with open(file_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        logging.info(f"Data successfully written to {file_path}.")
    except Exception as e:
        logging.error(f"Error writing to CSV at {file_path}: {e}")
        raise
