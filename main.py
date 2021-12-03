import os

import asyncio
import functools

import discord
from discord import embeds
from discord.ext import commands, tasks
import youtube_dl

import random

from async_timeout import timeout

# SENSITIVE
bot_token = ''
bot_id = ''

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

class YTDLError(Exception):
    pass

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('webpage_url')
        self.duration = self.parse_duration(int(data.get('duration')))
        self.uploader = data.get('uploader')
        self.uploader_url = data.get('uploader_url')
        self.thumbnail = data.get('thumbnail')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url']
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

    @classmethod
    async def create_source(cls, ctx: commands.Context, search: str, *, loop: asyncio.BaseEventLoop = None):
        loop = loop or asyncio.get_event_loop()

        partial = functools.partial(ytdl.extract_info, search, download=False, process=False)
        data = await loop.run_in_executor(None, partial)

        if data is None:
            raise YTDLError('Couldn\'t find anything that matches `{}`'.format(search))

        if 'entries' not in data:
            process_info = data
        else:
            process_info = None
            for entry in data['entries']:
                if entry:
                    process_info = entry
                    break

            if process_info is None:
                raise YTDLError('Couldn\'t find anything that matches `{}`'.format(search))

        webpage_url = process_info['webpage_url']
        partial = functools.partial(ytdl.extract_info, webpage_url, download=False)
        processed_info = await loop.run_in_executor(None, partial)

        if processed_info is None:
            raise YTDLError('Couldn\'t fetch `{}`'.format(webpage_url))

        if 'entries' not in processed_info:
            info = processed_info
        else:
            info = None
            while info is None:
                try:
                    info = processed_info['entries'].pop(0)
                except IndexError:
                    raise YTDLError('Couldn\'t retrieve any matches for `{}`'.format(webpage_url))

        return cls(discord.FFmpegPCMAudio(info['url'], **ffmpeg_options), data=info)
    
    @staticmethod
    def parse_duration(duration: int):
        minutes, seconds = divmod(duration, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)

        duration = []
        if days > 0:
            duration.append('{} days'.format(days))
        if hours > 0:
            duration.append('{} hours'.format(hours))
        if minutes > 0:
            duration.append('{} minutes'.format(minutes))
        if seconds > 0:
            duration.append('{} seconds'.format(seconds))

        return ', '.join(duration)

