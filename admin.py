import discord
from discord.ext import commands

import os, sys
from dotenv import load_dotenv

from main import colors

load_dotenv()
ADMIN_ROLE_ID = int(os.getenv('ADMIN_ROLE'))

class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @property
    def player(self):
        return getattr(self.bot, "player", None)

    @property
    def ffmpeg_path(self):
        return getattr(self.bot, "ffmpeg_path", None)

    async def cog_check(self, ctx):
        if not ctx.guild:
            return False

        role = ctx.guild.get_role(ADMIN_ROLE_ID)
        if role is None:
            return True

        return role in ctx.author.roles

    @commands.command(name="leave", aliases=["disconnect", "dc"])
    async def leave(self, ctx):
        vc = ctx.guild.voice_client
        if not vc:
            return await ctx.reply("Not in a vc.")

        self.player.queue.clear()
        self.player.current_song = None
        self.player.is_playing = False
        self.player.is_paused = False

        await vc.disconnect()
        await ctx.send("Disconnected.")

    @commands.command(name="stop")
    async def stop(self, ctx):
        vc = ctx.guild.voice_client
        if not vc:
            return await ctx.reply("Not connected to vc.")

        self.player.queue.clear()
        self.player.current_song = None
        self.player.is_playing = False
        self.player.is_paused = False
        self.player.radio_mode = False
        vc.stop()

        await ctx.send("Stopped and cleared all Player flags.")

    @commands.command(name="restart", aliases=['r', 'rs'])
    async def rst(self, ctx):
        await ctx.reply("OK")

        if self.player:
            await self.player.cleanup()

        os.execv(sys.executable, [sys.executable] + sys.argv)

    @commands.command(name="debug")
    async def debug(self, ctx):
        vc = ctx.guild.voice_client
        embed = discord.Embed(color=colors.main)
        embed.set_author(name="Music Debug Panel")

        if vc:
            status = (
                "Playing" if vc.is_playing()
                else "Paused" if vc.is_paused()
                else "Idle"
            )

            vc_info = (
                f"Channel: `{vc.channel.name}`\n"
                f"Connected: `{vc.is_connected()}`\n"
                f"State: `{status}`\n"
                f"Bitrate: `{vc.channel.bitrate / 1000:.0f} kbps`\n"
                f"Members: `{len(vc.channel.members)}`"
            )
        else:
            vc_info = "Not Connected"

        embed.add_field(name="Voice Client", value=vc_info, inline=False)

        if self.player.current_song:
            song = self.player.current_song
            song_info = (
                f"Name: `{song.get('name', 'Unknown')}`\n"
                f"Category: `{song.get('category', 'Unknown')}`\n"
                f"Duration: `{song.get('length', 'Unknown')}`\n"
                f"Has Path: `{'path' in song}`"
            )
        else:
            song_info = "No current song"

        embed.add_field(name="Current Song", value=song_info, inline=False)

        queue_preview = list(self.player.queue)[:3]
        if queue_preview:
            preview_text = "\n".join(
                f"{i+1}. {s.get('name', 'Unknown')}"
                for i, s in enumerate(queue_preview)
            )
        else:
            preview_text = "Queue empty"

        embed.add_field(
            name="Queue",
            value=(
                f"Size: `{len(self.player.queue)}`\n"
                f"Preview:\n{preview_text}"
            ),
            inline=False,
        )

        embed.add_field(
            name="Player Flags",
            value=(
                f"Playing: `{self.player.is_playing}`\n"
                f"Paused: `{self.player.is_paused}`\n"
                f"Radio Mode: `{self.player.radio_mode}`"
            ),
            inline=False,
        )

        await ctx.reply(embed=embed)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            return

def setup(bot):
    bot.add_cog(AdminCommands(bot))