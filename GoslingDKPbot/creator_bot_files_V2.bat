@echo off
setlocal enabledelayedexpansion

:: Запрос ввода от пользователя
set /p kingdom=Enter kingdom (four digits): 
set /p token=Enter token (alphanumeric characters): 
set /p channels=Enter channels (comma-separated numbers): 

:: Создание папки kingdom
mkdir %kingdom%
cd %kingdom%

:: Создание подпапок cogs, data, utilits
mkdir cogs
mkdir data
mkdir utilits

:: Создание файлов .env, .gitignore, bot{kingdom}.py
echo DISCORD_TOKEN=%token% > .env
echo DATABASE=./data/DKP%kingdom%.db >> .env

echo # Environment Variables > .gitignore
echo .env >> .gitignore

:: Создание bot{kingdom}.py
echo # bot%kingdom%.py > bot%kingdom%.py
echo import discord >> bot%kingdom%.py
echo import os >> bot%kingdom%.py
echo import asyncio >> bot%kingdom%.py
echo import logging >> bot%kingdom%.py
echo from discord.ext import commands >> bot%kingdom%.py
echo from utilits.database import Database >> bot%kingdom%.py
echo from utilits.constants import DATABASE >> bot%kingdom%.py
echo from dotenv import load_dotenv >> bot%kingdom%.py
echo. >> bot%kingdom%.py
echo logging.basicConfig(level=logging.INFO) >> bot%kingdom%.py
echo logger = logging.getLogger(__name__) >> bot%kingdom%.py
echo load_dotenv() >> bot%kingdom%.py
echo TOKEN = os.getenv('DISCORD_TOKEN') >> bot%kingdom%.py
echo DATABASE_PATH = os.getenv('DATABASE') >> bot%kingdom%.py
echo intents = discord.Intents.default() >> bot%kingdom%.py
echo intents.message_content = True >> bot%kingdom%.py
echo intents.reactions = True >> bot%kingdom%.py
echo bot = commands.Bot(command_prefix='!', intents=intents) >> bot%kingdom%.py
echo bot.db = Database(DATABASE_PATH) >> bot%kingdom%.py
echo. >> bot%kingdom%.py
echo @bot.event >> bot%kingdom%.py
echo async def on_ready(): >> bot%kingdom%.py
echo     logger.info(f'Connected to database {DATABASE_PATH}') >> bot%kingdom%.py
echo     logger.info(f'Logged in as {bot.user}') >> bot%kingdom%.py
echo. >> bot%kingdom%.py
echo @bot.event >> bot%kingdom%.py
echo async def on_disconnect(): >> bot%kingdom%.py
echo     await bot.db.close() >> bot%kingdom%.py
echo     logger.info('Disconnected from database') >> bot%kingdom%.py
echo. >> bot%kingdom%.py
echo async def load_extensions(): >> bot%kingdom%.py
echo     initial_extensions = ['cogs.reminders', 'cogs.linkme', 'cogs.stats', 'cogs.rankings'] >> bot%kingdom%.py
echo     for extension in initial_extensions: >> bot%kingdom%.py
echo         try: >> bot%kingdom%.py
echo             await bot.load_extension(extension) >> bot%kingdom%.py
echo             logger.info(f'Loaded extension {extension}') >> bot%kingdom%.py
echo         except Exception as e: >> bot%kingdom%.py
echo             logger.error(f'Failed to load extension {extension}: {e}') >> bot%kingdom%.py
echo. >> bot%kingdom%.py
echo async def main(): >> bot%kingdom%.py
echo     try: >> bot%kingdom%.py
echo         await bot.db.setup() >> bot%kingdom%.py
echo         await load_extensions() >> bot%kingdom%.py
echo         await bot.start(TOKEN) >> bot%kingdom%.py
echo     except Exception as e: >> bot%kingdom%.py
echo         logger.error(f'Error during bot startup: {e}') >> bot%kingdom%.py
echo. >> bot%kingdom%.py
echo if __name__ == '__main__': >> bot%kingdom%.py
echo     asyncio.run(main()) >> bot%kingdom%.py

