import csv
import discord
from discord.ext import commands
from discord.ui import Select, View
from asyncio import TimeoutError
import random
from datetime import datetime

# Function to read CSV
def read_csv(file_path):
    options = []
    try:
        with open(file_path, mode='r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                options.append({
                    'label': row['label'],        # Person's name
                    'value': row['value'],        # Identifier or shift code
                    'phone': row.get('phone', 'Not provided'),  # Phone number
                })
    except Exception as e:
        print(f"Error reading CSV: {e}")
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
            options=[discord.SelectOption(label=opt['label'], value=opt['value']) for opt in options],
            min_values=1,
            max_values=5 if multiple else 1  # Allow up to 5 selections
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
        await ctx.send("No response received within the time limit. Skipping this step.")
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

        # People selection callback
        async def people_callback(interaction):
            selected_people.extend(interaction.data['values'])
            await interaction.response.send_message(f"You selected: {', '.join(selected_people)} (People)", ephemeral=True)

            if selected_people:
                await ctx.send("Now, assign places for each selected person.")
                await create_places_dropdowns()

        # Places selection callback
        async def place_callback(interaction, person):
            places = [value for value in interaction.data['values']]  # Extract only city names
            selected_places[person] = places
            await interaction.response.send_message(f"{person} will drive to {format_places_list(places)}", ephemeral=True)

            # Check if all places are assigned
            if len(selected_places) == len(selected_people):
                await ctx.send("Drivers and places have been assigned. Now, configure additional settings.")
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
            await ctx.send("Assign places for each selected person:", view=view)

        # Create dropdowns for additional settings
        async def create_additional_settings_dropdowns():
            nonlocal selected_percentage, selected_goal_percentage, selected_days_inactive
            additional_comment = None  # To store the user's additional comment
            random_phrases = ["kjører til", "fikser", "order"]  # Random action phrases

            async def percentage_callback(interaction):
                nonlocal selected_percentage
                selected_percentage = int(interaction.data['values'][0])
                await interaction.response.send_message(f"Selected percentage: {selected_percentage}%", ephemeral=True)

            async def goal_percentage_callback(interaction):
                nonlocal selected_goal_percentage
                selected_goal_percentage = int(interaction.data['values'][0])
                await interaction.response.send_message(f"Selected goal percentage: {selected_goal_percentage}%", ephemeral=True)

            async def days_inactive_callback(interaction):
                nonlocal selected_days_inactive
                selected_days_inactive = int(interaction.data['values'][0])
                await interaction.response.send_message(f"Selected days inactive: {selected_days_inactive} days", ephemeral=True)

                # Once all settings are configured, prompt for additional comments
                additional_comment = await read_chat(
                    ctx,
                    "If you have additional notes or instructions, please type them in the chat below. You have 60 seconds:"
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
                            for person, places in selected_places.items()
                        ]
                    )
                    + "\n\n📊 **Operational Notes**:\n"
                    f"- **Inactivity**: 🔄 {selected_percentage}% inactive for {selected_days_inactive} days.\n"
                    f"- **Clusters**: {selected_percentage + 10}% in clusters.\n"
                    f"- **Redeployment**: 📉 {selected_percentage + 15}% on inactives.\n\n"
                    "📞 **Contact**:\n"
                    + "\n".join(
                        [
                            f"• {name}: {phone}"
                            for name, phone in person_details.items()
                            if name in selected_places.keys()
                        ]
                    )
                    + f"\n\n **Comment**:\n{comment or 'No additional comment'}\n\n"
                    "🪫🪫 **Battery Check** 🔋🔋 \n"
                    "Make sure you're charged up and ready to go! \n"
                )
                await ctx.send(shift_plan_message)

            # Create dropdowns
            percentage_dropdown = Dropdown(
                placeholder="Select percentage",
                options=generate_percentage_options(),
                callback=percentage_callback
            )

            goal_percentage_dropdown = Dropdown(
                placeholder="Select goal percentage",
                options=generate_goal_percentage_options(),
                callback=goal_percentage_callback
            )

            days_inactive_dropdown = Dropdown(
                placeholder="Select days inactive",
                options=generate_days_options(),
                callback=days_inactive_callback
            )

            # Create a view with the dropdowns
            view = DropdownView(ctx, [percentage_dropdown, goal_percentage_dropdown, days_inactive_dropdown])
            await ctx.send("Please configure additional settings using the dropdowns below:", view=view)

        # Create a dropdown for selecting people
        people_dropdown = Dropdown(
            "Select people",
            [{'label': opt['label'], 'value': opt['label']} for opt in people_options],
            people_callback,
            multiple=True
        )
        view = DropdownView(ctx, [people_dropdown])
        await ctx.send("Please select the people first:", view=view)

    except Exception as e:
        await ctx.send(f"An error occurred: {e}")
