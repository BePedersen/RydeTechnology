import csv
import discord
from discord.ext import commands
from discord.ui import Select, View
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to read names from a CSV file
def read_names_from_csv(file_path):
    options = []
    logging.debug(f"Attempting to read CSV file: {file_path}")
    try:
        with open(file_path, mode='r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                logging.debug(f"Processing row: {row}")
                options.append({
                    'label': row['label'].strip(),  # Assuming the CSV has a "name" column
                    'value': row['value'].strip()
                })
            logging.info(f"Read {len(options)} names from {file_path}")
    except Exception as e:
        logging.error(f"Error reading CSV {file_path}: {e}")
    return options

# Dropdown class
class NameDropdown(Select):
    def __init__(self, options):
        logging.debug(f"Initializing dropdown with options: {options}")
        super().__init__(
            placeholder="Select a name",
            options=[
                discord.SelectOption(label=opt['label'], value=opt['value'])
                for opt in options
            ],
            min_values=1,
            max_values=1  # Only allow selecting one name
        )

    async def callback(self, interaction: discord.Interaction):
        selected_name = interaction.data['values'][0]
        logging.info(f"User selected: {selected_name}")
        await interaction.response.send_message(f"You selected: {selected_name}", ephemeral=True)

# Dropdown view class
class NameDropdownView(View):
    def __init__(self, options):
        logging.debug(f"Creating dropdown view with options: {options}")
        super().__init__()
        self.add_item(NameDropdown(options))

# Bot setup
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True  # Enable the Message Content Intent
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    logging.info(f"Bot logged in as {bot.user}")

@bot.command()
async def name(ctx):
    logging.info(f"Received !name command from user: {ctx.author}")
    
    # Read names from the CSV file
    file_path = 'Data/people_on_shift_ops.csv'  # Replace with the path to your CSV file
    options = read_names_from_csv(file_path)

    if not options:
        logging.warning("No names found in the CSV file.")
        await ctx.send("No names found in the CSV file. Please check the file.")
        return

    # Log the options generated
    logging.debug(f"Dropdown options generated: {options}")

    # Create and send the dropdown menu
    view = NameDropdownView(options)
    await ctx.send("Please select a name from the dropdown:", view=view)

# Run the bot
if __name__ == "__main__":
    logging.info("Starting bot...")
    bot.run('MTI5ODcxMDI4MDcyOTI2ODMwNQ.GyeHsc.bMbQg-291WFeE3-AA55N7UTDxjc9P48DsEsYgU')