:: Переход в папку cogs и создание файлов
cd cogs
echo. > __init__.py
echo. > linkme.py
echo # cogs/linkme.py > linkme.py
echo. >> linkme.py
echo import discord >> linkme.py
echo from discord.ext import commands >> linkme.py
echo import asyncio >> linkme.py
echo. >> linkme.py
echo from utilits.constants import ALLOWED_CHANNELS >> linkme.py
echo import logging >> linkme.py
echo. >> linkme.py
echo logger = logging.getLogger(__name__) >> linkme.py
echo. >> linkme.py
echo class Linkme(commands.Cog): >> linkme.py
echo     def __init__(self, bot): >> linkme.py
echo         self.bot = bot >> linkme.py
echo         self.user_command_timestamps = {} >> linkme.py
echo. >> linkme.py
echo     @commands.command() >> linkme.py
echo     async def linkme(self, ctx, player_id: str): >> linkme.py
echo         now = discord.utils.utcnow() >> linkme.py
echo         last_used = self.user_command_timestamps.get(ctx.author.id, None) >> linkme.py
echo         if last_used and (now - last_used).total_seconds() < 10: >> linkme.py
echo             await ctx.send("Please wait before using this command again.") >> linkme.py
echo             return >> linkme.py
echo         self.user_command_timestamps[ctx.author.id] = now >> linkme.py
echo. >> linkme.py
echo         if ctx.channel.id not in ALLOWED_CHANNELS: >> linkme.py
echo             return >> linkme.py
echo. >> linkme.py
echo         try: >> linkme.py
echo             player_id = int(player_id) >> linkme.py
echo         except ValueError: >> linkme.py
echo             await ctx.send("Invalid player ID. Please provide a valid numeric ID. Example: `!linkme 12345`.") >> linkme.py
echo             return >> linkme.py
echo. >> linkme.py
echo         discord_user_id = ctx.author.id >> linkme.py
echo. >> linkme.py
echo         try: >> linkme.py
echo             async with self.bot.db.conn.cursor() as cursor: >> linkme.py
echo                 await cursor.execute("SELECT ID FROM DKP WHERE ID=?", (player_id,)) >> linkme.py
echo                 player_in_dkp = await cursor.fetchone() >> linkme.py
echo. >> linkme.py
echo                 if not player_in_dkp: >> linkme.py
echo                     await ctx.send(f"ID {player_id} not found in the DKP table. Please check the entered ID.") >> linkme.py
echo                     return >> linkme.py
echo. >> linkme.py
echo                 await cursor.execute("SELECT * FROM users WHERE discord_user_id=?", (discord_user_id,)) >> linkme.py
echo                 existing_user = await cursor.fetchone() >> linkme.py
echo. >> linkme.py
echo                 if not existing_user: >> linkme.py
echo                     await cursor.execute("INSERT INTO users (discord_user_id) VALUES (?)", (discord_user_id,)) >> linkme.py
echo                     await self.bot.db.conn.commit() >> linkme.py
echo                     existing_user = (discord_user_id, None, None, None, None, None, None, None, None, None) >> linkme.py
echo. >> linkme.py
echo                 linked_ids = existing_user[1:] >> linkme.py
echo                 if player_id in linked_ids: >> linkme.py
echo                     await ctx.send(f"ID {player_id} is already linked to your profile.") >> linkme.py
echo                     return >> linkme.py
echo. >> linkme.py
echo                 message = await ctx.send( >> linkme.py
echo                     "Choose an option:\n" >> linkme.py
echo                     "1️⃣ Main\n" >> linkme.py
echo                     "2️⃣ Alt\n" >> linkme.py
echo                     "3️⃣ Farm" >> linkme.py
echo                 ) >> linkme.py
echo. >> linkme.py
echo                 reactions = ['1️⃣', '2️⃣', '3️⃣'] >> linkme.py
echo                 for emoji in reactions: >> linkme.py
echo                     await message.add_reaction(emoji) >> linkme.py
echo. >> linkme.py
echo                 def check(reaction, user): >> linkme.py
echo                     return user == ctx.author and str(reaction.emoji) in reactions and reaction.message.id == message.id >> linkme.py
echo. >> linkme.py
echo                 try: >> linkme.py
echo                     reaction, _ = await self.bot.wait_for('reaction_add', timeout=60.0, check=check) >> linkme.py
echo. >> linkme.py
echo                     if reaction.emoji == '1️⃣': >> linkme.py
echo                         columns_to_check = ["main_id"] >> linkme.py
echo                     elif reaction.emoji == '2️⃣': >> linkme.py
echo                         columns_to_check = ["alt1_id", "alt2_id", "alt3_id"] >> linkme.py
echo                     elif reaction.emoji == '3️⃣': >> linkme.py
echo                         columns_to_check = ["farm1_id", "farm2_id", "farm3_id", "farm4_id", "farm5_id"] >> linkme.py
echo. >> linkme.py
echo                     for column in columns_to_check: >> linkme.py
echo                         column_index = { >> linkme.py
echo                             "main_id": 0, >> linkme.py
echo                             "alt1_id": 1, >> linkme.py
echo                             "alt2_id": 2, >> linkme.py
echo                             "alt3_id": 3, >> linkme.py
echo                             "farm1_id": 4, >> linkme.py
echo                             "farm2_id": 5, >> linkme.py
echo                             "farm3_id": 6, >> linkme.py
echo                             "farm4_id": 7, >> linkme.py
echo                             "farm5_id": 8 >> linkme.py
echo                         }[column] >> linkme.py
echo                         if linked_ids[column_index] is None: >> linkme.py
echo                             await cursor.execute(f"UPDATE users SET {column}=? WHERE discord_user_id=?", (player_id, discord_user_id)) >> linkme.py
echo                             await self.bot.db.conn.commit() >> linkme.py
echo                             await ctx.send(f"ID {player_id} successfully linked to your profile as {column.replace('_id', '').capitalize()}.") >> linkme.py
echo                             return >> linkme.py
echo. >> linkme.py
echo                 await ctx.send("All slots for the selected option are already occupied.") >> linkme.py
echo. >> linkme.py
echo                 except asyncio.TimeoutError: >> linkme.py
echo                     await ctx.send("Selection time has expired.") >> linkme.py
echo. >> linkme.py
echo         except Exception as e: >> linkme.py
echo             logger.error(f"Database error: {e}") >> linkme.py
echo             await ctx.send("An error occurred while linking the ID.") >> linkme.py
echo. >> linkme.py
echo     @commands.command() >> linkme.py
echo     async def unlinkme(self, ctx, player_id: str): >> linkme.py
echo         now = discord.utils.utcnow() >> linkme.py
echo         last_used = self.user_command_timestamps.get(ctx.author.id, None) >> linkme.py
echo         if last_used and (now - last_used).total_seconds() < 10: >> linkme.py
echo             await ctx.send("Please wait before using this command again.") >> linkme.py
echo             return >> linkme.py
echo         self.user_command_timestamps[ctx.author.id] = now >> linkme.py
echo. >> linkme.py
echo         if ctx.channel.id not in ALLOWED_CHANNELS: >> linkme.py
echo             return >> linkme.py
echo. >> linkme.py
echo         try: >> linkme.py
echo             player_id = int(player_id) >> linkme.py
echo         except ValueError: >> linkme.py
echo             await ctx.send("Invalid player ID. Please provide a valid numeric ID. Example: `!unlinkme 12345`.") >> linkme.py
echo             return >> linkme.py
echo. >> linkme.py
echo         discord_user_id = ctx.author.id >> linkme.py
echo. >> linkme.py
echo         try: >> linkme.py
echo             async with self.bot.db.conn.cursor() as cursor: >> linkme.py
echo                 await cursor.execute(""" >> linkme.py
echo                     SELECT main_id, alt1_id, alt2_id, alt3_id, farm1_id, farm2_id, farm3_id, farm4_id, farm5_id >> linkme.py
echo                     FROM users >> linkme.py
echo                     WHERE discord_user_id=? >> linkme.py
echo                 """, (discord_user_id,)) >> linkme.py
echo                 linked_ids = await cursor.fetchone() >> linkme.py
echo. >> linkme.py
echo                 if not linked_ids: >> linkme.py
echo                     await ctx.send("You have no linked IDs.") >> linkme.py
echo                     return >> linkme.py
echo. >> linkme.py
echo                 if player_id not in linked_ids: >> linkme.py
echo                     await ctx.send(f"ID {player_id} is not linked to your profile.") >> linkme.py
echo                     return >> linkme.py
echo. >> linkme.py
echo                 for i, column in enumerate(["main_id", "alt1_id", "alt2_id", "alt3_id", "farm1_id", "farm2_id", "farm3_id", "farm4_id", "farm5_id"]): >> linkme.py
echo                     if linked_ids[i] == player_id: >> linkme.py
echo                         await cursor.execute(f"UPDATE users SET {column}=NULL WHERE discord_user_id=?", (discord_user_id,)) >> linkme.py
echo                         await self.bot.db.conn.commit() >> linkme.py
echo                         await ctx.send(f"ID {player_id} successfully unlinked from your profile.") >> linkme.py
echo                         return >> linkme.py
echo. >> linkme.py
echo         except Exception as e: >> linkme.py
echo             logger.error(f"Database error: {e}") >> linkme.py
echo             await ctx.send("An error occurred while unlinking the ID.") >> linkme.py
echo. >> linkme.py
echo async def setup(bot): >> linkme.py
echo     await bot.add_cog(Linkme(bot)) >> linkme.py
echo. > rankings.py
:: Создание rankings.py с необходимым содержимым
echo import discord > rankings.py
echo from discord.ext import commands >> rankings.py
echo from discord.ui import View, Button >> rankings.py
echo from utilits.constants import UPDATE_DATE, ALLOWED_CHANNELS >> rankings.py
echo import logging >> rankings.py
echo import asyncio >> rankings.py
echo. >> rankings.py
echo logger = logging.getLogger(__name__) >> rankings.py
echo. >> rankings.py
echo class Rankings(commands.Cog): >> rankings.py
echo     def __init__(self, bot): >> rankings.py
echo         self.bot = bot >> rankings.py
echo         # Anti-DDoS rate limiting: Dictionary to track command usage >> rankings.py
echo         self.user_command_timestamps = {} >> rankings.py
echo. >> rankings.py
echo     @commands.command() >> rankings.py
echo     async def top(self, ctx, number: int = 10): >> rankings.py
echo         # Implement rate limiting (1 command per 10 seconds per user) >> rankings.py
echo         now = discord.utils.utcnow() >> rankings.py
echo         last_used = self.user_command_timestamps.get(ctx.author.id, None) >> rankings.py
echo         if last_used and (now - last_used).total_seconds() < 10: >> rankings.py
echo             await ctx.send("Please wait before using this command again.") >> rankings.py
echo             return >> rankings.py
echo         self.user_command_timestamps[ctx.author.id] = now >> rankings.py
echo. >> rankings.py
echo         try: >> rankings.py
echo             if ctx.channel.id not in ALLOWED_CHANNELS: >> rankings.py
echo                 await ctx.send("This command is not allowed in this channel.") >> rankings.py
echo                 return >> rankings.py
echo. >> rankings.py
echo             # Limit the number of players >> rankings.py
echo             if number < 1 or number > 25: >> rankings.py
echo                 await ctx.send("Please specify a number between 1 and 25.") >> rankings.py
echo                 return >> rankings.py
echo. >> rankings.py
echo             # Create the buttons for selecting ranking categories >> rankings.py
echo             view = RankSelectionView(self.bot, ctx.author, number) >> rankings.py
echo             message = await ctx.send("Choose a ranking category:", view=view) >> rankings.py
echo. >> rankings.py
echo             # Save the message for future interactions >> rankings.py
echo             view.message = message >> rankings.py
echo. >> rankings.py
echo         except Exception as e: >> rankings.py
echo             logger.error(f'Error in top command: {e}') >> rankings.py
echo             await ctx.send("An error occurred while fetching the top rankings.") >> rankings.py
echo. >> rankings.py
echo class RankSelectionView(View): >> rankings.py
echo     def __init__(self, bot, author, number): >> rankings.py
echo         super().__init__(timeout=60) >> rankings.py
echo         self.bot = bot >> rankings.py
echo         self.author = author >> rankings.py
echo         self.number = number >> rankings.py
echo         self.column_mapping = { >> rankings.py
echo             'Starting Power': 'Power_before_matchmaking', >> rankings.py
echo             'Deads Gained': '(Deads_gained_z5 + Deads_gained_Kingsland + Deads_gained_7_pass)', >> rankings.py
echo             'KP Gained': '(KP_gained_z5 + KP_gained_Kingsland + Altars_gained_KP + KP_gained_7_pass)', >> rankings.py
echo             'Score': 'Changed_DKP' >> rankings.py
echo         } >> rankings.py
echo. >> rankings.py
echo         for label, column in self.column_mapping.items(): >> rankings.py
echo             button = Button(label=label, style=discord.ButtonStyle.primary) >> rankings.py
echo             button.callback = lambda interaction, col=column: self.show_ranking(interaction, col) >> rankings.py
echo             self.add_item(button) >> rankings.py
echo. >> rankings.py
echo     async def interaction_check(self, interaction): >> rankings.py
echo         """Checks whether the user who pressed the button is the same as the one who invoked the command.""" >> rankings.py
echo         if interaction.user != self.author: >> rankings.py
echo             await interaction.response.send_message("You cannot interact with these buttons.", ephemeral=True) >> rankings.py
echo             return False >> rankings.py
echo         return True >> rankings.py
echo. >> rankings.py
echo     async def show_ranking(self, interaction, column_name): >> rankings.py
echo         if not await self.interaction_check(interaction): >> rankings.py
echo             return >> rankings.py
echo. >> rankings.py
echo         try: >> rankings.py
echo             async with self.bot.db.conn.cursor() as cursor: >> rankings.py
echo                 query = f""" >> rankings.py
echo                     SELECT Name, ID, {column_name} >> rankings.py
echo                     FROM DKP >> rankings.py
echo                     ORDER BY {column_name} DESC >> rankings.py
echo                 """ >> rankings.py
echo                 await cursor.execute(query) >> rankings.py
echo                 all_players = await cursor.fetchall() >> rankings.py
echo. >> rankings.py
echo             if not all_players: >> rankings.py
echo                 await interaction.response.send_message("Failed to retrieve data about the top players.", ephemeral=True) >> rankings.py
echo                 return >> rankings.py
echo. >> rankings.py
echo             cleaned_players = [(name, player_id, self.safe_int_conversion(value)) for name, player_id, value in all_players] >> rankings.py
echo             sorted_players = sorted(cleaned_players, key=lambda x: -x[2])[:self.number] >> rankings.py
echo             namename = self.get_column_display_name(column_name) >> rankings.py
echo. >> rankings.py
echo             embed = discord.Embed( >> rankings.py
echo                 title=f"Top {self.number} by {namename}", >> rankings.py
echo                 description=f"Here are the top {self.number} players sorted by {namename}.", >> rankings.py
echo                 color=discord.Color.gold() >> rankings.py
echo             ) >> rankings.py
echo. >> rankings.py
echo             for index, (name, player_id, value_int) in enumerate(sorted_players): >> rankings.py
echo                 trophy = self.get_trophy(index) >> rankings.py
echo                 embed.add_field(name=f"{trophy} {name}", value=f"{value_int:,}", inline=False) >> rankings.py
echo. >> rankings.py
echo             embed.set_footer(text=f'Updated - {UPDATE_DATE}') >> rankings.py
echo             await interaction.response.send_message(embed=embed) >> rankings.py
echo. >> rankings.py
echo         except Exception as e: >> rankings.py
echo             logger.error(f'Error in show_ranking: {e}') >> rankings.py
echo             await interaction.response.send_message("An error occurred while fetching the top players.", ephemeral=True) >> rankings.py
echo. >> rankings.py
echo     def get_column_display_name(self, column_name): >> rankings.py
echo         """Maps column names to human-readable display names for the ranking categories.""" >> rankings.py
echo         return { >> rankings.py
echo             'Power_before_matchmaking': "Starting Power", >> rankings.py
echo             '(Deads_gained_z5 + Deads_gained_Kingsland + Deads_gained_7_pass)': "Deads Gained", >> rankings.py
echo             '(KP_gained_z5 + KP_gained_Kingsland + Altars_gained_KP + KP_gained_7_pass)': "KP Gained", >> rankings.py
echo             'Changed_DKP': 'Score' >> rankings.py
echo         }.get(column_name, column_name.replace('_', ' ').capitalize()) >> rankings.py
echo. >> rankings.py
echo     def safe_int_conversion(self, value): >> rankings.py
echo         """Converts a value to an integer, ignoring any fractional part.""" >> rankings.py
echo         try: >> rankings.py
echo             if isinstance(value, str): >> rankings.py
echo                 value_clean = value.replace(' ', '').replace(',', '.') >> rankings.py
echo                 return int(float(value_clean)) >> rankings.py
echo             else: >> rankings.py
echo                 return int(value) >> rankings.py
echo         except (ValueError, TypeError): >> rankings.py
echo             return 0 >> rankings.py
echo. >> rankings.py
echo     def get_trophy(self, index): >> rankings.py
echo         """Assigns a trophy emoji or position number based on ranking index.""" >> rankings.py
echo         trophies = [":first_place:", ":second_place:", ":third_place:"] >> rankings.py
echo         return trophies[index] if index < 3 else f"{index + 1}:" >> rankings.py
echo. >> rankings.py
echo     async def on_timeout(self): >> rankings.py
echo         """Disable the view after timeout.""" >> rankings.py
echo         for child in self.children: >> rankings.py
echo             child.disabled = True >> rankings.py
echo         if hasattr(self, 'message'): >> rankings.py
echo             await self.message.edit(view=self) >> rankings.py
echo. >> rankings.py
echo async def setup(bot): >> rankings.py
echo     await bot.add_cog(Rankings(bot)) >> rankings.py