class admin(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    @commands.command(hidden=True, help='Shuts down the bot completely.')
    @commands.is_owner()
    async def shutdown(self, ctx):
        await ctx.message.add_reaction('💤')
        await client.close()

    @commands.command(hidden=True, help='Returns an invite link of the bot to a server.')
    @commands.is_owner()
    async def invite(self, ctx):
        embed = (discord.Embed( title='🎧 Invite Link', 
                                description='https://discordapp.com/oauth2/authorize?client_id={}&permissions=8&scope=bot'.format(bot_id), 
                                color=discord.Color.blurple()))
        await ctx.send(embed=embed)

    @commands.command(hidden=True, help='Gets all servers the bot is currently in.')
    @commands.is_owner()
    async def servers(self, ctx):
        servers = await client.fetch_guilds().flatten()
        await ctx.send(f'Servers: {[server.name for server in servers]}')

    def setup(client):
        client.add_cog(admin(client))

class general(commands.Cog):
    def __init__(self, client):
            self.client = client

    @commands.command(help='This command returns the current latency of the bot')
    async def ping(self, ctx):
        await ctx.send(f'**Pong:** {round(client.latency * 1000)} ms')

    @commands.command(help='This command says hi to the user')
    async def hello(self, ctx):
        await ctx.send(f'Moin {ctx.message.author.name}.')
    
    @commands.command(help='This command informs the user about the bot')
    async def about(self, ctx):
        servers = client.guilds

        embed = (discord.Embed(title='🎧  About me',
                               description='Hey, I\'m Kevin\'s music bot written in Python and hosted 24/7 on Heroku.',
                               color=discord.Color.blurple())
                               .add_field(name='Owner', value='Kevin#4854'.format(self))
                               .add_field(name='Servers', value=f'{len(servers)}'.format(self))
                               .add_field(name='GitHub', value=f'https://github.com/kvinsu/discord_musicbot'.format(self), inline=False))
        await ctx.send(embed=embed)

    def setup(client):
        client.add_cog(general(client))

repeating = {}
songs = {}
current_song = {}

class music(commands.Cog):
    def __init__(self, client):
        self.client = client

    #TODO: spotify support (if possible?), youtube playlists, limit max duration
    
    @commands.command(help='This command makes the bot join the voice channel')
    async def join(self, ctx):
        global songs, current_song, repeating

        if ctx.author.voice is None:
            await ctx.send('Ur not in a voice channel lmao.')
        else:
            voice_channel = ctx.author.voice.channel
            if ctx.voice_client is None:
                await voice_channel.connect()
            else:
                await ctx.voice_client.move_to(voice_channel)
            
            # init
            songs[ctx.guild.id] = []
            current_song[ctx.guild.id] = None
            repeating[ctx.guild.id] = False
    
    @commands.command(help='This command makes the bot leave the voice channel')
    async def leave(self, ctx):
        global songs, repeating, current_song
        
        voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
        if not await self.voice_check(ctx, voice):
            return
        else:
            await ctx.voice_client.disconnect()
            await ctx.message.add_reaction('👋')

            songs[ctx.guild.id] = []
            repeating[ctx.guild.id] = False
            current_song[ctx.guild.id] = None

    @commands.command(help='This command skips the current song')
    async def skip(self, ctx):
        voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
        if not await self.voice_check(ctx, voice):
            return
        elif not voice.is_playing():
            await ctx.send('Nothing to skip.')
            return
        else:
            ctx.voice_client.stop()
            if(repeating[ctx.guild.id]):
                await ctx.send('🎧 **Skipped. Still in repeat mode tho!**')
            else:
                await ctx.send('🎧 **Skipped.**')

    @commands.command(help='This command pauses the current song')
    async def pause(self, ctx):
        voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
        if not await self.voice_check(ctx, voice):
            return
        elif not voice.is_playing():
            await ctx.send('Nothing to pause.')
            return
        else:
            voice.pause()
            await ctx.message.add_reaction('⏸️')

    @commands.command(help='This command resumes the current song')
    async def resume(self, ctx):
        voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
        if not await self.voice_check(ctx, voice):
            return
        elif not voice.is_paused():
            await ctx.send('Nothing is paused.')
            return
        else:
            voice.resume()
            await ctx.message.add_reaction('▶️')

    @commands.command(help='This command sets the repeat mode of the player')
    async def repeat(self, ctx):
        global repeating

        voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
        if not await self.voice_check(ctx, voice):
            return
        elif not voice.is_playing() or current_song[ctx.guild.id] == None:
            await ctx.send('Nothing to repeat.')
            return
        else:
            repeating[ctx.guild.id] = not repeating[ctx.guild.id]
            if repeating[ctx.guild.id]:
                await ctx.send('🎧 **Repeat mode ON**')
            else:
                await ctx.send('🎧 **Repeat mode OFF**')

    @commands.command(help='This command shuffles the current queue')
    async def shuffle(self, ctx):
        global songs

        voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
        if not await self.voice_check(ctx, voice):
            return
        elif not songs[ctx.guild.id]:
            await ctx.send('Queue is empty, nothing to shuffle.')
            return
        else:
            random.shuffle(songs[ctx.guild.id])
            await ctx.send('🎧 **Queue shuffled.**')

    @commands.command(help='This command stops the current song and empties the queue')
    async def stop(self, ctx):
        global songs, current_song, repeating

        voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
        if not await self.voice_check(ctx, voice):
            return
        elif not voice.is_playing():
            await ctx.send('Nothing to stop.')
            return
        else:
            songs[ctx.guild.id] = []
            current_song[ctx.guild.id] = None
            repeating[ctx.guild.id] = False
            
            voice.stop()
            await ctx.send('🎧 **Stopped and queue cleared.**')

    @commands.command(help='This command clears the current queue')
    async def clear(self, ctx):
        global songs, current_song

        voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
        if not await self.voice_check(ctx, voice):
            return
        elif not songs[ctx.guild.id]:
            await ctx.send('Queue is empty, nothing to clear.')
            return
        else:
            songs[ctx.guild.id] = []
            await ctx.send('🎧 **Queue cleared.**')

    @commands.command(name='remove', help='This command removes a specific song from the current queue')
    async def _remove(self, ctx, index: int):
        global songs

        voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
        if not await self.voice_check(ctx, voice):
            return
        elif not songs[ctx.guild.id]:
            await ctx.send('Queue is empty, nothing to remove.')
            return
        else:
            if index > 0 and index <= len(songs[ctx.guild.id]):
                tmp = songs[ctx.guild.id][index - 1]
                del(songs[ctx.guild.id][index - 1])
                await ctx.send(f'🎧 **Removed:** {tmp.title}')
            else:
                await ctx.send('Invalid index. Check for it via ``!queue``.')

    @commands.command(help='This command displays the current queue')
    async def queue(self, ctx):
        voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
        
        if not await self.voice_check(ctx, voice):
            return
        elif not songs[ctx.guild.id]:
            await ctx.send('Queue is empty.')
            return
        else:
            titles = [song.title for song in songs[ctx.guild.id]]
            enum_titles = []

            for idx, val in enumerate(titles, start=1):
                enum_titles.append(f'**{idx}.** {val}')

            embed = (discord.Embed(title='🎧  Current Queue',
                                description='\n'.join(enum_titles).format(self),
                                color=discord.Color.blurple()))
            await ctx.send(embed=embed)

    @commands.command(help='This command plays songs or adds them to the current queue')
    async def play(self, ctx, *, url):
        global songs, current_song, repeating

        voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
        if ctx.author.voice is None:
            await ctx.send("Ur not in a voice channel lmao.")
            return
        elif voice and ctx.voice_client.channel != ctx.author.voice.channel:
            await ctx.send('Ur not in that voice channel. 🌚')
            return

        if not voice:
            await ctx.invoke(self.client.get_command('join'))

        voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
        if voice:
            if url != '':
                song = await YTDLSource.create_source(ctx, url, loop=self.client.loop)
                try:
                    songs[ctx.guild.id].append(song)
                except:
                    songs[ctx.guild.id] = [song]
            else:
                await ctx.send('Nothing to play!')
                return

            if not voice.is_playing():
                try:
                    if not repeating[ctx.guild.id]:
                        current_song[ctx.guild.id] = songs[ctx.guild.id].pop(0)
                        ctx.voice_client.play(current_song[ctx.guild.id], after=lambda e: print('Player error: %s' % e) if e else asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.client.loop))
                        await ctx.send(embed=self.create_play_embed(ctx=ctx))
                    else:
                        current_song[ctx.guild.id] = await YTDLSource.create_source(ctx, current_song[ctx.guild.id].title, loop=self.client.loop)
                        ctx.voice_client.play(current_song[ctx.guild.id], after=lambda e: print('Player error: %s' % e) if e else asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.client.loop))
                except YTDLError as e:
                    await ctx.send('An error occurred while processing this request: {}'.format(str(e)))
            else:
                await ctx.send(f'🎧 **Enqueued:** {song.title}')

    async def play_next(self, ctx):
        global songs, current_song, repeating

        if songs[ctx.guild.id] or repeating[ctx.guild.id]:
            try:
                if not repeating[ctx.guild.id]:
                    current_song[ctx.guild.id] = songs[ctx.guild.id].pop(0)
                    ctx.voice_client.play(current_song[ctx.guild.id], after=lambda e: print('Player error: %s' % e) if e else asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.client.loop))
                    await ctx.send(embed=self.create_play_embed(ctx=ctx)) 
                else:
                    current_song[ctx.guild.id] = await YTDLSource.create_source(ctx, current_song[ctx.guild.id].title, loop=self.client.loop)
                    ctx.voice_client.play(current_song[ctx.guild.id], after=lambda e: print('Player error: %s' % e) if e else asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.client.loop))
            except YTDLError as e:
                await ctx.send('An error occurred while processing this request: {}'.format(str(e)))
        else:
            await asyncio.sleep(210)
            voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
            if not voice.is_playing():
                await ctx.voice_client.disconnect()

                songs[ctx.guild.id] = []
                repeating[ctx.guild.id] = False
                current_song[ctx.guild.id] = None

    def create_play_embed(self, ctx):
        embed = (discord.Embed(title='🎧  Now playing',
                               description=f'{current_song[ctx.guild.id].title}'.format(self),
                               color=discord.Color.blurple())
                 .add_field(name='Duration', value=current_song[ctx.guild.id].duration)
                 .add_field(name='Channel', value=f'[{current_song[ctx.guild.id].uploader}]({current_song[ctx.guild.id].uploader_url})'.format(self))
                 .add_field(name='URL', value=f'[YouTube]({current_song[ctx.guild.id].url})'.format(self))
                 .set_thumbnail(url=current_song[ctx.guild.id].thumbnail))
        return embed

    # check voice_states of member and bot
    async def voice_check(self, ctx, voice):
        if not voice:
            await ctx.send('Huh? I\'m not in a voice channel right now.')
            return False
        elif ctx.author.voice is None:
            await ctx.send("Ur not in a voice channel lmao.")
            return False
        elif ctx.voice_client.channel != ctx.author.voice.channel:
            await ctx.send('Ur not in that voice channel. 🌚')
            return False
        else:
            return True

    def setup(client):
        client.add_cog(music(client))

