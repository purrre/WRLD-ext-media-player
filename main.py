import discord
from discord.ext import commands
from discord.gateway import DiscordWebSocket

import asyncio
import aiohttp
from collections import deque
from typing import Optional
from urllib.parse import quote
import os
import sys
from dotenv import load_dotenv
import random

from mobile import WRLD2

load_dotenv()

class colors:
    main = 0x6A0DAD

ffmpeg_path = None
try:
    from local_ffmpeg import install, is_installed

    ffmpeg_dir = os.path.join(os.path.dirname(__file__), "ffmpeg")

    if not is_installed(path=ffmpeg_dir):
        print("Installing FFmpeg...")
        success, message = install(path=ffmpeg_dir)
        print(message if success else f"FFmpeg install failed: {message}")

    if sys.platform == "win32":
        ffmpeg_path = os.path.join(ffmpeg_dir, "ffmpeg.exe")
    else:
        ffmpeg_path = os.path.join(ffmpeg_dir, "ffmpeg")

    if not os.path.exists(ffmpeg_path):
        ffmpeg_path = None

except Exception as e:
    print(f"FFmpeg setup error: {e}")
    print("Using system FFmpeg")


intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.guilds = True

DiscordWebSocket.identify = WRLD2
bot = commands.Bot(
    command_prefix=commands.when_mentioned_or('..'),
    intents=intents,
    help_command=None,
    case_insensitive=True
)

class LyricsButton(discord.ui.View):
    def __init__(self, lyrics: str):
        super().__init__(timeout=None)
        self.lyrics = lyrics

    @discord.ui.button(label="Lyrics", style=discord.ButtonStyle.gray)
    async def callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        lines = self.lyrics.splitlines(keepends=True)

        chunks = []
        current = ""

        for line in lines:
            if len(current) + len(line) > 4096:
                chunks.append(current)
                current = line
            else:
                current += line

        if current:
            chunks.append(current)

        embed = discord.Embed(description=chunks[0], color=colors.main)
        await interaction.response.send_message(embed=embed, ephemeral=True)

        for chunk in chunks[1:]:
            await interaction.followup.send(
                embed=discord.Embed(description=chunk, color=colors.main),
                ephemeral=True
            )