:: Скрипт завершен
echo rankings.py created successfully!
echo. > reminders.py
:: Создание reminders.py с необходимым содержимым
echo # cogs/reminders.py > reminders.py
echo. >> reminders.py
echo import discord >> reminders.py
echo from discord.ext import commands, tasks >> reminders.py
echo from datetime import datetime, timedelta >> reminders.py
echo import pytz >> reminders.py
echo import logging >> reminders.py
echo from utilits.constants import UPDATE_DATE, ALLOWED_CHANNELS >> reminders.py
echo. >> reminders.py
echo logger = logging.getLogger(__name__) >> reminders.py
echo. >> reminders.py
echo class Reminders(commands.Cog): >> reminders.py
echo     def __init__(self, bot): >> reminders.py
echo         self.bot = bot >> reminders.py
echo         self.check_reminders.start() >> reminders.py
echo         self.user_command_timestamps = {} >> reminders.py
echo. >> reminders.py
echo     def cog_unload(self): >> reminders.py
echo         self.check_reminders.cancel() >> reminders.py
echo. >> reminders.py
echo     @commands.command() >> reminders.py
echo     @commands.has_permissions(administrator=True) >> reminders.py
echo     async def remind(self, ctx, event_type: str, date: str, time: str): >> reminders.py
echo         now = discord.utils.utcnow() >> reminders.py
echo         last_used = self.user_command_timestamps.get(ctx.author.id, None) >> reminders.py
echo         if last_used and (now - last_used).total_seconds() < 10: >> reminders.py
echo             await ctx.send("Please wait before using this command again.") >> reminders.py
echo             return >> reminders.py
echo         self.user_command_timestamps[ctx.author.id] = now >> reminders.py
echo. >> reminders.py
echo         try: >> reminders.py
echo             event_datetime = datetime.strptime(f"%date% %time%", "%%d.%%m.%%y %%H:%%M") >> reminders.py
echo             event_datetime = event_datetime.replace(tzinfo=pytz.UTC) >> reminders.py
echo. >> reminders.py
echo             if event_datetime <= datetime.utcnow().replace(tzinfo=pytz.UTC): >> reminders.py
echo                 await ctx.send("The event time must be in the future.") >> reminders.py
echo                 return >> reminders.py
echo. >> reminders.py
echo             if event_type == "altar": >> reminders.py
echo                 notify_time = event_datetime - timedelta(hours=2) >> reminders.py
echo                 interval = timedelta(hours=86) >> reminders.py
echo             elif event_type == "ruin": >> reminders.py
echo                 notify_time = event_datetime - timedelta(hours=1) >> reminders.py
echo                 interval = timedelta(hours=40) >> reminders.py
echo             else: >> reminders.py
echo                 await ctx.send("Invalid event type. Use 'altar' or 'ruin'. Example: `!remind altar 01.10.24 16:12`.") >> reminders.py
echo                 return >> reminders.py
echo. >> reminders.py
echo             try: >> reminders.py
echo                 async with self.bot.db.conn.cursor() as cursor: >> reminders.py
echo                     await cursor.execute("DELETE FROM reminders WHERE event_type = ? AND channel_id = ?", (event_type, ctx.channel.id)) >> reminders.py
echo                     await cursor.execute("INSERT INTO reminders (event_type, event_time, notify_time, channel_id) VALUES (?, ?, ?, ?)", (event_type, event_datetime.isoformat(), notify_time.isoformat(), ctx.channel.id)) >> reminders.py
echo                     await self.bot.db.conn.commit() >> reminders.py
echo                 await ctx.send(f"Reminder set for {event_type} on {event_datetime.strftime('%%d.%%m.%%y %%H:%%M UTC')} in this channel.") >> reminders.py
echo             except Exception as e: >> reminders.py
echo                 logger.error(f"Database error: {e}") >> reminders.py
echo                 await ctx.send("An error occurred while setting the reminder.") >> reminders.py
echo. >> reminders.py
echo         except ValueError: >> reminders.py
echo             await ctx.send("Invalid date or time format. Use 'DD.MM.YY HH:MM'. Example: `!remind altar 01.10.24 16:12`.") >> reminders.py
echo. >> reminders.py
echo     @commands.command() >> reminders.py
echo     @commands.has_permissions(administrator=True) >> reminders.py
echo     async def remind_off(self, ctx, event_type: str): >> reminders.py
echo         if ctx.channel.id not in ALLOWED_CHANNELS: >> reminders.py
echo             return >> reminders.py
echo. >> reminders.py
echo         try: >> reminders.py
echo             async with self.bot.db.conn.cursor() as cursor: >> reminders.py
echo                 await cursor.execute("DELETE FROM reminders WHERE event_type = ? AND channel_id = ?", (event_type, ctx.channel.id)) >> reminders.py
echo                 await self.bot.db.conn.commit() >> reminders.py
echo             await ctx.send(f"All upcoming {event_type} reminders in this channel have been cancelled.") >> reminders.py
echo         except Exception as e: >> reminders.py
echo             logger.error(f"Database error: {e}") >> reminders.py
echo             await ctx.send("An error occurred while cancelling the reminders.") >> reminders.py
echo. >> reminders.py
echo     @tasks.loop(minutes=1) >> reminders.py
echo     async def check_reminders(self): >> reminders.py
echo         now = datetime.utcnow().replace(tzinfo=pytz.UTC) >> reminders.py
echo         try: >> reminders.py
echo             async with self.bot.db.conn.cursor() as cursor: >> reminders.py
echo                 await cursor.execute("SELECT id, event_type, event_time, notify_time, channel_id FROM reminders WHERE notify_time <= ?", (now.isoformat(),)) >> reminders.py
echo                 reminders = await cursor.fetchall() >> reminders.py
echo. >> reminders.py
echo                 for reminder in reminders: >> reminders.py
echo                     reminder_id, event_type, event_time, notify_time, channel_id = reminder >> reminders.py
echo                     event_time = datetime.fromisoformat(event_time).replace(tzinfo=pytz.UTC) >> reminders.py
echo. >> reminders.py
echo                     channel = self.bot.get_channel(channel_id) >> reminders.py
echo                     if channel: >> reminders.py
echo                         description = f"**Reminder:** {event_type.capitalize()} opens on {event_time.strftime('%%d.%%m.%%y %%H:%%M UTC')}." >> reminders.py
echo                         embed = discord.Embed(title=f"Event Reminder: {event_type.capitalize()}", description=description, color=discord.Color.red()) >> reminders.py
echo                         await channel.send(f"@everyone", embed=embed) >> reminders.py
echo. >> reminders.py
echo                         next_event_time = event_time + (timedelta(hours=86) if event_type == "altar" else timedelta(hours=40)) >> reminders.py
echo                         next_notify_time = next_event_time - (timedelta(hours=2) if event_type == "altar" else timedelta(hours=1)) >> reminders.py
echo. >> reminders.py
echo                         await cursor.execute("UPDATE reminders SET event_time = ?, notify_time = ? WHERE id = ?", (next_event_time.isoformat(), next_notify_time.isoformat(), reminder_id)) >> reminders.py
echo             await self.bot.db.conn.commit() >> reminders.py
echo         except Exception as e: >> reminders.py
echo             logger.error(f"Error checking reminders: {e}") >> reminders.py
echo. >> reminders.py
echo     @check_reminders.before_loop >> reminders.py
echo     async def before_check_reminders(self): >> reminders.py
echo         await self.bot.wait_until_ready() >> reminders.py
echo. >> reminders.py
echo     @commands.Cog.listener() >> reminders.py
echo     async def on_command_error(self, ctx, error): >> reminders.py
echo         if isinstance(error, commands.CommandNotFound): >> reminders.py
echo             await ctx.send("Command not found. Please check your input.") >> reminders.py
echo         elif isinstance(error, commands.MissingRequiredArgument): >> reminders.py
echo             if ctx.command.name == 'remind_off': >> reminders.py
echo                 await ctx.send("Please provide the event type argument. Example: `!remind_off altar`.") >> reminders.py
echo             else: >> reminders.py
echo                 await ctx.send("Please provide all required arguments. Example: `!remind altar 01.10.24 16:12`.") >> reminders.py
echo         elif isinstance(error, commands.BadArgument): >> reminders.py
echo             await ctx.send("One of the arguments is invalid. Please check your input. Example: `!remind altar 01.10.24 16:12`.") >> reminders.py
echo         elif isinstance(error, commands.CheckFailure): >> reminders.py
echo             await ctx.send("You do not have permission to use this command.") >> reminders.py
echo         else: >> reminders.py
echo             await ctx.send("An unexpected error occurred. Please try again later.") >> reminders.py
echo             logger.error(f"Error in command '{ctx.command}': {error}") >> reminders.py
echo. >> reminders.py
echo async def setup(bot): >> reminders.py
echo     await bot.add_cog(Reminders(bot)) >> reminders.py

