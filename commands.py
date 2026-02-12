import discord
from discord.ext import commands

import time
import platform
import re

from main import colors

class MusicCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()

    @property
    def player(self):
        return getattr(self.bot, "player", None)

    @commands.command(name="join")
    async def join(self, ctx):
        if not ctx.author.voice or not ctx.author.voice.channel:
            return await ctx.reply("You need to be in a vc.")

        channel = ctx.author.voice.channel
        vc = ctx.guild.voice_client

        if vc:
            if vc.channel.id == channel.id:
                return await ctx.reply("I'm already here bruh")
            await vc.move_to(channel)
        else:
            await channel.connect()

        await ctx.send(f"Joined <#{channel.id}>")

    @commands.command(name="play")
    async def play(self, ctx, *, query: str = None):
        if not query:
            return await ctx.reply(f"Usage: `{ctx.prefix}play <song or link>`")

        if not ctx.guild.voice_client:
            if not ctx.author.voice:
                return await ctx.reply("You need to be in a vc.")
            await ctx.author.voice.channel.connect()

        async with ctx.typing():
            song_data = None

            match = re.search(r"/songs/(\d+)", query)
            if match:
                song_id = match.group(1)
                song_data = await self.player.get_song_by_id(song_id)
            else:
                song_data = await self.player.search_song(query)

        if not song_data:
            return await ctx.reply(f"No results found for **{query}**.")

        if song_data.get("category", "").lower() not in ("released", "unreleased"):
            return await ctx.reply("Song must be Released or Unreleased. You can use the JSON url (ex. `https://juicewrldapi.com/juicewrld/songs/25/`)")

        self.player.radio_mode = None
        self.player.add_to_queue(song_data)

        embed = discord.Embed(
            title=song_data.get("name", "Unknown"),
            description=f"Prod. {song_data.get('producers', 'Unknown')}",
            color=colors.main,
        )
        embed.set_author(name="+ Song Added")
        embed.add_field(name="Length", value=song_data.get("length", "N/A"), inline=True)
        embed.add_field(
            name="Category",
            value=song_data.get("category", "N/A").title(),
            inline=True,
        )

        if self.player.is_playing:
            embed.add_field(
                name="Position",
                value=f"#{len(self.player.queue)}",
                inline=True,
            )

        image_url = song_data.get("image_url")
        if image_url:
            embed.set_thumbnail(url=f"https://juicewrldapi.com{image_url}")

        await ctx.reply(embed=embed)

        if not self.player.is_playing:
            await self.player.play_next(ctx)

    @commands.command(name="pause")
    async def pause(self, ctx):
        vc = ctx.guild.voice_client
        if not vc or not vc.is_playing():
            return await ctx.reply("Nothing is playing.")

        vc.pause()
        self.player.is_paused = True
        await ctx.send("Paused <:juiceL:1407602749851435059>")

    @commands.command(name="resume", aliases=['unpause'])
    async def resume(self, ctx):
        vc = ctx.guild.voice_client
        if not vc or not vc.is_paused():
            return await ctx.reply("Nothing is paused.")

        vc.resume()
        self.player.is_paused = False
        await ctx.send("Resumed <:love:1413032472731582505>")

    @commands.command(name="skip", aliases=["s"])
    async def skip(self, ctx):
        vc = ctx.guild.voice_client
        if not vc or not vc.is_playing():
            return await ctx.reply("Nothing is playing.")

        vc.stop()
        await ctx.send("Skipped <:love:1413032472731582505>")

    @commands.command(name="queue", aliases=["q"])
    async def show_queue(self, ctx):
        if not self.player.current_song and not self.player.queue:
            return await ctx.reply("Queue is empty.")

        embed = discord.Embed(title="Current Playlist", color=colors.main)

        if self.player.current_song:
            song = self.player.current_song

            era = song.get("era", {})
            era_name = era.get("name", "Unknown") if isinstance(era, dict) else "Unknown"
            text = f"**{song.get('name', 'Unknown')}**\n{era_name}"

            if song.get("length"):
                text += f" • {song['length']}"

            embed.add_field(name="Now Playing", value=text, inline=False)

        if self.player.queue:
            lines = []

            for i, song in enumerate(list(self.player.queue)[:10], start=1):
                era = song.get("era", {})
                era_name = era.get("name", "Unknown") if isinstance(era, dict) else "Unknown"

                line = (
                    f"`{i}.` **{song.get('name', 'Unknown')}** - "
                    f"{era_name} - "
                    f"{song.get('category', 'Unknown').title()}"
                )

                if song.get("length"):
                    line += f" • {song['length']}"

                lines.append(line)

            if len(self.player.queue) > 10:
                lines.append(f"*...and {len(self.player.queue) - 10} more*")

            embed.add_field(name="Queue", value="\n".join(lines), inline=False)

        embed.set_footer(text=f"{len(self.player.queue)} songs in queue")
        await ctx.reply(embed=embed)

    @commands.command(name="nowplaying", aliases=["np"])
    async def now_playing(self, ctx):
        song = self.player.current_song
        if not song:
            return await ctx.reply("Nothing is playing.")

        embed = discord.Embed(
            title=song.get("name", "N/A"),
            description=(
                f"Prod. {song.get('producers', 'Unknown')}\n"
                f"Eng. {song.get('engineers', 'Unknown')}"
            ),
            color=colors.main,
        )

        details = []
        if song.get("credited_artists"): details.append(f"Artist(s): {song['credited_artists']}")
        if song.get("length"): details.append(f"Duration: {song['length']}")
        if song.get("category"): details.append(f"Type: {song['category'].title()}")

        era = song.get("era")
        if isinstance(era, dict) and era.get("name"):
            details.append(f"Era: {era['name']}")

        if details:
            embed.add_field(name="Details", value="\n".join(details), inline=False)

        embed.set_author(name="Now Playing in VC")

        image_url = song.get("image_url")
        if image_url:
            embed.set_thumbnail(url=f"https://juicewrldapi.com{image_url}")

        await ctx.reply(embed=embed)

    @commands.command(name="radio")
    async def radio(self, ctx):
        if not ctx.guild.voice_client:
            if not ctx.author.voice:
                return await ctx.reply("You need to be in a vc.")
            await ctx.author.voice.channel.connect()

        self.player.radio_mode = True

        if self.player.is_playing:
            msg = "Radio enabled. It will start after the current song."
        else:
            msg = "Radio enabled. Starting now..."
            await self.player.play_next(ctx)

        await ctx.send(msg)

    @commands.command(name="stopradio")
    async def stop_radio(self, ctx):
        self.player.radio_mode = None
        await ctx.send("Radio disabled.")

    @commands.command(name="about")
    async def about(self, ctx):
        uptime = self._format_uptime(int(time.time() - self.start_time))
        embed=discord.Embed(title='WRLD 2', description=f'WRLD 2 is an extension of WRLD by purree, to provide Juice WRLD media in Voice Channels. It is exclusive to the JUICEWRLDAPI server, however is open source so it could be self built and hosted. Created in Python v{platform.python_version()} and made possible by juicewrldapi.com', color=colors.main)
        embed.add_field(name='📊 Stats', value=
                        f'`{uptime}` uptime\n'
                        f'`{len(self.bot.users)}` users\n'
                        f'`{len(self.bot.commands)}` commands\n'
                        f'`{platform.system()} {platform.release()}` OS'
                        )
        embed.add_field(name='<:github:1413031789961805875> GitHub', value='[Click Here](https://github.com/purrre/WRLD-ext-media-player/)')
        embed.set_footer(text='Made with 💖 by @purree')
        await ctx.reply(embed=embed)

    @commands.command(name="ping")
    async def ping(self, ctx):
        api_latency = round(self.bot.latency * 1000)

        start = time.time()
        msg = await ctx.reply("Pinging...")
        response_ms = round((time.time() - start) * 1000)

        embed = discord.Embed(color=colors.main)
        embed.set_author(name="Pong!")
        embed.add_field(name="API Latency", value=f"{api_latency}ms", inline=True)
        embed.add_field(name="Response", value=f"{response_ms}ms", inline=True)

        await msg.edit(content=None, embed=embed)

    def _format_uptime(self, seconds):
        days, rem = divmod(seconds, 86400)
        hours, rem = divmod(rem, 3600)
        minutes, secs = divmod(rem, 60)

        parts = []
        if days:
            parts.append(f"{days}d")
        if hours:
            parts.append(f"{hours}h")
        if minutes:
            parts.append(f"{minutes}m")
        parts.append(f"{secs}s")

        return " ".join(parts)

def setup(bot):
    bot.add_cog(MusicCommands(bot))