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
            for index, row in enumerate(csv_reader):
                label = row.get('label', '').strip()
                value = row.get('value', '').strip() or f"generated_value_{index}"  # Generate unique value if missing
                username = row.get('username', '').strip() 

                options.append({
                    'label': label,
                    'value': value,
                    'username': username
                })
                logging.debug(f"Processed option: Label={label}, Value={value}")
            logging.info(f"Read {len(options)} names from {file_path}")
    except Exception as e:
        logging.error(f"Error reading CSV {file_path}: {e}")
    return options

# Helper to format places list with "and" between the last two cities
def format_places_list(places):
    if len(places) > 1:
        return f"{', '.join(places[:-1])} så {places[-1]}"
    return places[0]

# Generate percentage options for general usage
def generate_percentage_options():
    return [{'label': f"{i}%", 'value': str(i)} for i in range(25, 55, 5)]

# Generate percentage options for goals, ensuring they do not overlap with general percentages
def generate_goal_percentage_options():
    return [{'label': f"{i}%", 'value': str(i)} for i in range(85, 97, 1)]

# Generate days inactive options
def generate_days_options():
    return [{'label': f"{i / 2:.1f} days", 'value': f"{i / 2:.1f}"} for i in range(1, 9)]

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

def update_skiftleder_csv(file_path, skiftleder_name):
    """Creates or overwrites the skiftleder.csv file with the current skiftleder name."""
    with open(file_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        
        # Write the header
        writer.writerow(['Skiftleder'])
        
        # Write the current skiftleder's name
        writer.writerow([skiftleder_name])
        logging.info(f"Skiftleder {skiftleder_name} written to {file_path}")



async def update_skiftleder_roles(ctx):
  
    guild = ctx.guild
    skiftleder_file = 'Data/skiftleder.csv'
    role_name = "Nivel"
    try:
        # Read the Skiftleder file
        with open(skiftleder_file, mode='r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            # Expecting only one row for Skiftleder
            row = next(csv_reader, None)
            if not row:
                logging.error(f"File '{skiftleder_file}' is empty or invalid.")
                await ctx.send(f"File '{skiftleder_file}' is empty or invalid.")
                return
            
            # Extract the name of the Skiftleder
            skiftleder_name = row.get("Skiftleder", "").strip()
            if not skiftleder_name:
                logging.error(f"Skiftleder name not found in file '{skiftleder_file}'.")
                await ctx.send(f"Skiftleder name not found in file '{skiftleder_file}'.")
                return

        # Find the role in the guild
        role = discord.utils.get(guild.roles, name=role_name)
        if not role:
            logging.error(f"Role '{role_name}' not found in the server.")
            await ctx.send(f"Role '{role_name}' not found in the server.")
            return

        # Find the member by name
        member = discord.utils.get(guild.members, display_name=skiftleder_name)
        if not member:
            logging.warning(f"Skiftleder '{skiftleder_name}' not found in the server.")
            await ctx.send(f"Skiftleder '{skiftleder_name}' not found in the server.")
            return

        try:
            # Check if the bot's role is higher than the user's top role
            if guild.me.top_role <= member.top_role:
                logging.warning(f"Cannot update role for '{member.display_name}' due to hierarchy restrictions.")
                await ctx.send(f"Cannot update role for '{member.display_name}' due to hierarchy restrictions.")
                return

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
        logging.error(f"File '{skiftleder_file}' not found.")
        await ctx.send(f"File '{skiftleder_file}' not found.")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        await ctx.send(f"An unexpected error occurred: {e}")



# The opsplan function
async def opsplan(ctx):
    try:
        # Load data from CSV files
        people_options = read_csv('Data/people_on_shift_ops.csv')
        places_options = read_csv('Data/Bergen_areas.csv')

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
            # Map selected dropdown `value`s back to their human-readable `label`s
            places = [
                next((opt['label'] for opt in places_options if f"{person}_{i}_{opt['value']}" == value), value)
                for i, value in enumerate(interaction.data['values'])
            ]
            selected_places[person] = places  # Store the mapped labels for the selected places

            logging.debug(f"Updated selected_places: {selected_places}")

            # Respond with the correctly formatted message
            await interaction.response.send_message(
                f"{person} will drive to {format_places_list(places)}", ephemeral=True
            )

            # Check if all places are assigned
            if len(selected_places) == len(selected_people):
                logging.info("All places have been assigned. Moving to the next step.")
                await ctx.send("Drivers and places have been assigned. Now, configure additional settings.")
                await create_additional_settings_dropdowns()
        
        async def create_places_dropdowns():
            dropdowns = []

            for person in selected_people:
                # Generate unique dropdown values
                person_places_options = [
                    {"label": opt["label"], "value": f"{person}_{opt['value']}"}
                    for opt in places_options
                ]

                # Log the generated options
                logging.debug(f"Dropdown options for {person}: {person_places_options}")

                dropdown = Dropdown(
                    placeholder=f"Where should {person} drive?",
                    options=person_places_options,
                    callback=lambda interaction, p=person: place_callback(interaction, p),
                    multiple=True
                )
                dropdowns.append(dropdown)

            if not dropdowns:
                logging.error("No dropdowns created. Check selected_people and places_options.")
                await ctx.send("No places available to assign. Please try again.")
                return

            view = DropdownView(ctx, dropdowns)
            msg = await ctx.send("Assign places for each selected person:", view=view)
            bot_messages.append(msg)
            
        # Create dropdowns for additional settings
        async def create_additional_settings_dropdowns():
            nonlocal selected_percentage, selected_goal_percentage, selected_days_inactive

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
                selected_days_inactive = float(interaction.data['values'][0])
                msg = await interaction.response.send_message(f"Selected days inactive: {selected_days_inactive} days", ephemeral=True)
                bot_messages.append(msg)

                # Once all settings are configured, prompt for additional comments
                additional_comment = await read_chat(
                    ctx,"If you have additional notes or instructions, please type them in the chat below. You have 60 seconds:"
                )
                await send_final_message(additional_comment)

            # Final message function
            async def send_final_message(comment):

                # Create a mapping of `label` to `username` (Discord IDs)
                label_to_username = {row['label']: row['username'] for row in people_options}
                
                # Map dropdown values back to labels
                value_to_label = {f"{person}_{opt['value']}": opt['label'] for opt in places_options for person in selected_places}

                formatted_places = {
                    person: [
                        value_to_label.get(value, value)  # Use the label if found, fallback to value
                        for value in places
                    ]
                    for person, places in selected_places.items()
                }

                logging.debug(f"Formatted places for final message: {formatted_places}")

                now = datetime.now()
                date_string = now.strftime("%d.%m.%Y")

                shift_text = (
                    f"🌅 Tidligskift {date_string} 🌅" if 6 <= now.hour < 14 else
                    f"🌄 Kveldskift {date_string} 🌄" if 14 <= now.hour < 22 else
                    f"🌠 Natteskift {date_string} 🌠"
                )

                shift_plan_message = (
                    f"{shift_text}\n\n"
                    f"**Skiftleder: {ctx.author.display_name}**\n\n"
                    f" **Goal** \n"
                    f"- Availability: 🎯 {selected_goal_percentage}%\n\n"
                    "🚦 **Team and Areas**:\n"
                    + "\n".join(
                        [
                            f"- <{label_to_username.get(person, person)}> {random.choice(['kjører', 'fikser', 'ordner', 'cleaner','redder', 'går crazy på', 'gønner', 'swiper', 'går løs på', ''])} {format_places_list(places)}"
                            for person, places in formatted_places.items()
                        ]
                    )
                    + "\n\n📋 **Operational Notes**:\n"
                    f"- **Vi kjører på:**: {selected_percentage }%\n"                    
                    f"- **Inaktive**: {selected_days_inactive} days\n"
                    f"- **Klynger**: {selected_percentage + 10}% i klynger\n"
                    f"- **Redeploy**: {selected_percentage + 15}% på inactive\n\n"
                    "**Reminders:**\n"
                    "**Husk Use Car🚗**\n"
                    "**God QC**\n"
                    "**Fiks Nivler innen en time**\n"
                    "**Ta med deploys fra lageret**\n\n"
                    "**If you have any questions:**\n"
                    "Contact skiftleder over Discord through the voice channel or tag skiftleder and write a message in this chat.\n\n"
                    f" **Comment**:\n{comment or 'No additional comment'}\n\n"
                    "🔋🔋 **Battery Check** 🔋🔋 \n"
                    "Make sure you're charged up and ready to go! \n"
                )

                for msg in bot_messages:
                    try:
                        await msg.delete()
                    except Exception as e:
                        logging.warning(f"Failed to delete message: {e}")

                # Fetch pinned messages and unpin the previous one, if any
                pinned_messages = await ctx.channel.pins()
                for pinned_msg in pinned_messages:
                    if pinned_msg.author == ctx.me:  # Check if the pinned message belongs to the bot
                        await pinned_msg.unpin()
                        logging.info(f"Unpinned messages")

                # Send the final message and pin it
                final_msg = await ctx.send(shift_plan_message)
                await final_msg.pin()
                logging.info(f"Pinned the new message")

                # Overwrite the skiftleder.csv file with the current skiftleder's name
                update_skiftleder_csv('Data/skiftleder.csv', ctx.author.display_name)
                await update_skiftleder_roles(ctx)


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
