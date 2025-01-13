import csv
import discord
from discord.ext import commands
from discord.ui import Select, View
from asyncio import TimeoutError
import random
from datetime import datetime
import logging

intents = discord.Intents.default()
intents.messages = True  # Allow reading messages
intents.message_content = True  # Allow access to message content
intents.guilds = True  # Allow interaction within guilds
intents.members = True  # Enable fetching member details

# Configure logging
logging.basicConfig(level=logging.DEBUG)  # Set to DEBUG to see all log messages

# Function to read CSV
# Function to read names from a CSV file
def read_csv(file_path):
    options = []
    logging.debug(f"Attempting to read CSV file: {file_path}")
    try:
        with open(file_path, mode='r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                label = row.get('label', '').strip()
                value = row.get('value', '').strip()
                phone = row.get('phone', '').strip()  # Add phone reading


                # Ensure label and value meet the 5-character minimum requirement
                if len(label) < 5:
                    label = label.ljust(5, '_')  # Pad with underscores if too short
                if len(value) < 5:
                    value = value.ljust(5, '_')  # Pad with underscores if too short

                options.append({
                    'label': label,
                    'value': value,
                    'phone': phone
                })
                logging.debug(f"Processed option: Label={label}, Value={value}")
            logging.info(f"Read {len(options)} names from {file_path}")
    except Exception as e:
        logging.error(f"Error reading CSV {file_path}: {e}")
    return options

# Helper to format places list with "and" between the last two cities
def format_places_list(places):
    if len(places) > 1:
        return f"{', '.join(places[:-1])} and {places[-1]}"
    return places[0]

# Generate percentage options for general usage
def generate_percentage_options():
    return [{'label': f"{i}%", 'value': str(i)} for i in range(20, 45, 5)]

# Generate percentage options for goals, ensuring they do not overlap with general percentages
def generate_goal_percentage_options():
    return [{'label': f"{i}%", 'value': str(i)} for i in range(85, 97, 1)]

# Generate days inactive options
def generate_days_options():
    return [{'label': f"{i} days", 'value': str(i)} for i in range(1, 6, 1)]

# Dropdown and View classes
class Dropdown(Select):
    def __init__(self, placeholder, options, callback, multiple=False):
        super().__init__(
            placeholder=placeholder,
            options=[
                discord.SelectOption(label=opt['label'], value=opt['value'])
                for opt in options
            ],
            min_values=1,
            max_values=len(options) if multiple else 1  # Allow multiple selections if `multiple=True`
        )
        self.custom_callback = callback

    async def callback(self, interaction: discord.Interaction):
        await self.custom_callback(interaction)

class DropdownView(View):
    def __init__(self, ctx, dropdowns):
        super().__init__()
        self.ctx = ctx
        for dropdown in dropdowns:
            self.add_item(dropdown)

# Function to read chat input
async def read_chat(ctx, prompt_message, timeout=60):
    """Prompt the user to input additional data via chat."""
    await ctx.send(prompt_message)
    try:
        message = await ctx.bot.wait_for(
            'message',
            check=lambda m: m.author == ctx.author and m.channel == ctx.channel,
            timeout=timeout
        )
        return message.content
    except TimeoutError:
        msg = await ctx.send("No response received within the time limit. Skipping this step.")
        return None

# The opsplan function
async def opsplan(ctx):
    try:
        # Load data from CSV files
        people_options = read_csv('Data/people_on_shift_ops.csv')
        places_options = read_csv('Data/Stavanger.csv')

        selected_people = []
        selected_places = {}
        selected_percentage = None
        selected_goal_percentage = None
        selected_days_inactive = None

        # List to store messages sent by the bot
        bot_messages = []

        async def people_callback(interaction):
            selected_people.extend(
                [option['label'] for option in people_options if option['value'] in interaction.data['values']]
            )  # Extract only labels for selected people
            msg = await interaction.response.send_message(
                f"You selected: {', '.join(selected_people)} (People)", ephemeral=True
            )
            bot_messages.append(msg)

            if selected_people:
                msg = await ctx.send("Now, assign places for each selected person.")
                bot_messages.append(msg)
                await create_places_dropdowns()

        # Places selection callback
        async def place_callback(interaction, person):
            places = [value for value in interaction.data['values']]  # Extract only city names
            selected_places[person] = places

            msg = await interaction.response.send_message(f"{person} will drive to {format_places_list(places)}", ephemeral=True)
            bot_messages.append(msg)

            # Check if all places are assigned
            if len(selected_places) == len(selected_people):
                msg = await ctx.send("Drivers and places have been assigned. Now, configure additional settings.")
                bot_messages.append(msg)
                await create_additional_settings_dropdowns()

        # Create dropdowns for each person
        async def create_places_dropdowns():
            dropdowns = []
            for person in selected_people:
                person_places_options = [
                    {
                        'label': opt['label'],  # City name
                        'value': opt['value']  # Unique value for the city
                    }
                    for opt in places_options
                ]

                dropdown = Dropdown(
                    placeholder=f"Where should {person} drive?",
                    options=person_places_options,
                    callback=lambda interaction, p=person: place_callback(interaction, p),
                    multiple=True  # Allow multiple places to be selected
                )
                dropdowns.append(dropdown)

            # Create a view with all place dropdowns
            view = DropdownView(ctx, dropdowns)
            msg = await ctx.send("Assign places for each selected person:", view=view)
            bot_messages.append(msg)

        # Create dropdowns for additional settings
        async def create_additional_settings_dropdowns():
            nonlocal selected_percentage, selected_goal_percentage, selected_days_inactive
            additional_comment = None  # To store the user's additional comment
            random_phrases = ["kjører til", "fikser", "order"]  # Random action phrases

            async def percentage_callback(interaction):
                nonlocal selected_percentage
                selected_percentage = int(interaction.data['values'][0])
                msg = await interaction.response.send_message(f"Selected percentage: {selected_percentage}%", ephemeral=True)
                bot_messages.append(msg)
                
            async def goal_percentage_callback(interaction):
                nonlocal selected_goal_percentage
                selected_goal_percentage = int(interaction.data['values'][0])
                msg = await interaction.response.send_message(f"Selected goal percentage: {selected_goal_percentage}%", ephemeral=True)
                bot_messages.append(msg)

            async def days_inactive_callback(interaction):
                nonlocal selected_days_inactive
                selected_days_inactive = int(interaction.data['values'][0])
                msg = await interaction.response.send_message(f"Selected days inactive: {selected_days_inactive} days", ephemeral=True)
                bot_messages.append(msg)

                # Once all settings are configured, prompt for additional comments
                additional_comment = await read_chat(
                    ctx,"If you have additional notes or instructions, please type them in the chat below. You have 60 seconds:"
                )
                await send_final_message(additional_comment)

            # Final message function
            async def send_final_message(comment):
                # Match names to phone numbers
                person_details = {person['label']: person['phone'] for person in people_options}

                now = datetime.now()
                current_hour = now.hour
                date_string = now.strftime("%d.%m.%Y")

                if 6 <= current_hour < 14:
                    shift_text = f"🌅 Morgenskift {date_string} 🌅"
                elif 14 <= current_hour < 22:
                    shift_text = f"🌄 Kveldskift {date_string} 🌄"
                else:
                    shift_text = f"🌠 Nattskift {date_string} 🌠"

                shift_plan_message = (
                    f"{shift_text}\n\n"
                    f"Skiftleder: {ctx.author.name}\n\n"
                    f" **Goal** \n"
                    f"- Availability: 🎯 {selected_goal_percentage}%\n\n"
                    "🚦 **Team and Areas**:\n"
                    + "\n".join(
                        [
                            f"- {person} {random.choice(random_phrases)} {format_places_list(places)}"
                            for person, places in selected_places.items()  # Use the list of labels (people)
                        ]
                    )
                    + "\n\n🕰 **Operational Notes**:\n"
                    f"- **Inactivity**: 🔄 {selected_percentage}% inactive for {selected_days_inactive} days.\n"
                    f"- **Clusters**: {selected_percentage + 10}% in clusters.\n"
                    f"- **Redeployment**: 🔽 {selected_percentage + 15}% on inactives.\n\n"
                    "📞 **Contact**:\n"
                    + "\n".join(
                    [
                        f"• {name}: {phone}"
                        for name, phone in person_details.items()
                        if name in selected_places.keys()
                    ]
                    )
                    + f"\n\n **Comment**:\n{comment or 'No additional comment'}\n\n"
                    "🔋🔋 **Battery Check** 🔋🔋 \n"
                    "Make sure you're charged up and ready to go! \n"
                )

                # Delete all bot messages
                for msg in bot_messages:
                    try:
                        await msg.delete()
                    except Exception as e:
                        logging.warning(f"Failed to delete message: {e}")

                await ctx.send(shift_plan_message)

            # Create dropdowns
            percentage_dropdown = Dropdown(
                placeholder="Select percentage",
                options=generate_percentage_options(),
                callback=percentage_callback,
                multiple=False  # Explicitly specify only one answer
            )

            goal_percentage_dropdown = Dropdown(
                placeholder="Select goal percentage",
                options=generate_goal_percentage_options(),
                callback=goal_percentage_callback,
                multiple=False  # Explicitly specify only one answer
            )

            days_inactive_dropdown = Dropdown(
                placeholder="Select days inactive",
                options=generate_days_options(),
                callback=days_inactive_callback,
                multiple=False  # Explicitly specify only one answer
            )

            # Create a view with the dropdowns
            view = DropdownView(ctx, [percentage_dropdown, goal_percentage_dropdown, days_inactive_dropdown])
            msg = await ctx.send("Please configure additional settings using the dropdowns below:", view=view)
            bot_messages.append(msg)

        dropdown_options = [
            discord.SelectOption(
                label=opt['label'],
                value=opt['value'],
            )
            for opt in people_options
        ]

        # Log the processed dropdown options
        logging.debug(f"Sanitized dropdown options: {dropdown_options}")

        # Create the dropdown
        people_dropdown = Select(
            placeholder="Select people",
            options=dropdown_options,  # Pass sanitized options
            min_values=1,
            max_values=len(dropdown_options) if len(dropdown_options) > 0 else 1,
        )
        people_dropdown.callback = people_callback  # Attach the callback

        # Create the view and add the dropdown
        view = View()
        view.add_item(people_dropdown)
        msg = await ctx.send("Please select the people first:", view=view)
        bot_messages.append(msg)

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        msg = await ctx.send(f"An error occurred: {e}")
        bot_messages.append(msg)
