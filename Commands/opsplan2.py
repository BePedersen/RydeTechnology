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
from functools import partial  # Added for proper callback handling

intents = discord.Intents.default()
intents.messages = True  
intents.message_content = True  
intents.guilds = True  
intents.members = True  

logging.basicConfig(level=logging.DEBUG)  

# Function to read CSV files
def read_csv(file_path):
    options = []
    logging.debug(f"Reading CSV file: {file_path}")
    try:
        with open(file_path, mode='r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            for index, row in enumerate(csv_reader):
                label = row.get('label', '').strip()
                value = row.get('value', '').strip() or f"generated_value_{index}" 
                username = row.get('username', '').strip()

                options.append({'label': label, 'value': value, 'username': username})
                logging.debug(f"Processed: Label={label}, Value={value}")
            logging.info(f"Loaded {len(options)} entries from {file_path}")
    except Exception as e:
        logging.error(f"Error reading CSV {file_path}: {e}")
    return options

def format_places_list(places):
    return f"{', '.join(places[:-1])} og {places[-1]}" if len(places) > 1 else places[0]

def weekday():
    days = ["ENDELIG MANDAG", "Tirsdag", "It’s Wednesday my dudes", "Torsdag", "Fredag!", "Lørdag", "Søndag"]
    return days[datetime.now().weekday()]

async def read_chat(ctx, prompt_message, timeout=60):
    """Prompt user input via chat"""
    await ctx.send(prompt_message)
    try:
        message = await ctx.bot.wait_for(
            'message',
            check=lambda m: m.author == ctx.author and m.channel == ctx.channel,
            timeout=timeout
        )
        return message.content
    except TimeoutError:
        return None

def update_skiftleder_csv(file_path, skiftleder_name):
    """Write current skiftleder to CSV file."""
    with open(file_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Skiftleder'])
        writer.writerow([skiftleder_name])
        logging.info(f"Skiftleder {skiftleder_name} saved to {file_path}")

class Dropdown(Select):
    def __init__(self, placeholder, options, callback, multiple=False):
        super().__init__(
            placeholder=placeholder,
            options=[discord.SelectOption(label=opt['label'], value=opt['value']) for opt in options],
            min_values=1,
            max_values=len(options) if multiple else 1  
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

async def remind_task(ctx, selected_people, delay, message):
    """Unified function to send reminders with delay."""
    await asyncio.sleep(delay)
    label_to_username = {row['label']: row['username'] for row in read_csv('Data/people_on_shift_ops.csv')}
    mentions = " ".join([f"<@{label_to_username.get(person['name'], person['name'])}>" for person in selected_people])
    await ctx.send(f"{mentions} {message}")

async def opsplan(ctx):
    try:
        people_options = read_csv('Data/people_on_shift_ops.csv')
        places_options = read_csv('Data/Bergen_areas.csv')

        selected_people = []
        selected_places = {}

        async def people_callback(interaction):
            selected_people.extend(
                [{"name": option["label"], "username": option.get("username", "Unknown")} 
                 for option in people_options if option["value"] in interaction.data["values"]]
            )
            await interaction.response.send_message(
                f"You selected: {', '.join([person['name'] for person in selected_people])}", ephemeral=True
            )
            await create_places_dropdowns()

        async def place_callback(interaction, person):
            person_name = person['name']
            selected_places[person_name] = [
                next((opt['label'] for opt in places_options if f"{person_name}_{opt['value']}" == value), value)
                for value in interaction.data['values']
            ]
            await interaction.response.send_message(
                f"{person_name} will drive to {format_places_list(selected_places[person_name])}", ephemeral=True
            )

            if len(selected_places) == len(selected_people):
                await create_final_message()

        async def create_places_dropdowns():
            dropdowns = []

            for person in selected_people:
                person_places_options = [
                    {"label": opt["label"], "value": f"{person['name']}_{opt['value']}"} for opt in places_options
                ]

                dropdown = Dropdown(
                    placeholder=f"Where should {person['name']} drive?",
                    options=person_places_options,
                    callback=partial(place_callback, person=person),
                    multiple=True
                )
                dropdowns.append(dropdown)

            # Discord allows max **5 dropdowns per View**, so we split accordingly
            max_items_per_view = 5  
            dropdown_chunks = [dropdowns[i:i + max_items_per_view] for i in range(0, len(dropdowns), max_items_per_view)]

            for i, chunk in enumerate(dropdown_chunks):
                view = View()
                for dropdown in chunk:
                    view.add_item(dropdown)  # Add only up to 5 dropdowns per View

                await ctx.send(f"Assign places for each selected person (Batch {i+1}):", view=view)
        
        async def create_final_message():
            now = datetime.now()
            date_string = now.strftime("%d.%m.%Y")
            today = weekday()
            shift_text = "🌅 Morning Shift" if 6 <= now.hour < 14 else "🌄 Evening Shift" if 14 <= now.hour < 22 else "🌠 Night Shift"

            label_to_username = {row['label']: row['username'] for row in read_csv('Data/people_on_shift_ops.csv')}

            shift_plan_message = (
                f"{shift_text} - {date_string}\n\n"
                f"**{today}**\n\n"
                f"**Shift Leader: {ctx.author.display_name}**\n\n"
                f"🚦 **Team and Areas**:\n" +
                "\n".join([
                    f"- <@{label_to_username.get(person, 'Unknown')}> will go to {format_places_list(places)}"
                    for person, places in selected_places.items()
                ]) +
                "\n\n📋 **Operational Notes**:\n"
                "🔋🔋 Battery Check: Make sure you're charged up! 🔋🔋"
            )

            await ctx.send(shift_plan_message)
            await remind_task(ctx, selected_people, 60, "Husk å sende rute!")
            await remind_task(ctx, selected_people, 15 * 60, "Husk å starte Use Car 🚗!")
            # await remind_task(ctx, selected_people, 10 * 60, "Husk å sende inn avvik på bilen!")
            if datetime.now().weekday() == 4:
                await remind_task(ctx, selected_people, 180 * 60, "Husk at bilen skal vaskes! 🚗💦")

        dropdown_options = [discord.SelectOption(label=opt['label'], value=opt['value']) for opt in people_options]
        people_dropdown = Select(placeholder="Select people", options=dropdown_options, min_values=1, max_values=len(dropdown_options))
        people_dropdown.callback = people_callback

        view = View()
        view.add_item(people_dropdown)
        await ctx.send("Please select the people:", view=view)

    except Exception as e:
        logging.error(f"Error: {e}")
        await ctx.send(f"An error occurred: {e}")