echo. > stats.py
:: Добавляем код в файл stats.py
echo import os > stats.py
echo import discord >> stats.py
echo from discord.ext import commands >> stats.py
echo import aiosqlite >> stats.py
echo import asyncio >> stats.py
echo import logging >> stats.py
echo from utilits.constants import UPDATE_DATE, ALLOWED_CHANNELS >> stats.py
echo. >> stats.py
echo logger = logging.getLogger(__name__) >> stats.py
echo. >> stats.py
echo class PlayerStats(commands.Cog): >> stats.py
echo     def __init__(self, bot): >> stats.py
echo         self.bot = bot >> stats.py
echo         self.user_command_timestamps = {} >> stats.py
echo. >> stats.py
echo     @commands.command() >> stats.py
echo     async def stats(self, ctx): >> stats.py
echo         now = discord.utils.utcnow() >> stats.py
echo         last_used = self.user_command_timestamps.get(ctx.author.id, None) >> stats.py
echo         self.user_command_timestamps[ctx.author.id] = now >> stats.py
echo. >> stats.py
echo         if ctx.channel.id not in ALLOWED_CHANNELS: >> stats.py
echo             await ctx.send("This command is not available in this channel.") >> stats.py
echo             return >> stats.py
echo. >> stats.py
echo         discord_user_id = ctx.author.id >> stats.py
echo         DATABASE = os.getenv('DATABASE') >> stats.py
echo. >> stats.py
echo         try: >> stats.py
echo             async with aiosqlite.connect(DATABASE) as db: >> stats.py
echo                 cursor = await db.cursor() >> stats.py
echo. >> stats.py
echo                 await cursor.execute(^"SELECT main_id, alt1_id, alt2_id, alt3_id, farm1_id, farm2_id, farm3_id, farm4_id, farm5_id FROM users WHERE discord_user_id=?"^, (discord_user_id,)) >> stats.py
echo                 user_data = await cursor.fetchone() >> stats.py
echo. >> stats.py
echo                 if not user_data: >> stats.py
echo                     await ctx.send("You do not have any registered accounts.") >> stats.py
echo                     return >> stats.py
echo. >> stats.py
echo                 available_columns = [] >> stats.py
echo                 player_ids = [] >> stats.py
echo                 column_names = [] >> stats.py
echo. >> stats.py
echo                 columns = [^"main_id"^, ^"alt1_id"^, ^"alt2_id"^, ^"alt3_id"^, ^"farm1_id"^, ^"farm2_id"^, ^"farm3_id"^, ^"farm4_id"^, ^"farm5_id"^] >> stats.py
echo                 account_names = [^"Main"^, ^"Alt 1"^, ^"Alt 2"^, ^"Alt 3"^, ^"Farm 1"^, ^"Farm 2"^, ^"Farm 3"^, ^"Farm 4"^, ^"Farm 5"^] >> stats.py
echo. >> stats.py
echo                 for idx, player_id in enumerate(user_data): >> stats.py
echo                     if player_id: >> stats.py
echo                         available_columns.append(columns[idx]) >> stats.py
echo                         player_ids.append(player_id) >> stats.py
echo                         column_names.append(account_names[idx]) >> stats.py
echo. >> stats.py
echo                 if not available_columns: >> stats.py
echo                     await ctx.send("You do not have any registered accounts.") >> stats.py
echo                     return >> stats.py
echo. >> stats.py
echo                 if len(available_columns) == 1: >> stats.py
echo                     selected_column = available_columns[0] >> stats.py
echo                     selected_player_id = player_ids[0] >> stats.py
echo                 else: >> stats.py
echo                     message_content = "Select an account to view statistics:\n" + ^"\n"^.join([f^"{emoji} **{name}** (ID: **{player_id}**)" for emoji, name, player_id in zip(['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣'], column_names, player_ids)]) >> stats.py
echo                     message = await ctx.send(message_content) >> stats.py
echo. >> stats.py
echo                     for emoji in ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣'][:len(available_columns)]: >> stats.py
echo                         await message.add_reaction(emoji) >> stats.py
echo. >> stats.py
echo                     def check(reaction, user): >> stats.py
echo                         return user == ctx.author and str(reaction.emoji) in ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣'] >> stats.py
echo. >> stats.py
echo                     try: >> stats.py
echo                         reaction, _ = await self.bot.wait_for('reaction_add', timeout=60.0, check=check) >> stats.py
echo                         selected_index = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣'].index(str(reaction.emoji)) >> stats.py
echo                         selected_column = available_columns[selected_index] >> stats.py
echo                         selected_player_id = player_ids[selected_index] >> stats.py
echo. >> stats.py
echo                     except asyncio.TimeoutError: >> stats.py
echo                         await ctx.send("Time to select an account has expired.") >> stats.py
echo                         return >> stats.py
echo. >> stats.py
echo                 await cursor.execute(^"SELECT * FROM DKP WHERE ID=?"^, (selected_player_id,)) >> stats.py
echo                 player_data = await cursor.fetchone() >> stats.py
echo. >> stats.py
echo                 if player_data is None: >> stats.py
echo                     await ctx.send("No data found for the selected player.") >> stats.py
echo                     return >> stats.py
echo. >> stats.py
echo                 def safe_get(value, default=0): >> stats.py
echo                     return value if value is not None else default >> stats.py
echo. >> stats.py
echo                 try: >> stats.py
echo                     rank = safe_get(player_data[0]) >> stats.py
echo                     player_name = player_data[1] >> stats.py
echo                     player_id = player_data[2] >> stats.py
echo                     starting_power = safe_get(player_data[5]) >> stats.py
echo                     kp_requirements = safe_get(player_data[6]) >> stats.py
echo                     kill_requirements = safe_get(player_data[7]) >> stats.py
echo                     target_dkp_points = safe_get(player_data[8]) >> stats.py
echo                     dkp_points = safe_get(player_data[28]) >> stats.py
echo                     kp_gained_z5 = safe_get(player_data[13]) >> stats.py
echo                     kp_gained_altar = safe_get(player_data[15]) >> stats.py
echo                     kp_gained_pass_7 = safe_get(player_data[20]) >> stats.py
echo                     kp_gained_kingsland = safe_get(player_data[26]) >> stats.py
echo                     troops_killed_z5 = safe_get(player_data[14]) >> stats.py
echo                     troops_killed_pass_7 = safe_get(player_data[21]) >> stats.py
echo                     troops_killed_kingsland = safe_get(player_data[27]) >> stats.py
echo. >> stats.py
echo                     kp_gained = kp_gained_z5 + kp_gained_altar + kp_gained_pass_7 + kp_gained_kingsland >> stats.py
echo                     troops_killed = troops_killed_z5 + troops_killed_pass_7 + troops_killed_kingsland >> stats.py
echo. >> stats.py
echo                     if target_dkp_points > 0: >> stats.py
echo                         goal_achieved = (dkp_points / target_dkp_points) * 100 >> stats.py
echo                     else: >> stats.py
echo                         goal_achieved = 0 >> stats.py
echo. >> stats.py
echo                     embed = discord.Embed( >> stats.py
echo                         title=f"Player Stats - {player_name}", >> stats.py
echo                         description=f"Statistics for player ID: **{player_id}**", >> stats.py
echo                         color=discord.Color.green() >> stats.py
echo                     ) >> stats.py
echo. >> stats.py
echo                     embed.add_field(name="Rank", value=f"{rank}", inline=True) >> stats.py
echo                     embed.add_field(name="Starting Power", value=f"{starting_power:,}", inline=True) >> stats.py
echo                     embed.add_field(name="KP Gained", value=f"{kp_gained:,}", inline=True) >> stats.py
echo. >> stats.py
echo                     embed.add_field(name="Troops Killed", value=f"{troops_killed:,}", inline=True) >> stats.py
echo                     embed.add_field(name="Dead Requirements", value=f"{kill_requirements:,}", inline=True) >> stats.py
echo                     embed.add_field(name="KP Requirements", value=f"{kp_requirements:,}", inline=True) >> stats.py
echo. >> stats.py
echo                     embed.add_field(name="DKP Points", value=f"{dkp_points:,}", inline=True) >> stats.py
echo                     embed.add_field(name="Target DKP Points", value=f"{target_dkp_points:,}", inline=True) >> stats.py
echo                     embed.add_field(name="Goal Achieved", value=f"{goal_achieved:.2f}%%", inline=True) >> stats.py
echo. >> stats.py
echo                     embed.set_footer(text=f"Updated - {UPDATE_DATE}") >> stats.py
echo. >> stats.py
echo                     await ctx.send(embed=embed) >> stats.py
echo. >> stats.py
echo                 except Exception as e: >> stats.py
echo                     logger.error(f"Error extracting player data: {e}") >> stats.py
echo                     await ctx.send("Incomplete data for player statistics.") >> stats.py
echo. >> stats.py
echo         except Exception as e: >> stats.py
echo             logger.error(f"Database error: {e}") >> stats.py
echo             await ctx.send("An error occurred while retrieving player statistics.") >> stats.py
echo. >> stats.py
echo async def setup(bot): >> stats.py
echo     await bot.add_cog(PlayerStats(bot)) >> stats.py

