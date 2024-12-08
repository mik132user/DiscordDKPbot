import discord
import os
import asyncio
import logging
from discord.ext import commands
from utilits.database import Database  # импорт класса базы данных
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
    try:
        logger.info(f'Logged in as {bot.user}')

        # Check if database connection is active
        logger.info('Checking database connection...')
        if not await bot.db.is_connected():  # Здесь нужно использовать await для асинхронного метода
            try:
                await bot.db.connect()  # Попытка переподключения
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
    logger.warning('Bot disconnected from Discord!')
    # Try to close the database connection gracefully
    try:
        await bot.db.close()
        logger.info('Disconnected from database')
    except Exception as e:
        logger.error(f'Error during database disconnection: {e}', exc_info=True)

# Event when bot successfully reconnects to Discord
@bot.event
async def on_resumed():
    logger.info('Bot successfully reconnected to Discord!')
    # Reconnect to database if needed
    try:
        if not await bot.db.is_connected():  # Используем await здесь
            await bot.db.connect()  # Переподключение
            logger.info(f'Reconnected to database {DATABASE_PATH} after Discord reconnect')
        else:
            logger.info('Database connection already active.')
    except Exception as e:
        logger.error(f'Failed to reconnect to database after Discord reconnect: {e}', exc_info=True)

# Function to reconnect to the database if connection is lost
async def reconnect_to_database():
    while not await bot.db.is_connected():  # Используем await для проверки соединения
        try:
            await bot.db.connect()  # Попытка подключения
            logger.info('Successfully reconnected to the database.')
            break
        except Exception as e:
            logger.error(f'Failed to reconnect to the database: {e}', exc_info=True)
            await asyncio.sleep(60)  # Подождать 60 секунд перед повторной попыткой


# Handle unexpected errors
@bot.event
async def on_error(event, *args, **kwargs):
    logger.error(f'An error occurred in event {event}: {args[0] if args else "no args"}', exc_info=True)

# Asynchronous function to load Cogs
async def load_extensions():
    initial_extensions = ['cogs.reminders', 'cogs.linkme', 'cogs.stats', 'cogs.rankings']
    for extension in initial_extensions:
        try:
            await bot.load_extension(extension)
            logger.info(f'Loaded extension {extension}')
        except Exception as e:
            logger.error(f'Failed to load extension {extension}: {e}', exc_info=True)

# Main asynchronous function to initialize and run the bot
async def run_bot():
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
    asyncio.run(run_bot())
