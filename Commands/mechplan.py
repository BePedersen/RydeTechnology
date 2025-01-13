import csv
import discord
from discord.ext import commands
from discord.ui import Select, View
from asyncio import TimeoutError
import logging
from datetime import datetime

intents = discord.Intents.default()
intents.messages = True  # Allow reading messages
intents.message_content = True  # Allow access to message content
intents.guilds = True  # Allow interaction within guilds
intents.members = True  # Enable fetching member details

# Function to read CSV files
def read_csv(file_path):
    options = []
    try:
        with open(file_path, mode='r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                options.append({
                    'label': row['label'].strip(),
                    'value': row['value'].strip()
                })
    except Exception as e:
        logging.error(f"Error reading CSV {file_path}: {e}")
    return options

# Dropdown for selecting tasks or people
class Dropdown(Select):
    def __init__(self, placeholder, options, callback, multiple=False):
        super().__init__(
            placeholder=placeholder,
            options=[
                discord.SelectOption(label=opt['label'], value=opt['value'])
                for opt in options
            ],
            min_values=1,
             max_values=len(options) if len(options) < 5 else 5  # Adjust for fewer options
        )
        self.custom_callback = callback

    async def callback(self, interaction: discord.Interaction):
        try:
            await self.custom_callback(interaction)
        except Exception as e:
            logging.error(f"Error in Dropdown callback: {e}")
            try:
                await interaction.response.defer()
                await interaction.followup.send("An error occurred while processing your selection.", ephemeral=True)
            except discord.errors.NotFound:
                logging.error("Interaction response could not be sent as the interaction was not found.")

# Dropdown view for displaying selectable items
class DropdownView(View):
    def __init__(self, ctx, dropdowns):
        super().__init__()
        self.ctx = ctx
        for dropdown in dropdowns:
            self.add_item(dropdown)

# Function to read user input from chat
async def read_chat(ctx, prompt_message, timeout=60):
    await ctx.send(prompt_message)
    try:
        message = await ctx.bot.wait_for(
            'message',
            check=lambda m: m.author == ctx.author and m.channel == ctx.channel,
            timeout=timeout
        )
        return message.content
    except TimeoutError:
        await ctx.send("No response received within the time limit. Proceeding without additional input.")
        return None

