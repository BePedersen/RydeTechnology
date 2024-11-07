import discord
import random
from discord.ext import commands
from discord import Interaction, ui

# Set up the bot with necessary intents
intents = discord.Intents.default()
intents.message_content = True  # Enable this to read message content
intents.members = True  # Enable this to read members from the server

# Create the bot instance
bot = commands.Bot(command_prefix="!", intents=intents)

class MemberSelect(ui.Select):
    def __init__(self, members):
        # Create a list of options for each member, excluding bots
        options = [
            discord.SelectOption(label=member.display_name, value=str(member.id))
            for member in members if not member.bot  # Exclude bots
        ]

        # If fewer than 5 members are available, add dummy options
        if len(options) < 5:
            for i in range(5 - len(options)):
                options.append(discord.SelectOption(label=f"Placeholder {i + 1}", value=f"placeholder_{i + 1}", description="No more members available"))

        super().__init__(placeholder="Choose members (1-5)", min_values=1, max_values=5, options=options)

    async def callback(self, interaction: discord.Interaction):
        print(f"Members selected: {self.values}")  # Debugging log

        # Store the selected members' IDs in the view and enable the button
        self.view.selected_members = [member_id for member_id in self.values if not "placeholder" in member_id]
        self.view.submit_plan.disabled = False  # Enable the submit button

        # Defer interaction to prevent timeout
        await interaction.response.defer()

        # Edit the original message with the updated view (enable the submit button)
        await interaction.followup.edit_message(interaction.message.id, view=self.view)


class FormModal(ui.Modal, title="Skift Plan Form"):
    def __init__(self, selected_members, member_names):
        super().__init__()
        # Store the selected members
        self.selected_members = selected_members
        self.member_names = member_names  # The display names of the selected members

        # Shortened label to avoid exceeding the 45 character limit
        self.areas = ui.TextInput(
            label="Enter Areas for Members",  # Shortened label
            placeholder=f"Areas for: {', '.join(member_names)}",  # Add member names as a placeholder
            style=discord.TextStyle.paragraph
        )
        self.percentage = ui.TextInput(label="Enter Percentage", style=discord.TextStyle.short)
        self.days = ui.TextInput(label="Enter Number of Days", style=discord.TextStyle.short)

        self.add_item(self.areas)
        self.add_item(self.percentage)
        self.add_item(self.days)

    async def on_submit(self, interaction: discord.Interaction):
        print(f"Selected members for areas: {self.selected_members}")  # Debugging log

        # Fetch members from their IDs
        members = [await interaction.guild.fetch_member(int(member_id)) for member_id in self.selected_members]
        areas = [area.strip() for area in self.areas.value.split(',')]

        # Check that the number of areas is between 1 and 5
        if not (1 <= len(areas) <= 5):
            await interaction.response.send_message("Please enter between 1 and 5 areas.")
            return

        percentage = int(self.percentage.value)  # Convert the input percentage to an integer
        days = self.days.value

        # List of possible action words to randomly choose from
        action_words = ["kjører", "holder fortet i", "triller rundt i", "gønner", "redder", "dreper superlows på", "går batshit crazy"]

        # Calculate the dynamic cluster and redeployment percentages
        cluster_percentage = percentage + 10
        redeployment_percentage = percentage + 15

        # Format the result message with a loop for members and areas
        response = "🦍🦍🛴🛴 **Skift Plan** 🦍🦍🛴🛴\n\n"
        response += "🚦 **Team and områder**:\n"
        for i in range(min(len(members), len(areas))):
            random_action = random.choice(action_words)  # Pick a random word from the list
            response += f"- **{members[i].mention}**: {random_action} **{areas[i]}**\n"

        # Add the rest of the message
        response += (
            f"\n📊 **Operational Notes**:\n"
            f"- **Inactivity**: 🔄 {percentage}% inactive for **{days} days**.\n"
            f"- **Clusters**: ➕ {cluster_percentage}% in clusters.\n"
            f"- **Redeployment**: 📉 {redeployment_percentage}% on inactives.\n\n"
            f"🔒 **Container Codes**:\n"
            f"- Code 1: **5071**\n"
            f"- Code 2: **76872**\n\n"
            f"🚨 **Important Reminders**:\n"
            f"- **Use the car** 🚗\n"
            f"- **Send routes** 🗺️\n"
            f"- Ensure **Good Quality Control (QC)**\n"
            f"- **Prioritize Superlows**\n"
            f"- If you receive a **nivel** issue, **fix it within an hour**.\n\n"
            f"📞 **Contact**:\n"
            f"- **My phone**: 90232485\n"
            f"- Or via **Discord**\n\n"
            f"🪫🪫 **Battery Check** 🔋🔋\n\n"
            f"Make sure you're charged up and ready to go!"
        )

        await interaction.response.send_message(response)


class FormView(ui.View):
    def __init__(self, members):
        super().__init__()
        self.selected_members = None
        self.member_names = []  # To store member display names

        # Add the member select menu, excluding bots
        self.add_item(MemberSelect(members))

        # Add the submit button, initially disabled
        self.submit_plan = discord.ui.Button(label="Submit Plan", style=discord.ButtonStyle.primary, disabled=True)
        self.submit_plan.callback = self.submit_plan_callback
        self.add_item(self.submit_plan)

    async def submit_plan_callback(self, interaction: discord.Interaction):
        # Only proceed if members were selected
        if not self.selected_members:
            await interaction.response.send_message("Please select members first.")
            return

        # Get display names for the selected members to show in the areas input
        print(f"Fetching display names for selected members: {self.selected_members}")  # Debugging log
        self.member_names = [interaction.guild.get_member(int(member_id)).display_name for member_id in self.selected_members]

        # Show the modal for further input (areas, percentage, etc.)
        await interaction.response.send_modal(FormModal(self.selected_members, self.member_names))


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')


@bot.command(name="plan")
async def start(ctx):
    # Get members from the server, excluding bots
    members = [member for member in ctx.guild.members if not member.bot]
    print(f"Members (excluding bots): {members}")  # Debugging log

    if len(members) == 0:
        await ctx.send("There are no human members to select.")
        return

    # Create a form view that includes a member select dropdown
    view = FormView(members)
    await ctx.send("Select the team members for the Skift Plan:", view=view)


# Run the bot
bot.run('MTI5OTAzMzU5MDcyNTYxMTUzMA.G3EwFp.Z1vloB5zRHQjQBcu5aSyzQYPA4CTYxkwHIYOi8')


