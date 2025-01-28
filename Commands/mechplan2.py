import csv
import discord
from discord.ext import commands
from discord.ui import Select, View
from asyncio import TimeoutError
import random
from datetime import datetime
import logging
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

def weekday():
    days = ["ENDElLIG MANDAG", "Tirsdag", "It´s wedensday my dudes", "Torsdag", "For det er fredag min venn", "Lørdag", "Søndag"]
    today = datetime.now().weekday()  # Gir en verdi mellom 0 (Mandag) og 6 (Søndag)
    return days[today]



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
async def mechplan(ctx):
    try:
        # Load data from CSV files
        people_options = read_csv('Data/people_on_shift_mech.csv')
        places_options = read_csv('Data/tasks_mech.csv')

        selected_people = []
        selected_places = {}

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
                await interaction.response.defer()  # Acknowledge the interaction
                person_name = person['name']

                # Map selected dropdown values to labels
                places = [
                    next((opt['label'] for opt in places_options if f"{person_name}_{opt['value']}" == value), value)
                    for value in interaction.data['values']
                ]
                selected_places[person_name] = places

                logging.debug(f"Updated selected_places: {selected_places}")

                # Check if all places are assigned
                if len(selected_places) == len(selected_people):
                    logging.info("All places have been assigned. Proceeding to the next step.")
                    await create_additional_settings_dropdowns()

            except Exception as e:
                logging.error(f"Error in place_callback: {e}")
                try:
                    await interaction.followup.send("An error occurred while assigning places.", ephemeral=True)
                except discord.errors.InteractionResponded:
                    logging.error("Interaction already responded.")                

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
                    placeholder=f"{person['name']}",
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
            msg = await ctx.send("Fordel ansvar for hver valgte person:", view=view)
            bot_messages.append(msg)
        
        
        # Create dropdowns for additional settings
        async def create_additional_settings_dropdowns():
            try:
                # Get today's goal
                goal = await get_todays_goal(ctx)

                # Prompt for additional comments
                additional_comment = await read_chat(
                    ctx, "If you have additional notes or instructions, please type them in the chat below. You have 60 seconds:"
                )

                # Send the final message with both goal and comment
                await send_final_message(goal, additional_comment)
            except Exception as e:
                logging.error(f"Error in create_additional_settings_dropdowns: {e}")
                await ctx.send("An error occurred while setting additional settings.")

        async def get_todays_goal(ctx):
            goal = await read_chat(ctx, "Please enter today's goal. You have 60 seconds:")
            return goal

        async def send_final_message(goal, comment):
            # Create a mapping of `label` to `username` (Discord IDs)
            label_to_username = {row['label']: row['username'] for row in people_options}

            # Map dropdown values back to labels
            value_to_label = {f"{person['name']}_{opt['value']}": opt['label'] for opt in places_options for person in selected_people}

            # Generate formatted places
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
            today = weekday()
            shift_text = (
                f"🌅 Tidligskift {date_string} 🌅" if 6 <= now.hour < 14 else
                f"🌄 Kveldskift {date_string} 🌄" if 14 <= now.hour < 22 else
                f"🌠 Natteskift {date_string} 🌠"
            )

            shift_plan_message = (
                f"{shift_text}\n"
                f"**{today}**\n\n"
                f"Today's Goal: {goal}\n\n"
                f"**Skiftleder: {ctx.author.display_name}**\n\n"
                "📋**Dagens Ansvarsområder:**:\n"
                + "\n".join(
                    [
                        f"- <{label_to_username.get(person['name'] if isinstance(person, dict) else person, person)}> "
                        f"{format_places_list(places)}"
                        for person, places in formatted_places.items()
                    ]
                )
                + "\n\n"
                f" **Comment**:\n{comment or 'No additional comment'}\n\n"
                "\U0001F4CC **Viktig**\n\n"
                "**Ikke glem å kost under pult og sjekk at det ser fint ut på verkstedet før du går**\n"
                "**Verkstedet skal ikke ha småting liggende rundt, legg alt på plass!**\n"
                "**Det skal aldri være batts inne i lageret når alle har gått**\n\n"
                "**Hvis har ansvar for rydding av pauserom eller mechstasjon, hå ned med avfall om nødvendig**\n"
                "**Husk å skru av alle ovner når du går**\n"
                "**Husk jobs, kildesortering og legg til deler**\n\n"
                "**Det er bare å spørre skiftleder eller andre dersom dere skulle lure på noe**"
            )

            # Delete previous bot messages
            for msg in bot_messages:
                try:                        
                    await msg.delete()
                except Exception as e:
                    logging.warning(f"Failed to delete message: {e}")

            # Unpin old messages and pin the new one
            pinned_messages = await ctx.channel.pins()
            for pinned_msg in pinned_messages:
                if pinned_msg.author == ctx.me:
                    await pinned_msg.unpin()

            # Send and pin the final message
            final_msg = await ctx.send(shift_plan_message)
            await final_msg.pin()
            logging.info("Pinned the new message.")

        dropdown_options = [
            discord.SelectOption(
                label=opt['label'],
                value=opt['value'],
            )
            for opt in people_options
        ]


        # Create the dropdown
        people_dropdown = Select(
            placeholder="Velgt ansatte",
            options=dropdown_options,  # Pass sanitized options
            min_values=1,
            max_values=len(dropdown_options) if len(dropdown_options) > 0 else 1,
        )
        people_dropdown.callback = people_callback  # Attach the callback

        # Create the view and add the dropdown
        view = View()
        view.add_item(people_dropdown)
        msg = await ctx.send("Vennligst velg ansatte:", view=view)
        bot_messages.append(msg)

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        msg = await ctx.send(f"An error occurred: {e}")
        bot_messages.append(msg)
