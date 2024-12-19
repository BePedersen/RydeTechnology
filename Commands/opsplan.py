import csv
import discord
from discord.ui import Select, View

# Function to read CSV
def read_csv(file_path):
    options = []
    try:
        with open(file_path, mode='r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                options.append({
                    'label': row['label'],
                    'value': row['label'],  # Ensure value matches label for simplicity
                    'phone': row.get('phone', 'Not provided'),
                    'username': row.get('username', 'Not provided'),
                })
    except Exception as e:
        print(f"Error reading CSV: {e}")
    return options

# Generate percentage options
def generate_percentage_options():
    return [{'label': f"{i}%", 'value': str(i)} for i in range(0, 101, 10)]

# Generate days inactive options
def generate_days_options():
    return [{'label': f"{i} days", 'value': str(i)} for i in range(0, 31, 5)]

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

# The opsplan function
async def opsplan(ctx):
    try:
        # Load data from CSV files
        people_options = read_csv('Deputy/people_on_shift.csv')
        places_options = read_csv('Data/Stavanger.csv')

        selected_people = []
        selected_places = {}

        # People selection callback
        async def people_callback(interaction):
            selected_people.extend(interaction.data['values'])
            await interaction.response.send_message(f"You selected: {', '.join(selected_people)} (People)", ephemeral=True)

            if selected_people:
                await ctx.send("Now, assign places for each selected person.")
                await create_places_dropdowns()

        # Places selection callback
        async def place_callback(interaction, person):
            places = interaction.data['values']
            selected_places[person] = places
            await interaction.response.send_message(f"{person} will drive to {', '.join(places)}", ephemeral=True)

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
                        'label': opt['label'],
                        'value': f"{opt['value']}_{person}"  # Ensure unique values
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
            # Percentage selection callback
            async def percentage_callback(interaction):
                selected_percentage = interaction.data['values'][0]
                await interaction.response.send_message(f"Selected percentage: {selected_percentage}%", ephemeral=True)

            # Goal percentage selection callback
            async def goal_percentage_callback(interaction):
                selected_goal_percentage = interaction.data['values'][0]
                await interaction.response.send_message(f"Selected goal percentage: {selected_goal_percentage}%", ephemeral=True)

            # Days inactive selection callback
            async def days_inactive_callback(interaction):
                selected_days = interaction.data['values'][0]
                await interaction.response.send_message(f"Selected days inactive: {selected_days} days", ephemeral=True)

            # Create dropdowns
            percentage_dropdown = Dropdown(
                placeholder="Select percentage",
                options=generate_percentage_options(),
                callback=percentage_callback
            )

            goal_percentage_dropdown = Dropdown(
                placeholder="Select goal percentage",
                options=generate_percentage_options(),
                callback=goal_percentage_callback
            )

            days_inactive_dropdown = Dropdown(
                placeholder="Select days inactive",
                options=generate_days_options(),
                callback=days_inactive_callback
            )

            # Create a view with the additional settings dropdowns
            view = DropdownView(ctx, [percentage_dropdown, goal_percentage_dropdown, days_inactive_dropdown])
            await ctx.send("Please configure additional settings using the dropdowns below:", view=view)

        # Create a dropdown for selecting people
        people_dropdown = Dropdown("Select people", people_options, people_callback, multiple=True)

        # Create a view with the people dropdown
        view = DropdownView(ctx, [people_dropdown])

        # Send the message for the first selection
        await ctx.send("Please select the people first:", view=view)

    except Exception as e:
        await ctx.send(f"An error occurred: {e}")