class MusicPlayer:
    def __init__(self):
        self.queue = deque()
        self.current_song = None
        self.is_playing = False
        self.is_paused = False
        self.radio_mode = None
        self.voice_client: discord.VoiceClient = None
        self.session: aiohttp.ClientSession = None

    async def get_channel(self):
        channel_id = os.getenv('CHANNEL')
        if channel_id:
            return bot.get_channel(int(channel_id))
        return None

    async def get_session(self):
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def get_song_by_id(self, song_id: str):
        session = await self.get_session()
        url = f"https://juicewrldapi.com/juicewrld/songs/{song_id}/"

        try:
            async with session.get(url) as resp:
                if resp.status == 200:
                    return await resp.json()
        except Exception as e:
            print(f"Get song by ID error: {e}")

        return None

    async def search_song(self, query: str):
        session = await self.get_session()
        url = f"https://juicewrldapi.com/juicewrld/songs/?search={quote(query)}"

        try:
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data["results"][0] if data.get("results") else None
        except Exception as e:
            print(f"Search error: {e}")
        return None

    def add_to_queue(self, song: dict):
        self.queue.append(song)

    async def get_radio_song(self):
        session = await self.get_session()
        try:
            async with session.get("https://juicewrldapi.com/juicewrld/songs/") as resp:
                if resp.status != 200:
                    print("Failed to fetch song list")
                    return None

                data = await resp.json()
                count = data.get("count")

                if not isinstance(count, int):
                    print("Invalid count")
                    return None

            for _ in range(15):
                randomi = random.randint(1, count)

                async with session.get(f"https://juicewrldapi.com/juicewrld/songs/{randomi}/") as song_resp:
                    if song_resp.status != 200:
                        continue

                    song_data = await song_resp.json()

                    if not isinstance(song_data, dict):
                        continue
                    if "path" not in song_data:
                        continue

                    category = song_data.get("category", "").lower()
                    if category in ["released", "unreleased"]:
                        return song_data

            print("No valid radio song found")
            return None

        except Exception as e:
            print(f"Song fetch error: {e}")
            return None

    async def play_next(self, ctx: commands.Context):
        if self.queue:
            self.radio_mode = None 

        if not self.queue:
            if self.radio_mode:
                radio_song = await self.get_radio_song()
                if radio_song:
                    self.add_to_queue(radio_song)
                else:
                    channel = await self.get_channel()
                    if channel:
                        await channel.send("Failed to fetch radio song. Radio stopping.")
                    self.radio_mode = None
            
            if not self.queue:
                self.is_playing = False
                self.current_song = None
                channel = await self.get_channel()
                if channel:
                    await channel.send("<:sadjoe:1469924039811399793> Queue finished.")
                return

        self.current_song = self.queue.popleft()
        self.is_playing = True
        self.is_paused = False

        path = self.current_song.get("path")
        if not path:
            print(f"No path for song: {self.current_song.get('name', 'Unknown')}")
            await self.play_next(ctx)
            return

        vc = ctx.guild.voice_client
        if not vc or not vc.is_connected():
            self.is_playing = False
            self.current_song = None
            return

        url = f"https://juicewrldapi.com/juicewrld/files/download/?path={quote(path)}"

        # shoutout google for this config :sob:
        ffmpeg_opts = {
            "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            "options": "-vn",
        }

        try:
            source = discord.FFmpegPCMAudio(
                url,
                executable=ffmpeg_path,
                **ffmpeg_opts
            )
        except Exception as e:
            print(f"FFmpeg error for {self.current_song.get('name', 'Unknown')}: {e}")
            await self.play_next(ctx)
            return

        def after_playing(error):
            if error:
                print(f"Playback error: {error}")
            
            bot.loop.create_task(self.play_next(ctx))

        self.voice_client = vc
        vc.play(source, after=after_playing)

        channel = await self.get_channel()
        if channel:
            message_cont = (
                f"🎵 Now Playing: **{self.current_song.get('name', 'Unknown')}** "
                f"(Prod. {self.current_song.get('producers', 'Unknown')}) - "
                f"{self.current_song.get('category', 'Unknown').title()}"
                f"\nDuration: {self.current_song.get('length', 'Unknown')}"
            )
            
            view = None
            if self.current_song.get('lyrics'):
                view = LyricsButton(self.current_song['lyrics'])
            
            await channel.send(message_cont, view=view)

    async def cleanup(self):
        if self.session and not self.session.closed:
            await self.session.close()

player = MusicPlayer()
bot.player = player

@bot.command(name="help")
async def help(ctx):
    hlist = (
        "play <song> - plays the specified song, accepts name OR direct url (ex. https://juicewrldapi.com/juicewrld/songs/25/)\n"
        "join - joins your voice channel\n"
        "pause - pauses the current song\n"
        "resume - resumes playback\n"
        "skip - skips current song\n"
        "queue / q - shows the queue\n"
        "nowplaying / np - shows the current song playing\n"
        "radio - enables randomly playing songs\n"
        "stopradio - disables radio\n"
        "ping - bot connection info\n"
        "about - bot information"
    )

    await ctx.reply(f"Prefix: `{ctx.prefix}` ```{hlist}```")

@bot.event
async def on_ready():
    print("Bot is ready 🎶\nMade by pure, powered by juicewrldapi")
    print(f"Logged in as {bot.user}")

async def main():
    for ext in ['commands', 'admin']:
        try:
            bot.load_extension(ext)
            print(f"Loaded file: {ext}")
        except Exception as e:
            print(f"Failed to load file {ext}: {e}")

    token = os.getenv("TOKEN")
    if not token:
        print("TOKEN not set in .env")
        return

    async with bot:
        try:
            await bot.start(token)
        finally:
            await player.cleanup()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass