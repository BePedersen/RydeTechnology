import discord
import csv
import random
from discord.ui import Select, View
from Commands import functions

# List of words
random_words = ['redder', 'fikser', 'støvsuger', 'ordner', 'steller']

# Function to read CSV
def read_csv(file_path):
    options = []
    try:
        with open(file_path, mode='r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                options.append({
                    'label': row['label'], 
                    'value': row['value'],
                    'phone': row.get('phone', 'Not provided'),
                    'username': row.get('username', 'Not provided')
                })
    except Exception as e:
        print(f"Error reading CSV: {e}")
    return options

# Function to create dropdown for people
def create_people_dropdown(options):
    select = Select(
        placeholder="Select people",
        options=[discord.SelectOption(label=person['label'], value=person['value']) for person in options]
    )
    return select

# Function to create dropdown for places
def create_place_dropdown(options, placeholder):
    select = Select(
        placeholder=placeholder,
        options=[discord.SelectOption(label=place, value=place) for place in options]
    )
    return select

# The main function for opsplan command
async def opsplan(ctx):
    try:
        # Read CSVs for people and places
        people_options = read_csv('data/people_on_shift.csv')
        places_options = read_csv('data/places.csv')

        # Create dropdown for people
        people_dropdown = create_people_dropdown(people_options)
        places_dropdown = create_place_dropdown([place['label'] for place in places_options], "Select place")

        # Create a view to hold the dropdowns
        view = View()
        view.add_item(people_dropdown)
        view.add_item(places_dropdown)

        # Wait for the user to select
        await ctx.send('Please select the people and places:', view=view)

        # Placeholder logic for user selections
        await ctx.send("Bot is ready to handle selection and plan assignments.")

    except Exception as e:
        await ctx.send(f"An error occurred: {e}")
