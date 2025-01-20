import discord
import os
import asyncio
import logging
from discord.ext import commands
from utilits.database import Database
from dotenv import load_dotenv

# Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Get environment variables
TOKEN = os.getenv('DISCORD_TOKEN')
DATABASE_PATH = os.getenv('DATABASE')

# Create a bot with the required intents
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True  # Allow bot to react to messages

bot = commands.Bot(command_prefix='!', intents=intents)

# Create a Database instance and assign it to the bot
bot.db = Database(DATABASE_PATH)

# Event when the bot is ready
@bot.event
async def on_ready():
    """
    Event triggered when the bot successfully connects to Discord and becomes ready.

    This function logs the bot's connection status and ensures the database connection is active.
    """
    try:
        logger.info(f'Logged in as {bot.user}')

        # Check if database connection is active
        logger.info('Checking database connection...')
        if not await bot.db.is_connected():
            try:
                await bot.db.connect()
                logger.info(f'Successfully connected to database {DATABASE_PATH}')
            except Exception as e:
                logger.error(f'Failed to reconnect to database: {e}')
        else:
            logger.info(f'Database {DATABASE_PATH} is already connected.')
    except Exception as e:
        logger.error(f'An error occurred in event on_ready: {e}', exc_info=True)

# Event when the bot disconnects from Discord
@bot.event
async def on_disconnect():
    """
    Event triggered when the bot disconnects from Discord.

    This function attempts to gracefully close the database connection.
    """
    logger.warning('Bot disconnected from Discord!')
    try:
        await bot.db.close()
        logger.info('Disconnected from database')
    except Exception as e:
        logger.error(f'Error during database disconnection: {e}', exc_info=True)

# Event when bot successfully reconnects to Discord
@bot.event
async def on_resumed():
    """
    Event triggered when the bot reconnects to Discord after being disconnected.

    This function ensures the database connection is re-established if needed.
    """
    logger.info('Bot successfully reconnected to Discord!')
    try:
        if not await bot.db.is_connected():
            await bot.db.connect()
            logger.info(f'Reconnected to database {DATABASE_PATH} after Discord reconnect')
        else:
            logger.info('Database connection already active.')
    except Exception as e:
        logger.error(f'Failed to reconnect to database after Discord reconnect: {e}', exc_info=True)

# Function to reconnect to the database if connection is lost
async def reconnect_to_database():
    """
    Attempt to reconnect to the database if the connection is lost.

    This function runs in a loop, retrying every 60 seconds until the connection is successful.
    """
    while not await bot.db.is_connected():
        try:
            await bot.db.connect()
            logger.info('Successfully reconnected to the database.')
            break
        except Exception as e:
            logger.error(f'Failed to reconnect to the database: {e}', exc_info=True)
            await asyncio.sleep(60)  # Wait 60 seconds before retrying

# Handle unexpected errors
@bot.event
async def on_error(event, *args, **kwargs):
    """
    Event triggered when an unexpected error occurs during the bot's operation.

    Args:
        event (str): The name of the event where the error occurred.
        *args: Additional positional arguments.
        **kwargs: Additional keyword arguments.
    """
    logger.error(f'An error occurred in event {event}: {args[0] if args else "no args"}', exc_info=True)

# Asynchronous function to load Cogs
async def load_extensions():
    """
    Load the bot's extensions (Cogs).

    This function iterates through a list of predefined extensions and attempts to load each one.
    Logs success or failure for each extension.
    """
    initial_extensions = ['cogs.reminders', 'cogs.linkme', 'cogs.stats', 'cogs.rankings']
    for extension in initial_extensions:
        try:
            await bot.load_extension(extension)
            logger.info(f'Loaded extension {extension}')
        except Exception as e:
            logger.error(f'Failed to load extension {extension}: {e}', exc_info=True)

# Main asynchronous function to initialize and run the bot
async def run_bot():
    """
    Initialize and run the bot.

    This function sets up the database, loads extensions, and starts the bot.
    In case of errors during execution, the bot will restart after a short delay.
    """
    while True:
        try:
            # Initialize the database
            await bot.db.setup()

            # Load Cogs
            await load_extensions()

            # Start the bot
            await bot.start(TOKEN)
        except (discord.ConnectionClosed, Exception) as e:
            logger.error(f'Error occurred during bot execution: {e}', exc_info=True)
            logger.info('Attempting to restart the bot in 10 seconds...')
            await asyncio.sleep(10)  # Wait 10 seconds before restarting

# Main entry point
if __name__ == '__main__':
    """
    Entry point of the script.

    This block initializes the asynchronous bot execution process.
    """
    asyncio.run(run_bot())
