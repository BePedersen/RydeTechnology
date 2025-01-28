import csv
import discord
from discord.ext import commands
from discord.ui import Select, View
from asyncio import TimeoutError
import random
from datetime import datetime
import logging
from .update_roles import update_roles
import asyncio

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
    return [{'label': f"{i}%", 'value': str(i)} for i in range(90, 97, 1)]

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
        # Fetch the role
        role = discord.utils.get(guild.roles, name=role_name)
        if not role:
            logging.warning(f"Role '{role_name}' not found in the server.")
            return  # Exit early if role doesn't exist

        # Remove the role from all members
        logging.info(f"Removing role '{role_name}' from all members...")
        for member in guild.members:
            if role in member.roles:
                try:
                    await member.remove_roles(role)
                    logging.info(f"Role '{role_name}' removed from '{member.display_name}'.")
                except discord.Forbidden:
                    logging.warning(f"Missing permissions to remove role '{role_name}' from '{member.display_name}'.")
                except Exception as e:
                    logging.error(f"An error occurred while removing role from '{member.display_name}': {e}")

        # Assign role to the new shift leader
        with open(skiftleder_file, mode='r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            row = next(csv_reader, None)  # Expecting a single row
            if not row or 'Skiftleder' not in row:
                logging.error(f"Skiftleder name missing in '{skiftleder_file}'.")
                return

            skiftleder_name = row['Skiftleder'].strip()
            new_leader = discord.utils.get(guild.members, display_name=skiftleder_name)
            if not new_leader:
                logging.warning(f"Shift leader '{skiftleder_name}' not found in the server.")
                return

            if guild.me.top_role <= new_leader.top_role:
                logging.warning(f"Cannot assign role to '{new_leader.display_name}' due to hierarchy restrictions.")
                return

            await new_leader.add_roles(role)
            logging.info(f"Assigned role '{role_name}' to '{new_leader.display_name}'.")

    except FileNotFoundError:
        logging.error(f"File '{skiftleder_file}' not found.")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

async def remind_send_route(ctx, selected_people):
    await asyncio.sleep(60)  # Wait for 5 minutes

    # Create a mapping of `label` to `username` (Discord IDs)
    label_to_username = {row['label']: row['username'] for row in read_csv('Data/people_on_shift_ops.csv')}

    # Mention all selected people
    mentions = " ".join([f"<{label_to_username.get(person['name'], person['name'])}>" for person in selected_people])
    reminder_message = f"{mentions} Husk å send rute!"

    await ctx.send(reminder_message)

async def remind_use_car(ctx, selected_people):
    await asyncio.sleep(15*60)  # Wait for 15 minutes

    # Create a mapping of `label` to `username` (Discord IDs)
    label_to_username = {row['label']: row['username'] for row in read_csv('Data/people_on_shift_ops.csv')}

    # Mention all selected people
    mentions = " ".join([f"<{label_to_username.get(person['name'], person['name'])}>" for person in selected_people])
    reminder_message = f"{mentions} Husk å start Use Car 🚗!"

    await ctx.send(reminder_message)

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
            try:
                selected_people.extend(
                    [
                        {
                            "name": option["label"],
                            "username": option.get("username", "Unknown")
                        }
                        for option in people_options
                        if option["value"] in interaction.data["values"]
                    ]
                )  # Extract labels and usernames for selected people

                # Write the selected people to the file
                with open("Data/Current_shift.csv", mode="w", newline="", encoding="utf-8") as file:
                    writer = csv.writer(file)
                    writer.writerow(["label", "Username"])  # Write header
                    for person in selected_people:
                        writer.writerow([person["name"], person["username"]])

                logging.info(f"Written {len(selected_people)} people to Current_shift.csv.")

                # Inform the user and proceed
                msg = await interaction.response.send_message(
                    f"You selected: {', '.join([person['name'] for person in selected_people])} (People)", ephemeral=True
                )
                bot_messages.append(msg)

                if selected_people:
                    await create_places_dropdowns()
            except Exception as e:
                logging.error(f"Error in people_callback: {e}")
                await interaction.response.send_message("An error occurred while processing your selection.", ephemeral=True)

        # Places selection callback
        async def place_callback(interaction, person):
            try:
                # Use the 'name' field of the person dictionary as the key
                person_name = person['name']
                
                # Map selected dropdown `value`s back to their human-readable `label`s
                places = [
                    next((opt['label'] for opt in places_options if f"{person_name}_{i}_{opt['value']}" == value), value)
                    for i, value in enumerate(interaction.data['values'])
                ]
                selected_places[person_name] = places  # Store the mapped labels for the selected places

                logging.debug(f"Updated selected_places: {selected_places}")

                # Respond with the correctly formatted message
                await interaction.response.send_message(
                    f"{person_name} will drive to {format_places_list(places)}", ephemeral=True
                )

                # Check if all places are assigned
                if len(selected_places) == len(selected_people):
                    logging.info("All places have been assigned. Moving to the next step.")
                    await create_additional_settings_dropdowns()
            except Exception as e:
                logging.error(f"Error in place_callback: {e}")
                await interaction.response.send_message("An error occurred while assigning places.", ephemeral=True)        
        async def create_places_dropdowns():
            dropdowns = []

            for person in selected_people:
                # Generate unique dropdown values
                person_places_options = [
                    {"label": opt["label"], "value": f"{person['name']}_{opt['value']}"}
                    for opt in places_options
                ]

                # Log the generated options
                logging.debug(f"Dropdown options for {person['name']}: {person_places_options}")

                dropdown = Dropdown(
                    placeholder=f"Where should {person['name']} drive?",
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

            async def send_final_message(comment):
                # Create a mapping of `label` to `username` (Discord IDs)
                label_to_username = {row['label']: row['username'] for row in people_options}
                
                # Map dropdown values back to labels
                value_to_label = {f"{person['name']}_{opt['value']}": opt['label'] for opt in places_options for person in selected_people}

                # Validate `person` data type and generate formatted places
                formatted_places = {
                    person['name'] if isinstance(person, dict) else person: [
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
                            f"- <{label_to_username.get(person['name'] if isinstance(person, dict) else person, person)}> "
                            f"{random.choice(['kjører', 'fikser', 'ordner', 'cleaner','redder', 'går crazy på', 'gønner', 'swiper', 'går løs på', ''])} "
                            f"{format_places_list(places)}"
                            for person, places in formatted_places.items()
                        ]
                    )
                    + "\n\n📋 **Operational Notes**:\n"
                    f"- **Vi kjører på:** {selected_percentage}%\n"
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

                # Delete previous bot messages
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

                # Overwrite the skiftleder.csv file with the current skiftleder's name
                update_skiftleder_csv('Data/skiftleder.csv', ctx.author.display_name)
                await update_skiftleder_roles(ctx)
                await update_roles(ctx, "Data/Current_shift.csv")

                # Send the final message and pin it
                final_msg = await ctx.send(shift_plan_message)
                await final_msg.pin()
                logging.info(f"Pinned the new message")
                await remind_send_route(ctx, selected_people)
                await remind_use_car(ctx, selected_people)




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