:: Переход в папку data и создание базы данных DKP{kingdom}.db
cd ..
cd data
echo. > DKP%kingdom%.db

:: Переход в папку utilits и создание файлов
cd ..
cd utilits
echo. > __init__.py
echo # utilits/constants.py > constants.py
echo import os >> constants.py
echo. >> constants.py
echo # List of allowed channel IDs >> constants.py
echo ALLOWED_CHANNELS = [%channels%] >> constants.py
echo. >> constants.py
echo # Updated date >> constants.py
echo UPDATE_DATE = 'unknown' >> constants.py
echo. >> constants.py
echo # Path to the database >> constants.py
echo DATABASE = os.getenv('DATABASE') >> constants.py

echo # utilits/database.py > database.py
echo import aiosqlite >> database.py
echo. >> database.py
echo class Database: >> database.py
echo     def __init__(self, db_path): >> database.py
echo         self.db_path = db_path >> database.py
echo         self.conn = None >> database.py
echo. >> database.py
echo     async def setup(self): >> database.py
echo         self.conn = await aiosqlite.connect(self.db_path) >> database.py
echo         await self.create_tables() >> database.py
echo. >> database.py
echo     async def create_tables(self): >> database.py
echo         await self.conn.execute(''' >> database.py
echo             CREATE TABLE IF NOT EXISTS reminders ( >> database.py
echo                 id INTEGER PRIMARY KEY AUTOINCREMENT, >> database.py
echo                 event_type TEXT NOT NULL, >> database.py
echo                 event_time TIMESTAMP NOT NULL, >> database.py
echo                 notify_time TIMESTAMP NOT NULL, >> database.py
echo                 channel_id INTEGER NOT NULL >> database.py
echo             ) >> database.py
echo         ''') >> database.py
echo         await self.conn.execute(''' >> database.py
echo             CREATE TABLE IF NOT EXISTS users ( >> database.py
echo                 discord_user_id INTEGER PRIMARY KEY, >> database.py
echo                 main_id INTEGER, >> database.py
echo                 alt1_id INTEGER, >> database.py
echo                 alt2_id INTEGER, >> database.py
echo                 alt3_id INTEGER, >> database.py
echo                 farm1_id INTEGER, >> database.py
echo                 farm2_id INTEGER, >> database.py
echo                 farm3_id INTEGER, >> database.py
echo                 farm4_id INTEGER, >> database.py
echo                 farm5_id INTEGER >> database.py
echo             ) >> database.py
echo         ''') >> database.py
echo         await self.conn.execute(''' >> database.py
echo             CREATE TABLE IF NOT EXISTS DKP ( >> database.py
echo                 "Name" TEXT DEFAULT NULL, >> database.py
echo                 "ID" INTEGER PRIMARY KEY, >> database.py
echo                 "Discord_profile" TEXT DEFAULT NULL, >> database.py
echo                 "Kvk_fight_group" INTEGER DEFAULT 0, >> database.py
echo                 "Power_before_matchmaking" INTEGER DEFAULT 0, >> database.py
echo                 "Goal_KP" INTEGER DEFAULT 0, >> database.py
echo                 "Goal_Deads" INTEGER DEFAULT 0, >> database.py
echo                 "Goal_DKP" INTEGER DEFAULT 0, >> database.py
echo                 "KP_before_z5" INTEGER DEFAULT 0, >> database.py
echo                 "Deads_before_z5" INTEGER DEFAULT 0, >> database.py
echo                 "KP_after_z5" INTEGER DEFAULT 0, >> database.py
echo                 "Deads_after_z5" INTEGER DEFAULT 0, >> database.py
echo                 "KP_gained_z5" INTEGER DEFAULT 0, >> database.py
echo                 "Deads_gained_z5" INTEGER DEFAULT 0, >> database.py
echo                 "Altars_gained_KP" INTEGER DEFAULT 0, >> database.py
echo                 "KP_before_7_pass" INTEGER DEFAULT 0, >> database.py
echo                 "Deads_before_7_pass" INTEGER DEFAULT 0, >> database.py
echo                 "KP_after_7_pass" INTEGER DEFAULT 0, >> database.py
echo                 "Deads_after_7_pass" INTEGER DEFAULT 0, >> database.py
echo                 "KP_gained_7_pass" INTEGER DEFAULT 0, >> database.py
echo                 "Deads_gained_7_pass" INTEGER DEFAULT 0, >> database.py
echo                 "KP_before_Kingsland" INTEGER DEFAULT 0, >> database.py
echo                 "Deads_before_Kingsland" INTEGER DEFAULT 0, >> database.py
echo                 "KP_after_Kingsland" INTEGER DEFAULT 0, >> database.py
echo                 "Deads_after_Kingsland" INTEGER DEFAULT 0, >> database.py
echo                 "KP_gained_Kingsland" INTEGER DEFAULT 0, >> database.py
echo                 "Deads_gained_Kingsland" INTEGER DEFAULT 0, >> database.py
echo                 "Changed_DKP" INTEGER DEFAULT 0, >> database.py
echo                 "Reason" TEXT DEFAULT NULL, >> database.py
echo                 "Goal" TEXT DEFAULT NULL >> database.py
echo             ) >> database.py
echo         ''') >> database.py
echo         await self.conn.commit() >> database.py
echo. >> database.py
echo     async def close(self): >> database.py
echo         if self.conn: >> database.py
echo             await self.conn.close() >> database.py

:: Скрипт завершен
echo Setup completed!
pause
