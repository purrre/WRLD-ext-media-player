# WRLD-ext-media-player (WRLD 2)

WRLD 2 is a simple Discord bot that allows users to play media from JuiceWRLDAPI directly in Discord voice channels.

It was created as an extension of [WRLD](https://github.com/purrre/WRLD-bot) for use in the JUICEWRLDAPI Discord server. To avoid maintenance, resources, and potential Discord issues, it was created as its own standalone bot. The project is open source, so anyone can self-host and use it in their own server. Note that streaming this content to Discord is against their ToS.

Its definitely not the prettiest or most efficient code and you're welcome to edit and PR, however this was created as a fun project for me, for people to use in JUICEWRLDAPI. I do not plan to do much going forward with it..

If you'd like to use the public instance instead of hosting it yourself, its available in the JUICEWRLDAPI Discord server:  
https://discord.gg/jwa


## Running

1. Clone or download the repository.

2. WRLD 2 uses `local-ffmpeg` by default.  
   If you already have FFmpeg installed globally and want to use that instead, remove `local-ffmpeg` from `requirements.txt` and slightly edit the code.

3. Install the required packages. Its recommended to use a virtual environment unless youre hosting:

   ```bash
   python -m venv venv
   source venv/bin/activate  # windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. Create a file named `.env` in the project root and add:

   ```bash
   TOKEN=
   CHANNEL=
   ADMIN_ROLE=
   ```

   - `TOKEN` - Your Discord bot token  
   - `CHANNEL` - Channel ID where "Now Playing" messages will be sent  
   - `ADMIN_ROLE` - Role ID allowed to use admin commands (in `admin.py`)

5. Start the bot:

   ```bash
   python main.py
   ```

You may want to adjust the code slightyl to remove my branding and custom emojis, however you should now have your own instance running!

If you need help, contact me on Discord: @purree