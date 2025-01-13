import discord
import logging

# Dictionary to track bot's sent messages (keyed by user ID)
bot_messages = {}

async def save_message(ctx, bot_message):
    """
    Save the bot's last sent message ID for a user.
    """
    bot_messages[ctx.author.id] = bot_message.id
    logging.info(f"Saved message ID {bot_message.id} for user {ctx.author.name}.")

async def edit_last_message(ctx, new_content):
    """
    Edit the last message sent by the bot for the user.
    """
    if not new_content:
        await ctx.send("You must provide new content to update the message. Usage: `!editplan <new content>`")
        return

    if ctx.author.id in bot_messages:
        try:
            # Fetch the last sent message
            message_id = bot_messages[ctx.author.id]
            bot_message = await ctx.channel.fetch_message(message_id)

            # Edit the bot's message with the new content
            await bot_message.edit(content=new_content)
            await ctx.send("Message updated successfully!")
            logging.info(f"Message with ID {message_id} updated by {ctx.author.name}.")
        except discord.NotFound:
            await ctx.send("I couldn't find the message to edit.")
        except discord.Forbidden:
            await ctx.send("I don't have permission to edit that message.")
        except discord.HTTPException as e:
            logging.error(f"HTTPException while editing message: {e}")
            await ctx.send(f"An error occurred: {e}")
    else:
        await ctx.send("I can't find a message to edit. Did you use the `opsplan` or `mechplan` command?")
