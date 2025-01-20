import os
import discord
from discord.ext import commands
import aiosqlite
import asyncio
import logging
from utilits.constants import UPDATE_DATE, ALLOWED_CHANNELS

logger = logging.getLogger(__name__)

class PlayerStats(commands.Cog):
    """
    A cog for handling player statistics retrieval and display.
    """
    def __init__(self, bot):
        """
        Initialize the PlayerStats cog.

        Args:
            bot (commands.Bot): The Discord bot instance.
        """
        self.bot = bot
        self.user_command_timestamps = {}

    @commands.command()
    async def stats(self, ctx):
        """
        Retrieve and display player statistics.

        This command retrieves statistics for a user’s linked accounts from the database and displays them in an embed.

        Args:
            ctx (commands.Context): The command context.
        """
        # Rate-limiting: Only one stats command every 10 seconds per user
        now = discord.utils.utcnow()
        last_used = self.user_command_timestamps.get(ctx.author.id, None)
        self.user_command_timestamps[ctx.author.id] = now

        if ctx.channel.id not in ALLOWED_CHANNELS:
            await ctx.send("This command is not available in this channel.")
            return

        discord_user_id = ctx.author.id
        DATABASE = os.getenv('DATABASE')

        try:
            async with aiosqlite.connect(DATABASE) as db:
                cursor = await db.cursor()

                # Fetch user data
                await cursor.execute("""
                    SELECT main_id, alt1_id, alt2_id, alt3_id, farm1_id, farm2_id, farm3_id, farm4_id, farm5_id 
                    FROM users 
                    WHERE discord_user_id=?
                """, (discord_user_id,))
                user_data = await cursor.fetchone()

                if not user_data:
                    await ctx.send("You do not have any registered accounts.")
                    return

                available_columns = []
                player_ids = []
                column_names = []

                # Determine which accounts are linked
                columns = ["main_id", "alt1_id", "alt2_id", "alt3_id", "farm1_id", "farm2_id", "farm3_id", "farm4_id", "farm5_id"]
                account_names = ["Main", "Alt 1", "Alt 2", "Alt 3", "Farm 1", "Farm 2", "Farm 3", "Farm 4", "Farm 5"]

                for idx, player_id in enumerate(user_data):
                    if player_id:
                        available_columns.append(columns[idx])
                        player_ids.append(player_id)
                        column_names.append(account_names[idx])

                if not available_columns:
                    await ctx.send("You do not have any registered accounts.")
                    return

                # If only one account is linked, select it automatically
                if len(available_columns) == 1:
                    selected_column = available_columns[0]
                    selected_player_id = player_ids[0]
                else:
                    # Message for selecting an account
                    message_content = "Select an account to view statistics:\n" + \
                                      "\n".join([f"{emoji} **{name}** (ID: **{player_id}**)"
                                                 for emoji, name, player_id in zip(['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣'], 
                                                                                   column_names, player_ids)])

                    message = await ctx.send(message_content)

                    for emoji in ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣'][:len(available_columns)]:
                        await message.add_reaction(emoji)

                    def check(reaction, user):
                        """
                        Check if the reaction is valid and from the command invoker.

                        Args:
                            reaction (discord.Reaction): The reaction object.
                            user (discord.User): The user who reacted.

                        Returns:
                            bool: True if valid, False otherwise.
                        """
                        return user == ctx.author and str(reaction.emoji) in ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣']

                    try:
                        reaction, _ = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
                        selected_index = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣'].index(str(reaction.emoji))
                        selected_column = available_columns[selected_index]
                        selected_player_id = player_ids[selected_index]

                    except asyncio.TimeoutError:
                        await ctx.send("Time to select an account has expired.")
                        return

                # Fetch statistics for the selected player
                await cursor.execute("SELECT * FROM DKP WHERE ID=?", (selected_player_id,))
                player_data = await cursor.fetchone()

                if player_data is None:
                    await ctx.send("No data found for the selected player.")
                    return

                # Safe extraction of player data with default values
                def safe_get(value, default=0):
                    """
                    Safely get a value, returning a default if the value is None.

                    Args:
                        value: The value to check.
                        default: The default value to return if value is None.

                    Returns:
                        The value or the default.
                    """
                    return value if value is not None else default

                try:
                    rank = safe_get(player_data[0])  # Rank
                    player_name = player_data[1]  # Player name
                    player_id = player_data[2]  # Player ID
                    starting_power = safe_get(player_data[5])  # Starting Power
                    kp_requirements = safe_get(player_data[6])  # KP Requirements
                    kill_requirements = safe_get(player_data[7])  # Kill Requirements
                    target_dkp_points = safe_get(player_data[8])  # Target DKP Points
                    dkp_points = safe_get(player_data[28])  # DKP Points
                    kp_gained_z5 = safe_get(player_data[13])  # KP Gained from Z5
                    kp_gained_altar = safe_get(player_data[15])  # KP Gained from altars
                    kp_gained_pass_7 = safe_get(player_data[20])
                    kp_gained_kingsland = safe_get(player_data[26])
                    troops_killed_z5 = safe_get(player_data[14])  # Troops Killed from Z5
                    troops_killed_pass_7 = safe_get(player_data[21])
                    troops_killed_kingsland = safe_get(player_data[27])

                    # Calculate KP Gained
                    kp_gained = kp_gained_z5 + kp_gained_altar + kp_gained_pass_7 + kp_gained_kingsland
                    troops_killed = troops_killed_z5 + troops_killed_pass_7 + troops_killed_kingsland

                    # Calculate Goal Achieved
                    if target_dkp_points > 0:
                        goal_achieved = (dkp_points / target_dkp_points) * 100
                    else:
                        goal_achieved = 0  # If no target DKP points are set, set goal to 0%

                    # Create embed for the player statistics
                    embed = discord.Embed(
                        title=f"Player Stats - {player_name}",
                        description=f"Statistics for player ID: **{player_id}**",
                        color=discord.Color.green()
                    )

                    embed.add_field(name="Rank", value=f"{rank}", inline=True)
                    embed.add_field(name="Starting Power", value=f"{starting_power:,}", inline=True)
                    embed.add_field(name="KP Gained", value=f"{kp_gained:,}", inline=True)

                    embed.add_field(name="Troops Killed", value=f"{troops_killed:,}", inline=True)
                    embed.add_field(name="Dead Requirements", value=f"{kill_requirements:,}", inline=True)
                    embed.add_field(name="KP Requirements", value=f"{kp_requirements:,}", inline=True)

                    embed.add_field(name="DKP Points", value=f"{dkp_points:,}", inline=True)
                    embed.add_field(name="Target DKP Points", value=f"{target_dkp_points:,}", inline=True)
                    embed.add_field(name="Goal Achieved", value=f"{goal_achieved:.2f}%", inline=True)

                    # Add the footer with the update date
                    embed.set_footer(text=f"Updated - {UPDATE_DATE}")

                    # Send the embed message
                    await ctx.send(embed=embed)

                except Exception as e:
                    logger.error(f"Error extracting player data: {e}")
                    await ctx.send("Incomplete data for player statistics.")
                    return

        except Exception as e:
            logger.error(f"Database error: {e}")
            await ctx.send("An error occurred while retrieving player statistics.")

async def setup(bot):
    """
    Add the PlayerStats cog to the bot.

    Args:
        bot (commands.Bot): The Discord bot instance.
    """
    await bot.add_cog(PlayerStats(bot))