# Main mechplan function
async def mechplan(ctx):
    try:
        # Load data from CSV files
        tasks_options = read_csv('Data/tasks_mech.csv')
        people_options = read_csv('Data/people_on_shift_mech.csv')

        if not tasks_options:
            await ctx.send("No tasks found in tasks_mech.csv. Please check the file.")
            return

        if not people_options:
            await ctx.send("No people found in people_on_shift_mech.csv. Please check the file.")
            return

        task_assignments = {}
        selected_tasks = []
        goal_for_day = None
        additional_comment = None

        # List to store messages sent by the bot
        bot_messages = []

        # Step 1: Ask for the goal of the day
        goal_for_day = await read_chat(ctx, "What is the goal for the day? Please type it in the chat below.")
        if not goal_for_day:
            goal_for_day = "No specific goal provided."

        # Step 2: Select tasks
        async def task_callback(interaction):
            try:
                await interaction.response.defer()  # Acknowledge the interaction immediately
                selected_task_values = interaction.data['values']
                selected_tasks.extend(selected_task_values)

                if len(selected_tasks) == len(set(selected_tasks)):
                    await assign_people_to_tasks()

            except Exception as e:
                logging.error(f"Error in task_callback: {e}")
                try:
                    await interaction.followup.send("Failed to process task selection.", ephemeral=True)
                except discord.errors.NotFound:
                    logging.error("Interaction follow-up failed as the interaction was not found.")

        dropdown = Dropdown(
            placeholder="Select tasks",
            options=tasks_options,
            callback=task_callback,
            multiple=True
        )
        view = DropdownView(ctx, [dropdown])
        msg = await ctx.send(view=view)
        bot_messages.append(msg)

        # Step 3: Assign people to tasks
        async def people_callback(task, assigned_people_values):
            assigned_people_names = [
                opt['label'] for opt in people_options if opt['value'] in assigned_people_values
            ]
            if task not in task_assignments:
                task_assignments[task] = []
            task_assignments[task].extend(assigned_people_names)

        async def assign_people_to_tasks():
            for i, task in enumerate(selected_tasks):
                task_label = next((opt['label'] for opt in tasks_options if opt['value'] == task), task)

                dropdown = Dropdown(
                    placeholder=f"Assign people for: {task_label}",
                    options=people_options,
                    callback=lambda interaction, t=task: handle_people_selection(interaction, t),
                    multiple=True
                )
                view = DropdownView(ctx, [dropdown])
                msg = await ctx.send(view=view)
                bot_messages.append(msg)

            # After all tasks, ask for additional comments
            await ask_for_additional_comment()

        async def handle_people_selection(interaction, task):
            try:
                await interaction.response.defer()  # Acknowledge the interaction immediately
                assigned_people_values = interaction.data['values']
                await people_callback(task, assigned_people_values)
            except Exception as e:
                logging.error(f"Error in handle_people_selection: {e}")
                try:
                    await interaction.followup.send("Failed to process people assignment.", ephemeral=True)
                except discord.errors.NotFound:
                    logging.error("Interaction follow-up failed as the interaction was not found.")

        # Step 4: Ask for additional comments
        async def ask_for_additional_comment():
            nonlocal additional_comment
            additional_comment = await read_chat(ctx, "If you have additional notes or instructions, please type them below.")
            await send_final_message()

        # Step 5: Send final message
        async def send_final_message():
            now = datetime.now()
            current_hour = now.hour
            date_string = now.strftime("%d.%m.%Y")

            if 6 <= current_hour < 14:
                shift_text = f"🌅 Morgenskift {date_string} 🌅"
            elif 14 <= current_hour < 22:
                shift_text = f"🌄 Kveldskift {date_string} 🌄"
            else:
                shift_text = f"🌠 Nattskift {date_string} 🌠"

            assigned_tasks = "\n\n".join(
                [
                    f"{next((opt['label'] for opt in tasks_options if opt['value'] == task), task)}: "
                    f"{', '.join(task_assignments.get(task, [])[:-1]) if len(task_assignments.get(task, [])) > 1 else ''}"
                    f"{task_assignments.get(task, [])[0] if len(task_assignments.get(task, [])) == 1 else ''}"
                    f"{' and ' + task_assignments.get(task, [])[-1] if len(task_assignments.get(task, [])) > 1 else ''}"
                    for task in selected_tasks
                ]
            )
            final_message = (
                f"{shift_text}\n\n"
                f"Skiftleder: {ctx.author.name}\n\n"
                f"\U0001F3AF Fokus for dagen: {goal_for_day}\n\n"
                f"{assigned_tasks}\n\n"
                f"**Comment**: {additional_comment or 'No additional comment'}\n\n"
                "\U0001F4CC Viktig\n\n"
                "Ikke glem å kost under pult og sjekk at det ser fint ut på verkstedet før dere går, "
                "verkstedet skal ikke ha småting liggende rundt, legg alt på plass!\n\n"
                "Husk jobs, kildesortering og legg til deler\U0001F4AA\n\n"
                "NB! Pass på at verktøyet på tavlene ligger på rett plass med riktig farge! ⚪️⚫️🔵🔴🟢🟠"
                "Det er bare å spørre meg eller andre dersom dere skulle lure på noe\U0001F60A"
            )

            # Delete all bot messages
            for msg in bot_messages:
                try:
                    await msg.delete()
                except Exception as e:
                    logging.warning(f"Failed to delete message: {e}")

            await ctx.send(final_message)

    except Exception as e:
        logging.error(f"Error in mechplan: {e}")
        await ctx.send("An error occurred while processing the mechplan.")
