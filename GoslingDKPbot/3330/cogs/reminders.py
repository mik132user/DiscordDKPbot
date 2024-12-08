# cogs/reminders.py

import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import pytz
import logging

from utilits.constants import UPDATE_DATE, ALLOWED_CHANNELS

logger = logging.getLogger(__name__)

class Reminders(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_reminders.start()
        self.user_command_timestamps = {}

    def cog_unload(self):
        self.check_reminders.cancel()

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def remind(self, ctx, event_type: str, date: str, time: str):
        # Rate-limiting: Only one remind command every 10 seconds per user
        now = discord.utils.utcnow()
        last_used = self.user_command_timestamps.get(ctx.author.id, None)
        if last_used and (now - last_used).total_seconds() < 10:
            await ctx.send("Please wait before using this command again.")
            return
        self.user_command_timestamps[ctx.author.id] = now
        
        try:
            # Parse date and time
            event_datetime = datetime.strptime(f"{date} {time}", "%d.%m.%y %H:%M")
            event_datetime = event_datetime.replace(tzinfo=pytz.UTC)
            
            # Ensure the event is in the future
            if event_datetime <= datetime.utcnow().replace(tzinfo=pytz.UTC):
                await ctx.send("The event time must be in the future.")
                return

            # Determine notification time and interval
            if event_type == "altar":
                notify_time = event_datetime - timedelta(hours=2)
                interval = timedelta(hours=86)
            elif event_type == "ruin":
                notify_time = event_datetime - timedelta(hours=1)
                interval = timedelta(hours=40)
            else:
                await ctx.send("Invalid event type. Use 'altar' or 'ruin'. Example: `!remind altar 01.10.24 16:12`.")
                return

            # Database operations with error handling
            try:
                async with self.bot.db.conn.cursor() as cursor:
                    await cursor.execute("""
                        DELETE FROM reminders
                        WHERE event_type = ? AND channel_id = ?
                    """, (event_type, ctx.channel.id))

                    await cursor.execute("""
                        INSERT INTO reminders (event_type, event_time, notify_time, channel_id)
                        VALUES (?, ?, ?, ?)
                    """, (event_type, event_datetime.isoformat(), notify_time.isoformat(), ctx.channel.id))
                    await self.bot.db.conn.commit()

                await ctx.send(f"Reminder set for {event_type} on {event_datetime.strftime('%d.%m.%y %H:%M UTC')} in this channel.")
            
            except Exception as e:
                logger.error(f"Database error: {e}")
                await ctx.send("An error occurred while setting the reminder.")
        
        except ValueError:
            await ctx.send("Invalid date or time format. Use 'DD.MM.YY HH:MM'. Example: `!remind altar 01.10.24 16:12`.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def remind_off(self, ctx, event_type: str):
        if ctx.channel.id not in ALLOWED_CHANNELS:
            return

        try:
            async with self.bot.db.conn.cursor() as cursor:
                await cursor.execute("""
                    DELETE FROM reminders
                    WHERE event_type = ? AND channel_id = ?
                """, (event_type, ctx.channel.id))
                await self.bot.db.conn.commit()

            await ctx.send(f"All upcoming {event_type} reminders in this channel have been cancelled.")
        
        except Exception as e:
            logger.error(f"Database error: {e}")
            await ctx.send("An error occurred while cancelling the reminders.")

    @tasks.loop(minutes=1)
    async def check_reminders(self):
        now = datetime.utcnow().replace(tzinfo=pytz.UTC)
        try:
            async with self.bot.db.conn.cursor() as cursor:
                await cursor.execute("""
                    SELECT id, event_type, event_time, notify_time, channel_id FROM reminders
                    WHERE notify_time <= ?
                """, (now.isoformat(),))
                reminders = await cursor.fetchall()

                for reminder in reminders:
                    reminder_id, event_type, event_time, notify_time, channel_id = reminder
                    event_time = datetime.fromisoformat(event_time).replace(tzinfo=pytz.UTC)

                    channel = self.bot.get_channel(channel_id)
                    if channel:
                        description = f"**Reminder:** {event_type.capitalize()} opens on {event_time.strftime('%d.%m.%y %H:%M UTC')}."
                        embed = discord.Embed(
                            title=f"Event Reminder: {event_type.capitalize()}",
                            description=description,
                            color=discord.Color.red()
                        )
                        # Mention @everyone
                        await channel.send(f"@everyone", embed=embed)

                        next_event_time = event_time + (timedelta(hours=86) if event_type == "altar" else timedelta(hours=40))
                        next_notify_time = next_event_time - (timedelta(hours=2) if event_type == "altar" else timedelta(hours=1))

                        await cursor.execute("""
                            UPDATE reminders
                            SET event_time = ?, notify_time = ?
                            WHERE id = ?
                        """, (next_event_time.isoformat(), next_notify_time.isoformat(), reminder_id))

            await self.bot.db.conn.commit()

        except Exception as e:
            logger.error(f"Error checking reminders: {e}")

    @check_reminders.before_loop
    async def before_check_reminders(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        # Handle command errors
        if isinstance(error, commands.CommandNotFound):
            await ctx.send("Command not found. Please check your input.")
        elif isinstance(error, commands.MissingRequiredArgument):
            # Specific error handling for remind_off command
            if ctx.command.name == 'remind_off':
                await ctx.send("Please provide the event type argument. Example: `!remind_off altar`.")
            else:
                await ctx.send("Please provide all required arguments. Example: `!remind altar 01.10.24 16:12`.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("One of the arguments is invalid. Please check your input. Example: `!remind altar 01.10.24 16:12`.")
        elif isinstance(error, commands.CheckFailure):
            await ctx.send("You do not have permission to use this command.")
        else:
            await ctx.send("An unexpected error occurred. Please try again later.")
            logger.error(f"Error in command '{ctx.command}': {error}")

async def setup(bot):
    await bot.add_cog(Reminders(bot))
