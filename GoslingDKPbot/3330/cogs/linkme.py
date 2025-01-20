# cogs/linkme.py

import discord
from discord.ext import commands
import asyncio

from utilits.constants import ALLOWED_CHANNELS
import logging

logger = logging.getLogger(__name__)

class Linkme(commands.Cog):
    """
    A Cog for managing linking and unlinking player IDs to Discord users.
    """

    def __init__(self, bot):
        """
        Initialize the Linkme Cog.

        Args:
            bot (commands.Bot): The bot instance.
        """
        self.bot = bot
        self.user_command_timestamps = {}

    @commands.command()
    async def linkme(self, ctx, player_id: str):
        """
        Link a player ID to a Discord user's profile.

        Args:
            ctx (commands.Context): The command context.
            player_id: The player ID to link.

        Notes:
            - Allows linking of main, alt, or farm IDs.
            - Enforces rate-limiting of 10 seconds between consecutive uses per user..
        """
        # Rate-limiting: Only one linkme command every 10 seconds per user
        now = discord.utils.utcnow()
        last_used = self.user_command_timestamps.get(ctx.author.id, None)
        if last_used and (now - last_used).total_seconds() < 10:
            await ctx.send("Please wait before using this command again.")
            return
        self.user_command_timestamps[ctx.author.id] = now

        if ctx.channel.id not in ALLOWED_CHANNELS:
            return

        # Validate that the player_id is a valid integer
        try:
            player_id = int(player_id)
        except ValueError:
            await ctx.send("Invalid player ID. Please provide a valid numeric ID. Example: `!linkme 12345`.")
            return

        discord_user_id = ctx.author.id

        try:
            async with self.bot.db.conn.cursor() as cursor:
                # Check if the player ID exists in the DKP table
                await cursor.execute("SELECT ID FROM DKP WHERE ID=?", (player_id,))
                player_in_dkp = await cursor.fetchone()

                if not player_in_dkp:
                    await ctx.send(f"ID {player_id} not found in the DKP table. Please check the entered ID.")
                    return

                # Check if the user already exists in the users table
                await cursor.execute("SELECT * FROM users WHERE discord_user_id=?", (discord_user_id,))
                existing_user = await cursor.fetchone()

                if not existing_user:
                    await cursor.execute("INSERT INTO users (discord_user_id) VALUES (?)", (discord_user_id,))
                    await self.bot.db.conn.commit()
                    existing_user = (discord_user_id, None, None, None, None, None, None, None, None, None)

                linked_ids = existing_user[1:]
                if player_id in linked_ids:
                    await ctx.send(f"ID {player_id} is already linked to your profile.")
                    return

                # Message for selecting type of account
                message = await ctx.send(
                    "Choose an option:\n"
                    "1️⃣ Main\n"
                    "2️⃣ Alt\n"
                    "3️⃣ Farm"
                )

                reactions = ['1️⃣', '2️⃣', '3️⃣']
                for emoji in reactions:
                    await message.add_reaction(emoji)

                def check(reaction, user):
                    return user == ctx.author and str(reaction.emoji) in reactions and reaction.message.id == message.id

                try:
                    reaction, _ = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)

                    if reaction.emoji == '1️⃣':
                        columns_to_check = ["main_id"]
                    elif reaction.emoji == '2️⃣':
                        columns_to_check = ["alt1_id", "alt2_id", "alt3_id"]
                    elif reaction.emoji == '3️⃣':
                        columns_to_check = ["farm1_id", "farm2_id", "farm3_id", "farm4_id", "farm5_id"]

                    # Link the player ID to the user's profile
                    for column in columns_to_check:
                        column_index = {
                            "main_id": 0,
                            "alt1_id": 1,
                            "alt2_id": 2,
                            "alt3_id": 3,
                            "farm1_id": 4,
                            "farm2_id": 5,
                            "farm3_id": 6,
                            "farm4_id": 7,
                            "farm5_id": 8
                        }[column]
                        if linked_ids[column_index] is None:
                            await cursor.execute(f"UPDATE users SET {column}=? WHERE discord_user_id=?", (player_id, discord_user_id))
                            await self.bot.db.conn.commit()
                            await ctx.send(f"ID {player_id} successfully linked to your profile as {column.replace('_id', '').capitalize()}.")
                            return

                    await ctx.send("All slots for the selected option are already occupied.")

                except asyncio.TimeoutError:
                    await ctx.send("Selection time has expired.")
        
        except Exception as e:
            logger.error(f"Database error: {e}")
            await ctx.send("An error occurred while linking the ID.")

    @commands.command()
    async def unlinkme(self, ctx, player_id: str):
        """
        Unlink a player ID from a Discord user's profile.

        Args:
            ctx (commands.Context): The command context.
            player_id (str): The player ID to unlink.

        Notes:
            - Validates that the player ID is numeric.
            - Removes the association of the player ID with the user's profile in the database.
            - Enforces rate-limiting of 10 seconds between consecutive uses per user.
        """
        now = discord.utils.utcnow()
        last_used = self.user_command_timestamps.get(ctx.author.id, None)
        if last_used and (now - last_used).total_seconds() < 10:
            await ctx.send("Please wait before using this command again.")
            return
        self.user_command_timestamps[ctx.author.id] = now

        if ctx.channel.id not in ALLOWED_CHANNELS:
            return

        try:
            player_id = int(player_id)
        except ValueError:
            await ctx.send("Invalid player ID. Please provide a valid numeric ID. Example: `!unlinkme 12345`.")
            return

        discord_user_id = ctx.author.id

        try:
            async with self.bot.db.conn.cursor() as cursor:
                await cursor.execute("""
                    SELECT main_id, alt1_id, alt2_id, alt3_id, farm1_id, farm2_id, farm3_id, farm4_id, farm5_id
                    FROM users
                    WHERE discord_user_id=?
                """, (discord_user_id,))
                linked_ids = await cursor.fetchone()

                if not linked_ids:
                    await ctx.send("You have no linked IDs.")
                    return

                columns = ["main_id", "alt1_id", "alt2_id", "alt3_id", "farm1_id", "farm2_id", "farm3_id", "farm4_id", "farm5_id"]
                found = False

                for column, linked_id in zip(columns, linked_ids):
                    if linked_id == player_id:
                        await cursor.execute(f"UPDATE users SET {column}=NULL WHERE discord_user_id=?", (discord_user_id,))
                        await self.bot.db.conn.commit()
                        await ctx.send(f"ID {player_id} successfully unlinked from your Discord profile.")
                        found = True
                        break

                if not found:
                    await ctx.send(f"ID {player_id} not found among your linked IDs.")
        
        except Exception as e:
            logger.error(f"Database error: {e}")
            await ctx.send("An error occurred while unlinking the ID.")

    @linkme.error
    async def linkme_error(self, ctx, error):
        """
        Handle errors for the linkme command.

        Args:
            ctx (commands.Context): The command context.
            error (commands.CommandError): The error raised during command execution.
        """
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please provide a player ID. Example: `!linkme 12345`.")
        elif isinstance(error, commands.CommandNotFound):
            await ctx.send("Command not found. Please check your input.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid argument provided. Please ensure you are using a numeric player ID. Example: `!linkme 12345`.")
        else:
            await ctx.send("An unexpected error occurred. Please try again later.")
            logger.error(f"Error in command '{ctx.command}': {error}")

    @unlinkme.error
    async def unlinkme_error(self, ctx, error):
        """
        Handle errors for the unlinkme command.

        Args:
            ctx (commands.Context): The command context.
            error (commands.CommandError): The error raised during command execution.
        """
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please provide a player ID. Example: `!unlinkme 12345`.")
        elif isinstance(error, commands.CommandNotFound):
            await ctx.send("Command not found. Please check your input.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Invalid argument provided. Please ensure you are using a numeric player ID. Example: `!unlinkme 12345`.")
        else:
            await ctx.send("An unexpected error occurred. Please try again later.")
            logger.error(f"Error in command '{ctx.command}': {error}")

async def setup(bot):
    """
    Setup function to add the Linkme Cog to the bot.

    Args:
        bot (commands.Bot): The bot instance.
    """
    await bot.add_cog(Linkme(bot))
