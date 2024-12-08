import discord
from discord.ext import commands, tasks
from discord.ui import View, Button
from datetime import datetime, timedelta
import aiosqlite
import asyncio
import pytz


ALLOWED_CHANNELS = [1285878000876916756]  # Здесь указывайте ID ваших каналов
UPDATE_DATE = 'Updated - 16.09.24'


DATABASE = 'DKP3330.db'
 

intents = discord.Intents.default()
intents.message_content = True  # Enable intent to receive message content

bot = commands.Bot(command_prefix='!', intents=intents)
 

async def setup_database():
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                event_time TIMESTAMP NOT NULL,
                notify_time TIMESTAMP NOT NULL,
                channel_id INTEGER NOT NULL
            )
        ''')
        await db.commit()


@bot.command()
@commands.has_permissions(administrator=True)
async def remind(ctx, event_type: str, date: str, time: str):
    try:
        # Парсинг даты и времени
        event_datetime = datetime.strptime(f"{date} {time}", "%d.%m.%y %H:%M")
        event_datetime = event_datetime.replace(tzinfo=pytz.UTC)

        # Определение времени уведомления
        if event_type == "altar":
            notify_time = event_datetime - timedelta(hours=2)
            interval = timedelta(hours=86)  # Интервал для алтари
        elif event_type == "ruin":
            notify_time = event_datetime - timedelta(hours=1)
            interval = timedelta(hours=40)  # Интервал для руин
        else:
            await ctx.send("Invalid event type. Use 'altar' or 'ruin'.")
            return

        async with aiosqlite.connect(DATABASE) as db:
            cursor = await db.cursor()
            # Удаление старой записи, если существует
            await cursor.execute("""
                DELETE FROM reminders
                WHERE event_type = ? AND channel_id = ?
            """, (event_type, ctx.channel.id))

            # Вставка нового напоминания
            await cursor.execute("""
                INSERT INTO reminders (event_type, event_time, notify_time, channel_id)
                VALUES (?, ?, ?, ?)
            """, (event_type, event_datetime.isoformat(), notify_time.isoformat(), ctx.channel.id))
            await db.commit()

        await ctx.send(f"Reminder set for {event_type} on {event_datetime.strftime('%d.%m.%y %H:%M UTC')} in this channel.")

    except ValueError:
        await ctx.send("Invalid date or time format. Use 'DD.MM.YY HH:MM'.")


@bot.command()
@commands.has_permissions(administrator=True)
async def remind_off(ctx, event_type: str):
    async with aiosqlite.connect(DATABASE) as db:
        cursor = await db.cursor()
        await cursor.execute("""
            DELETE FROM reminders
            WHERE event_type = ? AND channel_id = ?
        """, (event_type, ctx.channel.id))
        await db.commit()

    await ctx.send(f"All upcoming {event_type} reminders in this channel have been cancelled.")


@tasks.loop(minutes=1)
async def check_reminders():
    now = datetime.utcnow().replace(tzinfo=pytz.UTC)
    async with aiosqlite.connect(DATABASE) as db:
        cursor = await db.cursor()
        await cursor.execute("""
            SELECT id, event_type, event_time, notify_time, channel_id FROM reminders
            WHERE notify_time <= ?
        """, (now.isoformat(),))
        reminders = await cursor.fetchall()

        for reminder in reminders:
            reminder_id, event_type, event_time, notify_time, channel_id = reminder
            event_time = datetime.fromisoformat(event_time).replace(tzinfo=pytz.UTC)
            notify_time = datetime.fromisoformat(notify_time).replace(tzinfo=pytz.UTC)

            # Отправка уведомления
            channel = bot.get_channel(channel_id)
            if channel:
                if event_type == "altar":
                    description = f"**Reminder:** Altar event is scheduled for {event_time.strftime('%d.%m.%y %H:%M UTC')}."
                    next_notify_time = now + timedelta(hours=86)  # Следующее уведомление через 86 часов
                elif event_type == "ruin":
                    description = f"**Reminder:** Ruin event is scheduled for {event_time.strftime('%d.%m.%y %H:%M UTC')}."
                    next_notify_time = now + timedelta(hours=40)  # Следующее уведомление через 40 часов

                embed = discord.Embed(
                    title=f"Event Reminder: {event_type.capitalize()}",
                    description=description,
                    color=discord.Color.red()
                )
                await channel.send('@Member', embed=embed)

            # Обновление времени следующего напоминания
            async with aiosqlite.connect(DATABASE) as db:
                cursor = await db.cursor()
                await cursor.execute("""
                    UPDATE reminders
                    SET event_time = ?, notify_time = ?
                    WHERE id = ?
                """, (event_time.isoformat(), next_notify_time.isoformat(), reminder_id))
                await db.commit()


class LinkmeView(discord.ui.View):
    def __init__(self, player_id, discord_user_id):
        super().__init__()
        self.player_id = player_id
        self.discord_user_id = discord_user_id

    async def on_timeout(self):
        await self.message.edit(content="Selection time has expired.")

    @discord.ui.button(label='main', style=discord.ButtonStyle.primary)
    async def main_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self.handle_selection(interaction, "main_id")

    @discord.ui.button(label='alt', style=discord.ButtonStyle.primary)
    async def alt_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self.handle_selection(interaction, "alt1_id", "alt2_id", "alt3_id")

    @discord.ui.button(label='farm', style=discord.ButtonStyle.primary)
    async def farm_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self.handle_selection(interaction, "farm1_id", "farm2_id", "farm3_id", "farm4_id", "farm5_id")

    async def handle_selection(self, interaction: discord.Interaction, *columns):
        async with self.bot.db_conn.cursor() as cursor:
            for column in columns:
                await cursor.execute(f"SELECT {column} FROM users WHERE discord_user_id=?", (self.discord_user_id,))
                existing_id = await cursor.fetchone()

                if existing_id and existing_id[0] is not None:
                    continue  # If already occupied, go to the next column

                # If found free space, update it
                await cursor.execute(f"UPDATE users SET {column}=? WHERE discord_user_id=?", (self.player_id, self.discord_user_id))
                await self.bot.db_conn.commit()

                # Change the original message after selection
                await interaction.response.edit_message(content=f"Profile successfully linked to ID {self.player_id} in column {column}.")
                return

            # If all columns are occupied
            await interaction.response.edit_message(content="All cells for this option are already occupied.")


@bot.command()
async def linkme(ctx, player_id: int):
    if ctx.channel.id not in ALLOWED_CHANNELS:
        return
    discord_user_id = ctx.author.id  # Discord user ID

    async with aiosqlite.connect(DATABASE) as db:
        cursor = await db.cursor()

        # Check if player_id is in the DKP table
        await cursor.execute("SELECT ID FROM DKP WHERE ID=?", (player_id,))
        player_in_dkp = await cursor.fetchone()

        if not player_in_dkp:
            await ctx.send(f"ID {player_id} not found in the DKP table. Please check the entered ID.")
            return

        # Check if there is already a link for this Discord user
        await cursor.execute("SELECT discord_user_id FROM users WHERE discord_user_id=?", (discord_user_id,))
        existing_user = await cursor.fetchone()

        if not existing_user:
            # If the user doesn't exist, create a new record
            await cursor.execute("INSERT INTO users (discord_user_id) VALUES (?)", (discord_user_id,))
            await db.commit()

        # Check if this player_id is already linked to the user
        await cursor.execute("""
            SELECT main_id, alt1_id, alt2_id, alt3_id, farm1_id, farm2_id, farm3_id, farm4_id, farm5_id
            FROM users
            WHERE discord_user_id=?
        """, (discord_user_id,))
        linked_ids = await cursor.fetchone()

        # If player_id is already linked to the user, inform them
        if player_id in linked_ids:
            await ctx.send(f"ID {player_id} is already linked to your profile.")
            return

        # Send a message with selection options
        message = await ctx.send("Choose an option:\n"
                                 "1️⃣ Main"
                                 "2️⃣ Alt"
                                 "3️⃣ Farm")

        # Add reactions to the message
        for emoji in ['1️⃣', '2️⃣', '3️⃣']:
            await message.add_reaction(emoji)

        # Function to process choice through reactions
        def check(reaction, user):
            return user == ctx.author and reaction.message == message

        try:
            reaction, _ = await bot.wait_for('reaction_add', timeout=60.0, check=check)

            if reaction.emoji == '1️⃣':
                column = "main_id"
                columns_to_check = [column]
            elif reaction.emoji == '2️⃣':
                columns_to_check = ["alt1_id", "alt2_id", "alt3_id"]
            elif reaction.emoji == '3️⃣':
                columns_to_check = ["farm1_id", "farm2_id", "farm3_id", "farm4_id", "farm5_id"]

            # Check available cells in selected columns
            for column in columns_to_check:
                await cursor.execute(f"SELECT {column} FROM users WHERE discord_user_id=?", (discord_user_id,))
                existing_id = await cursor.fetchone()

                if not existing_id or existing_id[0] is None:
                    # If the column is empty, link player_id to this column
                    await cursor.execute(f"UPDATE users SET {column}=? WHERE discord_user_id=?", (player_id, discord_user_id))
                    await db.commit()
                    await ctx.send(f"ID {player_id} successfully linked to your profile.")
                    return

            # If all cells for the selected option are occupied
            await ctx.send("All cells for the selected option are already occupied.")

        except asyncio.TimeoutError:
            await ctx.send("Selection time has expired.")


@bot.command()
async def unlinkme(ctx, player_id: int):
    if ctx.channel.id not in ALLOWED_CHANNELS:
        return
    discord_user_id = ctx.author.id  # Discord user ID

    async with aiosqlite.connect(DATABASE) as db:
        cursor = await db.cursor()

        # Check if there is a link between Discord user and ID
        columns = ["main_id", "alt1_id", "alt2_id", "alt3_id", "farm1_id", "farm2_id", "farm3_id", "farm4_id", "farm5_id"]
        found = False

        for column in columns:
            await cursor.execute(f"SELECT {column} FROM users WHERE discord_user_id=?", (discord_user_id,))
            existing_id = await cursor.fetchone()

            if existing_id and existing_id[0] == player_id:
                # If ID is found in one of the columns, remove it
                await cursor.execute(f"UPDATE users SET {column}=NULL WHERE discord_user_id=?", (discord_user_id,))
                await db.commit()
                await ctx.send(f"ID {player_id} successfully unlinked from Discord profile.")
                found = True
                break

        if not found:
            await ctx.send(f"ID {player_id} not found among linked IDs.")

    # Class to represent reaction options
    class StatsView(discord.ui.View):
        def __init__(self, message, discord_user_id, available_columns, player_ids):
            super().__init__()
            self.message = message
            self.discord_user_id = discord_user_id
            self.available_columns = available_columns
            self.player_ids = player_ids  

        async def on_timeout(self):
            await self.message.edit(content="Selection time has expired.", view=None)

        async def handle_selection(self, interaction: discord.Interaction, column):
            async with aiosqlite.connect(DATABASE) as db:
                cursor = await db.cursor()
                await cursor.execute(f"SELECT {column} FROM users WHERE discord_user_id=?", (self.discord_user_id,))
                player_id = await cursor.fetchone()

                if player_id and player_id[0]:
                    await cursor.execute("SELECT * FROM DKP WHERE ID=?", (player_id[0],))
                    player_data = await cursor.fetchone()

                    if player_data:
                        # Создание Embed для красивого отображения данных
                        embed = discord.Embed(
                            title=f"Player Stats - {player_data[2]}",
                            description=f"Statistics for player ID: {player_data[1]}",
                            color=discord.Color.blue()
                        )
                        embed.add_field(name="Rank", value=player_data[0], inline=True)
                        embed.add_field(name="Starting Power", value=f"{player_data[3]:,}", inline=True)
                        embed.add_field(name="KP Gained", value=f"{player_data[4]:,}", inline=True)
                        embed.add_field(name="Dead Troops Gained", value=f"{player_data[5]:,}", inline=True)
                        embed.add_field(name="Dead Requirements", value=f"{player_data[6]:,}", inline=True)
                        embed.add_field(name="KP Requirements", value=f"{player_data[7]:,}", inline=True)
                        embed.add_field(name="Score", value=f"{player_data[8]:,}", inline=True)
                        embed.add_field(name="Score Goal", value=f"{player_data[9]:,}", inline=True)
                        embed.add_field(name="Goal Reached", value=player_data[10], inline=True)

                        embed.set_footer(text=f"{UPDATE_DATE}")
                        await interaction.channel.send(embed=embed)
                    else:
                        await interaction.channel.send(content="Player data not found.")
                else:
                    await interaction.channel.send(content="The selected account is not registered.")

        @discord.ui.button(label='Get Stats', style=discord.ButtonStyle.primary)
        async def get_stats_button(self, button: discord.ui.Button, interaction: discord.Interaction):
            selected_column = self.available_columns[0]
            await self.handle_selection(selected_column)
            self.stop()


@bot.command()
async def stats(ctx):
    if ctx.channel.id not in ALLOWED_CHANNELS:
        return

    discord_user_id = ctx.author.id  # ID пользователя в Discord

    async with aiosqlite.connect(DATABASE) as db:
        cursor = await db.cursor()

        await cursor.execute("""
            SELECT main_id, alt1_id, alt2_id, alt3_id, farm1_id, farm2_id, farm3_id, farm4_id, farm5_id 
            FROM users 
            WHERE discord_user_id=?
        """, (discord_user_id,))
        user_data = await cursor.fetchone()

        if user_data:
            available_columns = []
            player_ids = []
            column_names = []

            columns = ["main_id", "alt1_id", "alt2_id", "alt3_id", "farm1_id", "farm2_id", "farm3_id", "farm4_id", "farm5_id"]
            account_names = ["Main", "Alt 1", "Alt 2", "Alt 3", "Farm 1", "Farm 2", "Farm 3", "Farm 4", "Farm 5"]

            for idx, player_id in enumerate(user_data):
                if player_id:
                    available_columns.append(columns[idx])
                    player_ids.append(player_id)
                    column_names.append(account_names[idx])

            if not available_columns:
                await ctx.send("You have no registered accounts.")
                return

            if len(available_columns) == 1:
                # Если привязан только один аккаунт, сразу показываем статистику
                selected_column = available_columns[0]
                selected_player_id = player_ids[0]
            else:
                # Если привязано больше одного аккаунта, показываем выбор
                message_content = "Choose an account to display statistics:\n" + \
                                  "\n".join([f"{emoji} {name} (ID: {player_id})"
                                             for emoji, name, player_id in zip(['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣'], 
                                                                               column_names, player_ids)])

                message = await ctx.send(message_content)

                for emoji in ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣'][:len(available_columns)]:
                    await message.add_reaction(emoji)

                def check(reaction, user):
                    return user == ctx.author and str(reaction.emoji) in ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣']

                try:
                    reaction, _ = await bot.wait_for('reaction_add', timeout=60.0, check=check)
                    selected_index = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣'].index(str(reaction.emoji))
                    selected_column = available_columns[selected_index]
                    selected_player_id = player_ids[selected_index]

                except asyncio.TimeoutError:
                    await ctx.send("Selection time has expired.")
                    return

            # Получение данных и отображение статистики
            await cursor.execute("SELECT * FROM DKP WHERE ID=?", (selected_player_id,))
            player_data = await cursor.fetchone()

            if player_data:
                KPGAINED = player_data[13] + player_data[15] + player_data[20]
                DEADSGAINED = player_data[21] + player_data[14]

                # Создание Embed для ответа
                embed = discord.Embed(
                    title=f"Player Stats - {player_data[1]}",
                    description=f"Statistics for player ID: {player_data[2]}",
                    color=discord.Color.green()
                )
                embed.add_field(name="Rank", value=player_data[0], inline=True)
                embed.add_field(name="Starting Power", value=f"{int(player_data[5]):,}", inline=True)
                embed.add_field(name="KP Gained", value=KPGAINED, inline=True)
                embed.add_field(name="Dead Troops Gained", value=DEADSGAINED, inline=True)
                embed.add_field(name="Dead Requirements", value=f"{int(player_data[7]):,}", inline=True)
                embed.add_field(name="KP Requirements", value=f"{int(player_data[6]):,}", inline=True)
                embed.add_field(name="Score DKP", value=f"{int(player_data[23]):,}", inline=True)
                embed.add_field(name="Score Goal DKP", value=f"{int(player_data[8]):,}", inline=True)
                embed.add_field(name="Goal Reached", value=player_data[25], inline=True)

                embed.set_footer(text=f"{UPDATE_DATE}")
                await ctx.send(embed=embed)  # Отправка сообщения с Embed
            else:
                await ctx.send("Player data not found.")  # Ошибка

        else:
            await ctx.send("No data found for your Discord user ID.")

class RankSelectionView(View):
    def __init__(self, number, column_name):
        super().__init__(timeout=60)
        self.number = number
        self.column_name = column_name

    async def on_timeout(self):
        await self.message.edit(content="Selection time has expired.", view=None)

    async def handle_selection(self, interaction: discord.Interaction):
        # Выполнение SQL-запроса для получения данных
        async with aiosqlite.connect(DATABASE) as db:
            cursor = await db.cursor()

            # Получение данных топ игроков по выбранному столбцу
            await cursor.execute(f"""
                SELECT Name, ID, {self.column_name} 
                FROM DKP 
                ORDER BY {self.column_name} DESC 
                LIMIT ?
            """, (self.number,))
            top_players = await cursor.fetchall()

            if not top_players:
                await interaction.response.send_message("Failed to retrieve data about the top players.", ephemeral=True)
                return

            # Определение наименования столбца
            if self.column_name == '(KPgainedZ5 + KPgainedKingsland + ALTARS)':
                namename = "KP Gained"
            elif self.column_name == '(DEADSgainedZ5 + DeadsgainedKingsland)':
                namename = "Deads Gained"
            elif self.column_name == 'Power':
                namename = 'Starting Power'
            elif self.column_name == 'ChangedDKP':
                namename = 'Score'
            else:
                namename = self.column_name.replace('_', ' ').capitalize()

            # Формирование Embed для красивого вывода
            embed = discord.Embed(
                title=f"Top {self.number} by {namename}",
                description=f"Here are the top {self.number} players sorted by {namename}.",
                color=discord.Color.gold()
            )

            # Сортировка игроков по значениям в Python для обеспечения корректного ранжирования
            sorted_players = sorted(top_players, key=lambda x: -int(x[2]))  # сортируем по значению в убывающем порядке

            # Присвоение рангов и формирование сообщения
            current_rank = 1
            for index, (name, player_id, value) in enumerate(sorted_players):
                try:
                    value_int = int(value)
                    if value_int <= 0:
                        value_int = 0
                except ValueError:
                    value_int = 0

                # Присвоение трофеев для первых трех мест
                if index == 0:
                    trophy = ":first_place:"
                elif index == 1:
                    trophy = ":second_place:"
                elif index == 2:
                    trophy = ":third_place:"
                else:
                    trophy = f"{current_rank}:"
                
                # Добавление поля в Embed
                embed.add_field(name=f"{trophy} {name}", value=f"{value_int:,}", inline=False)

                # Увеличение ранга
                current_rank += 1

            embed.set_footer(text="Updated - 16.09.24")

            # Отправка сообщения с результатом
            await interaction.response.send_message(embed=embed)


async def show_ranking(interaction, number, column_name):
    view = RankSelectionView(number, column_name)
    await view.handle_selection(interaction)


@bot.command()
async def top(ctx, number: int = 10):
    if ctx.channel.id not in ALLOWED_CHANNELS:
        return

    # Ограничение числа участников рейтинга от 1 до 30
    if number < 1 or number > 25:
        await ctx.send("Please specify a number between 1 and 25.")
        return

    # Определяем колонки, которые можно выбрать для рейтинга
    available_columns = {
        'Starting Power': 'Power',
        'Deads Gained': '(DEADSgainedZ5 + DeadsgainedKingsland)',
        'KP Gained': '(KPgainedZ5 + KPgainedKingsland + ALTARS)',
        'Score': 'ChangedDKP'
    }

    # Создание списка кнопок для выбора метрики
    buttons_view = View(timeout=60)
    for label, column in available_columns.items():
        button = Button(label=label, style=discord.ButtonStyle.primary)
        button.callback = lambda interaction, col=column: show_ranking(interaction, number, col)
        buttons_view.add_item(button)

    # Сообщение с кнопками
    await ctx.send("Choose a ranking category:", view=buttons_view)


@bot.event
async def on_ready():
    bot.db_conn = await aiosqlite.connect(DATABASE)
    print(f'Connected to database {DATABASE}')
    await setup_database()
    check_reminders.start()


bot.run('')