class EmbedHelpCommand(commands.MinimalHelpCommand):
    async def send_pages(self):
        destination = self.get_destination()
        e = discord.Embed(title='🎧  Commands', color=discord.Color.blurple(), description='')
        for page in self.paginator.pages:
            e.description += page
        await destination.send(embed=e)

cogs = [admin, general, music]

client = commands.Bot(command_prefix='!')
# customize !help command
client.help_command = EmbedHelpCommand(no_category='misc')

# load cogs
for i in range(len(cogs)):
    cogs[i].setup(client)

@client.event
async def change_status():
    await client.change_presence(activity=discord.Game(name="Fortnite"))

# send error messages
@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CommandNotFound):
        await ctx.send("Huh? There is no such command (yet). Check commands via ``!help``.")
    else:
        await ctx.send(f"Error: {str(error)}")

# auto-disconnect when alone in channel
@client.event
async def on_voice_state_update(member, before, after):
    global songs, current_song, repeating

    voice_state = member.guild.voice_client
    if voice_state is None:
        return 

    if len(voice_state.channel.members) == 1:
        songs[member.guild.id] = []
        current_song[member.guild.id] = None
        repeating[member.guild.id] = False

        await voice_state.disconnect()

@client.event
async def on_guild_join(guild):
    general = discord.utils.find(lambda x: x.name == 'general',  guild.text_channels)
    allgemein = discord.utils.find(lambda x: x.name == 'allgemein',  guild.text_channels)

    if general and general.permissions_for(guild.me).send_messages:
        await general.send('🎧 **Hello {}!** My prefix is \'!\', use ``!help`` for more info :)'.format(guild.name))
    elif allgemein and allgemein.permissions_for(guild.me).send_messages:
        await allgemein.send('🎧 **Hello {}!** My prefix is \'!\', use ``!help`` for more info :)'.format(guild.name))
    
    print(f'Joined the server {guild.name}.')


# startup behavior
@client.event
async def on_ready():
    await change_status()
    print('MusicBox is online.')


client.run(bot_token)