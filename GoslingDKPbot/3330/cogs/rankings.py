import discord
from discord.ext import commands
from discord.ui import View, Button
from utilits.constants import UPDATE_DATE, ALLOWED_CHANNELS
import logging
import asyncio

logger = logging.getLogger(__name__)

class Rankings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Anti-DDoS rate limiting: Dictionary to track command usage
        self.user_command_timestamps = {}

    @commands.command()
    async def top(self, ctx, number: int = 10):
        # Implement rate limiting (1 command per 10 seconds per user)
        now = discord.utils.utcnow()
        last_used = self.user_command_timestamps.get(ctx.author.id, None)
        if last_used and (now - last_used).total_seconds() < 10:
            await ctx.send("Please wait before using this command again.")
            return
        self.user_command_timestamps[ctx.author.id] = now

        try:
            if ctx.channel.id not in ALLOWED_CHANNELS:
                await ctx.send("This command is not allowed in this channel.")
                return

            # Limit the number of players
            if number < 1 or number > 25:
                await ctx.send("Please specify a number between 1 and 25.")
                return

            # Create the buttons for selecting ranking categories
            view = RankSelectionView(self.bot, ctx.author, number)
            message = await ctx.send("Choose a ranking category:", view=view)

            # Save the message for future interactions
            view.message = message

        except Exception as e:
            logger.error(f'Error in top command: {e}')
            await ctx.send("An error occurred while fetching the top rankings.")


class RankSelectionView(View):
    def __init__(self, bot, author, number):
        super().__init__(timeout=60)
        self.bot = bot
        self.author = author
        self.number = number
        self.column_mapping = {
            'Starting Power': 'Power_before_matchmaking',
            'Deads Gained': '(Deads_gained_z5 + Deads_gained_Kingsland + Deads_gained_7_pass)',
            'KP Gained': '(KP_gained_z5 + KP_gained_Kingsland + Altars_gained_KP + KP_gained_7_pass)',
            'Score': 'Changed_DKP'
        }
        
        for label, column in self.column_mapping.items():
            button = Button(label=label, style=discord.ButtonStyle.primary)
            button.callback = lambda interaction, col=column: self.show_ranking(interaction, col)
            self.add_item(button)

    async def interaction_check(self, interaction):
        """Checks whether the user who pressed the button is the same as the one who invoked the command."""
        if interaction.user != self.author:
            await interaction.response.send_message("You cannot interact with these buttons.", ephemeral=True)
            return False
        return True

    async def show_ranking(self, interaction, column_name):
        if not await self.interaction_check(interaction):
            return
            
        try:
            async with self.bot.db.conn.cursor() as cursor:
                query = f"""
                    SELECT Name, ID, {column_name} 
                    FROM DKP 
                    ORDER BY {column_name} DESC
                """
                await cursor.execute(query)
                all_players = await cursor.fetchall()

            if not all_players:
                await interaction.response.send_message("Failed to retrieve data about the top players.", ephemeral=True)
                return

            cleaned_players = [(name, player_id, self.safe_int_conversion(value)) for name, player_id, value in all_players]
            sorted_players = sorted(cleaned_players, key=lambda x: -x[2])[:self.number]
            namename = self.get_column_display_name(column_name)

            embed = discord.Embed(
                title=f"Top {self.number} by {namename}",
                description=f"Here are the top {self.number} players sorted by {namename}.",
                color=discord.Color.gold()
            )

            for index, (name, player_id, value_int) in enumerate(sorted_players):
                trophy = self.get_trophy(index)
                embed.add_field(name=f"{trophy} {name}", value=f"{value_int:,}", inline=False)

            embed.set_footer(text=f'Updated - {UPDATE_DATE}')
            await interaction.response.send_message(embed=embed)

        except Exception as e:
            logger.error(f'Error in show_ranking: {e}')
            await interaction.response.send_message("An error occurred while fetching the top players.", ephemeral=True)

    def get_column_display_name(self, column_name):
        """Maps column names to human-readable display names for the ranking categories."""
        return {
            'Power_before_matchmaking': "Starting Power",
            '(Deads_gained_z5 + Deads_gained_Kingsland + Deads_gained_7_pass)': "Deads Gained",
            '(KP_gained_z5 + KP_gained_Kingsland + Altars_gained_KP + KP_gained_7_pass)': "KP Gained",
            'Changed_DKP': 'Score'
        }.get(column_name, column_name.replace('_', ' ').capitalize())

    def safe_int_conversion(self, value):
        """Converts a value to an integer, ignoring any fractional part."""
        try:
            if isinstance(value, str):
                value_clean = value.replace(' ', '').replace(',', '.')
                return int(float(value_clean))
            else:
                return int(value)
        except (ValueError, TypeError):
            return 0

    def get_trophy(self, index):
        """Assigns a trophy emoji or position number based on ranking index."""
        trophies = [":first_place:", ":second_place:", ":third_place:"]
        return trophies[index] if index < 3 else f"{index + 1}:"

    async def on_timeout(self):
        """Disable the view after timeout."""
        for child in self.children:
            child.disabled = True
        if hasattr(self, 'message'):
            await self.message.edit(view=self)
            
async def setup(bot):
    await bot.add_cog(Rankings(bot))
