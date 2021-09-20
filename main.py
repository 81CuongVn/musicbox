import asyncio

import discord
from discord.ext import commands, tasks
import youtube_dl

youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'  # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url']
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

class admin(commands.Cog):
    def __init__(self, client):
        self.client = client
        self._last_result = None
        self.sessions = set()
    
    @commands.command(hidden=True)
    @commands.is_owner()
    async def shutdown(self, ctx):
        await ctx.send('💤')
        await client.close()

    @commands.command(hidden=True)
    async def load(self, ctx, *, module):
        """Loads a module."""
        try:
            self.client.load_extension(module)
        except commands.ExtensionError as e:
            await ctx.send(f'{e.__class__.__name__}: {e}')
        else:
            await ctx.send('\N{OK HAND SIGN}')

    @commands.command(hidden=True)
    async def unload(self, ctx, *, module):
        """Unloads a module."""
        try:
            self.client.unload_extension(module)
        except commands.ExtensionError as e:
            await ctx.send(f'{e.__class__.__name__}: {e}')
        else:
            await ctx.send('\N{OK HAND SIGN}')

    @commands.group(name='reload', hidden=True, invoke_without_command=True)
    async def _reload(self, ctx, *, module):
        """Reloads a module."""
        try:
            self.client.reload_extension(module)
        except commands.ExtensionError as e:
            await ctx.send(f'{e.__class__.__name__}: {e}')
        else:
            await ctx.send('\N{OK HAND SIGN}')

    def setup(client):
        client.add_cog(admin(client))

class general(commands.Cog):
    def __init__(self, client):
            self.client = client

    @commands.command(help='This command returns the current latency of the bot')
    async def ping(self, ctx):
        await ctx.send(f'**Pong:** {round(client.latency * 1000)} ms')

    @commands.command(help='This command says hi to the user')
    async def hello(ctx):
        await ctx.send('Moin')

    def setup(client):
        client.add_cog(general(client))

songs = []
joined = 0

class music(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command(help='This command makes the bot join the voice channel')
    async def join(self, ctx):
        if ctx.author.voice is None:
            await ctx.send("Ur not in a voice channel.")
        else:
            voice_channel = ctx.author.voice.channel
            if ctx.voice_client is None:
                await voice_channel.connect()
            else:
                await ctx.voice_client.move_to(voice_channel)
    
    @commands.command(help='This command makes the bot leave the voice channel')
    async def leave(self, ctx):
        global songs, joined
        
        await ctx.voice_client.disconnect()

        songs = []
        joined = 0

    '''
    @commands.command()
    async def play(self, ctx, url):
        global songs

        songs.append(url)

        ffmpeg_options = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
        ydl_options = {'format': "bestaudio"}
        vc = ctx.voice_client

        with youtube_dl.YoutubeDL(ydl_options) as ydl:
            info = ydl.extract_info(url, download=False)
            url2 = info['formats'][0]['url']
            source = await discord.FFmpegOpusAudio.from_probe(url2, **ffmpeg_options)
            vc.play(source)
    '''

    @commands.command(hidden=True)
    async def real_play(self, ctx):
        global songs

        if songs:
            async with ctx.typing():
                player = await YTDLSource.from_url(songs[0], loop=client.loop)
                ctx.voice_client.play(player, after=lambda e: print('Player error: %s' % e) if e else None)

            await ctx.send('**Now playing:** {}'.format(player.title)) 
            del (songs[0])
        else:
            await ctx.send('Nothing to play.')                 

    @commands.command(help='This command plays songs or adds them to the current queue')
    async def play(self, ctx, url):
        global songs, joined

        if ctx.voice_channel != ctx.author.voice_channel:
            await ctx.invoke(self.client.get_command('join'))

        if ctx.voice_channel:
            songs.append(url)

            if joined == 0 or not ctx.voice_client.is_playing:
                await ctx.invoke(self.client.get_command('real_play'))
                joined = 1
            else:
                await ctx.send(f'`{url}` added to queue!')

    
    @commands.command(help='This command skips the current song')
    async def skip(self, ctx):
        global songs

        if not ctx.voice_client.is_playing:
            await ctx.voice_client.send('Nothing to skip.')
            return
        else if ctx.voice_channel != ctx.author.voice_channel:
            await ctx.voice_client.send('Ur not in that voice channel. 🌚')
            return
        
        ctx.voice_client.stop()
        await ctx.send('Skipped.')
        if songs:
            await ctx.invoke(self.client.get_command('real_play'))

    @commands.command(help='This command pauses the song')
    async def pause(self, ctx):
        if ctx.voice_channel != ctx.author.voice_channel:
            await ctx.voice_client.send('Ur not in that voice channel. 🌚')
            return

        voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
        if voice.is_playing():
            voice.pause()
            await ctx.send('⏸️')
        else:
            await ctx.send('Nothing to pause.')

    @commands.command(help='This command resumes the song')
    async def resume(self, ctx):
        if ctx.voice_channel != ctx.author.voice_channel:
            await ctx.voice_client.send('Ur not in that voice channel. 🌚')
            return

        voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
        if voice.is_paused():
            voice.resume()
            await ctx.send('▶️')
        else:
            await ctx.send('Nothing is paused.')

    @commands.command(help='This command stops the current song and empties the queue')
    async def stop(self,ctx):
        global songs

        if ctx.voice_channel != ctx.author.voice_channel:
            await ctx.voice_client.send('Ur not in that voice channel. 🌚')
            return

        server = ctx.message.guild
        voice_channel = server.voice_client

        if voice.is_playing():
            voice.stop()
            await ctx.send('⏹️')
            songs = []
        else:
            await ctx.send('Nothing to stop.')

    def setup(client):
        client.add_cog(music(client))

cogs = [admin, general, music]

client = commands.Bot(command_prefix='!')

for i in range(len(cogs)):
    cogs[i].setup(client)

@client.event
async def change_status():
    await client.change_presence(activity=discord.Game(name="Fortnite"))

@client.event
async def on_ready():
    await change_status()
    print('Bot is online.')

client.run("")