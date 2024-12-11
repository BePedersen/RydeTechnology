import random
from discord.ui import Select, View, SelectOption
from Commands import functions
import discord
import csv

def run():
    # List of words
    random_words = ['redder', 'fikser', 'støvsuger', 'ordner', 'steller']
    percentage_list =[30,35,40,45]
    goalpercentage_list = [80,82,84,86,88,90,91,92,93,94,95,96,97]
    daysinactive_list = [1,2,3,4]

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
            options=[SelectOption(label=person['label'], value=person['value']) for person in options],
        )
        return select

    # Function to create dropdown for places
    def create_place_dropdown(options):
        select = Select(
            placeholder="Select a place",
            options=[SelectOption(label=place, value=place) for place in options],
        )
        return select
    
    def create_percentage_dropdown(options):
        select = Select(
            placeholder="Select a percentage",
            options=[SelectOption(label=percentage, value=percentage) for percentage in options],
        )
        return select
    
    def create_goalpercentage_dropdown(options, ):
        select = Select(
            placeholder="Select a goal percentage",
            options=[SelectOption(label=goalpercentage, value=goalpercentage) for goalpercentage in options],
        )
        return select
    
    def create_daysinnactive_dropdown(options):
        select = Select(
            placeholder="Select how many days inactive",
            options=[SelectOption(label=daysinactive, value=daysinactive) for daysinactive in options],
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
            places_dropdown = create_place_dropdown([place['label'] for place in places_options])
            percentage_dropdown = create_percentage_dropdown(percentage_list)
            goalpercentage_dropdown = create_percentage_dropdown(goalpercentage_list)
            daysinactive_dropdown = create_daysinnactive_dropdown(daysinactive_list)

            # Create a view to hold the dropdowns
            view = View()
            view.add_item(people_dropdown)
            view.add_item(places_dropdown)
            view.add_item(percentage_dropdown)
            view.add_item(goalpercentage_dropdown)
            view.add_item(daysinactive_dropdown)

            # Wait for the user to select
            await ctx.send('Please select the people and places:', view=view)

            # Placeholder logic for user selections
            await ctx.send("Bot is ready to handle selection and plan assignments.")

        except Exception as e:
            await ctx.send(f"An error occurred: {e}")
