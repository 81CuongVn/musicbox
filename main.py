import os

import asyncio
import functools

import discord
from discord import embeds
from discord import user
from discord.ext import commands, tasks
from dotenv import load_dotenv

# fork of ytdl, more patched and maintained
import yt_dlp

import random
from async_timeout import timeout
import threading
import concurrent.futures
import time

import requests
import json


# get bot credentials
load_dotenv()
bot_token = os.getenv("BOT_TOKEN")
tenor_token = os.getenv("TENOR_TOKEN")
bot_id = os.getenv("BOT_ID")

# ignore unnecessary bug reports
yt_dlp.utils.bug_reports_message = lambda: ''

class YTDLError(Exception):
    pass


class YTDLSource(discord.PCMVolumeTransformer):
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
        # bind to ipv4 since ipv6 addresses cause issues sometimes
        'source_address': '0.0.0.0'
    }

    # prevent termination of FFMPEG executable due to corrupt packages
    ffmpeg_options = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 
        'options': '-vn'
    }

    ytdl = yt_dlp.YoutubeDL(ytdl_format_options)
    
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data
        self.requester = data.get('requester')
        self.channel = data.get('channel')

        self.title = data.get('title')
        self.url = data.get('webpage_url')
        self.duration = data.get('duration')
        self.uploader = data.get('uploader')
        self.uploader_url = data.get('uploader_url')
        self.thumbnail = data.get('thumbnail')

    @classmethod
    async def create_source(cls, ctx: commands.Context, search: str, *, loop: asyncio.BaseEventLoop = None):
        loop = loop or asyncio.get_event_loop()

        # prevents this method from opening to many stale threads (especially when playing playlists)
        executor = concurrent.futures.ThreadPoolExecutor(3)

        # first extraction: determine song type
        partial = functools.partial(cls.ytdl.extract_info, search, download=False, process=False)
        data = await loop.run_in_executor(executor, partial)

        if data is None:
            raise YTDLError('Couldn\'t find anything that matches `{}`'.format(search))

        playlist_detected = False
        if 'entries' not in data:
            # search song via keyword or url
            process_info = [data]
        else:
            # search song via yt playlist
            playlist_detected = True
            await ctx.send('🎧 **Processing playlist.** This may take a while...')
            process_info = [entry for entry in data['entries']]

            if not process_info:
                raise YTDLError('Couldn\'t find anything that matches `{}`'.format(search))

        sources = []
        for entry in process_info:
            # differentiation necessary, as yt playlists have different dict_keys
            if playlist_detected == False:
                webpage_url = entry['webpage_url']
            else:
                webpage_url = entry['url']

            # second extraction: actual audio processing + retrieval of other keys (thumbnail, duration etc.)
            partial = functools.partial(cls.ytdl.extract_info, webpage_url, download=False)
            data = await loop.run_in_executor(executor, partial)
            # TODO: case playlist: throws Errno 11: Resource temporarily not available after ~29th song
            # print(f'{threading.active_count()} Threads active.')

            if data is None:
                raise YTDLError('Couldn\'t fetch `{}`'.format(webpage_url))

            if 'entries' not in data:
                info = data
            else:
                info = None
                while info is None:
                    try:
                        info = data['entries'].pop(0)
                    except IndexError:
                        raise YTDLError('Couldn\'t retrieve any matches for `{}`'.format(webpage_url))

            # add user + channel info to dict
            info['requester'] = ctx.author
            info['channel'] = ctx.channel
            sources.append(cls(discord.FFmpegPCMAudio(info['url'], **cls.ffmpeg_options), data=info))

        return sources


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
    # improve random generator
    sys_random = random.SystemRandom()

    def __init__(self, client):
            self.client = client

    @commands.command(help='This command returns the current latency of the bot.')
    async def ping(self, ctx):
        await ctx.send(f'**Pong:** {round(client.latency * 1000)} ms')

    @commands.command(help='This command says hi to the user', aliases=['hi', 'hey'])
    async def hello(self, ctx):
        hellos = [
            'Hewo °‿‿°', 'Moin', 'Heyy ( ˘ ³˘)♥'
        ]

        hello = self.sys_random.choice(hellos)
        await ctx.send(f'{hello} {ctx.message.author.mention}')
    
    @commands.command(help='This command informs the user about the bot.', aliases=['info', 'stats'])
    async def about(self, ctx):
        servers = self.client.guilds

        embed = (discord.Embed(title='🎧  About me',
                               description='Hey, I\'m Kevin\'s music bot, hosted 24/7 on Heroku.',
                               color=discord.Color.blurple())
                               .add_field(name='Owner', value='Kevin#4854'.format(self))
                               .add_field(name='Servers', value=f'{len(servers)}'.format(self))
                               .add_field(name='Library', value="discord.py")
                               .add_field(name='GitHub', value=f'https://github.com/kvinsu/discord_musicbot'.format(self), inline=False))
        await ctx.send(embed=embed)

    @commands.command(help='This command answers your question with yes or no.')
    async def decide(self, ctx, *, question: commands.clean_content):
        responses = [
            'Yes ʘ‿ʘ', 'No ಠ_ಠ', 'Sure (｡◕‿◕｡)', 'Without a doubt, yes ♥‿♥', 'Yeh, oke ( ˇ෴ˇ )',
            'no... (╯°□°）╯︵ ┻━┻', 'no... baka 눈_눈',
            "senpai, pls no ;-;", 'Nah ⊙﹏⊙', 'Yas!!'
        ]

        answer = self.sys_random.choice(responses)
        await ctx.send(f'**{answer}**')

    @commands.command(help='This command hugs you or a named person <3')
    async def hug(self, ctx, username=None):
        hugs = [
            'https://c.tenor.com/OXCV_qL-V60AAAAC/mochi-peachcat-mochi.gif',
            'https://c.tenor.com/LadCBLn5HDQAAAAC/poke-hug.gif',
            'https://c.tenor.com/8nEtM-3oQ1sAAAAC/hug-cats.gif',
            'https://c.tenor.com/W-R9sPkk_IMAAAAC/come-here-hugs.gif',
            'https://c.tenor.com/GTlDCm4P4EsAAAAd/kitty-kitten.gif',
            'https://c.tenor.com/eAKshP8ZYWAAAAAC/cat-love.gif'
        ]

        embed = discord.Embed(
            color=discord.Color.blurple()
        ).set_image(url=self.sys_random.choice(hugs))

        async with ctx.channel.typing():
            if username != None:
                mentions_matches = ['<@!','>']
                if all(x in username for x in mentions_matches):
                    embed.description = f'{ctx.author.mention} hugs {username}!'
                else:
                    member = ctx.guild.get_member_named(username)
                    if member != None:
                        embed.description = f'{ctx.author.mention} hugs {member.mention}!'
            
        await ctx.send(embed=embed)

    @commands.command(help='This command performs a random coinflip for you (german).', aliases=["flip", "coin"])
    async def coinflip(self, ctx):
        coinsides = ['Kopf', 'Zahl']
        await ctx.send(f'{ctx.author.mention} hat gecoinflipped und **{self.sys_random.choice(coinsides)}** bekommen! ಠ‿ಠ')

    @commands.command(help='This command performs a lol coinflip for you or somebody else (german).', aliases=["lolflip", "lolcoin"])
    async def lolcoinflip(self, ctx, *, username=None):
        coinsides = ['wird feeden 🙃', 'wird inten 😭', 'hat carry boots an!! 😮 🥾', 'ist sheesh drauf! 🤩', 'es ist GG 🤗', 'es ist ein ff angle 💀']
        if username == None:
            await ctx.send(f'{ctx.author.mention} hat gecoinflipped und **{self.sys_random.choice(coinsides)}**')
        else:
            mentions_matches = ['<@!','>']
            if all(x in username for x in mentions_matches):
                await ctx.send(f'{username} hat gecoinflipped und **{self.sys_random.choice(coinsides)}**')
            else:
                member = ctx.guild.get_member_named(username)
                if member != None:
                    await ctx.send(f'{member.mention} hat gecoinflipped und **{self.sys_random.choice(coinsides)}**')
                else:
                    await ctx.send(f'**{username}** hat gecoinflipped und **{self.sys_random.choice(coinsides)}**')

    @commands.command(help='This command performs rock-paper-scissors for you (german).', aliases=["enemenemiste", "schnickschnackschnuck"])
    async def fliflaflu(self, ctx):
        fliflaflu = ['✂️ Schere', '🪨 Stein', '🧻 Papier']
        await ctx.send(f'{ctx.author.mention} hat **{self.sys_random.choice(fliflaflu)}** genommen!')

    @commands.command(help='This command slaps someone!', aliases=['punch', 'hit'])
    async def slap(self, ctx, *, username=None):
        slaps = [
            'https://c.tenor.com/_aIyKVBt8dUAAAAd/animated-couple.gif', 
            'https://c.tenor.com/m14m8vGLFugAAAAd/asobi-asobase-anime.gif', 
            'https://c.tenor.com/gIaioChTOloAAAAd/cat-cute.gif',
            'https://c.tenor.com/x4RluZcWrWwAAAAd/slap.gif',
            'https://c.tenor.com/aA5D_h_ej-QAAAAd/cute-slap.gif',
            'https://c.tenor.com/mMGM1FfaXLgAAAAd/slap-cat.gif',
            'https://c.tenor.com/Jpp7qo6lEHYAAAAd/mochi-cat.gif',
            'https://c.tenor.com/oayQFdQOMRUAAAAd/slap-face.gif',
            'https://c.tenor.com/HiOIMkcHywUAAAAd/tom-slaps-on-ass.gif',
            'https://c.tenor.com/Q3CI345S0RsAAAAd/mochicat-slap.gif'
        ]
        slap_gif = self.get_random_gif('hit')

        embed = discord.Embed(
            color=discord.Color.blurple()
        ).set_image(url=slap_gif)

        if username != None:
            mentions_matches = ['<@!','>']
            if all(x in username for x in mentions_matches):
                embed.description = f'{ctx.author.mention} slapped {username}!'
            else:
                member = ctx.guild.get_member_named(username)
                if member != None:
                    embed.description = f'{ctx.author.mention} slapped {member.mention}!'
                else:
                    embed.description = f'{ctx.author.mention} slapped **{username}**!'

        await ctx.send(embed=embed)

    @commands.command(help='This command selects an option from a list of options for you.', aliases=["select", "choice"])
    async def roulette(self, ctx, *, options):
        parsed_list = list(options.split(" "))
        list_to_string = ', '.join(parsed_list)

        embed = (discord.Embed(title='🎲  Roulette',
                               color=discord.Color.blurple())
                               .add_field(name='Options', value=f'{list_to_string}'.format(self), inline=False)
                               .add_field(name='Selected', value=f'{self.sys_random.choice(parsed_list)}'.format(self), inline=False))

        await ctx.send(embed=embed)

    @commands.command(help='This command sends a tenor gif according to your search keyword.')
    async def gif(self, ctx, *, search):
        embed = discord.Embed(
            color=discord.Color.blurple()
        ).set_image(url=self.get_random_gif(search))

        await ctx.send(embed=embed)

    def get_random_gif(self, searchTerm):
        response = requests.get('https://g.tenor.com/v1/search?q={}&key={}&limit=50'.format(searchTerm, tenor_token))
        data = response.json()
        
        gif = self.sys_random.choice(data['results'])
        return gif['media'][0]['gif']['url']
    
    def setup(client):
        client.add_cog(general(client))

        
repeating = {}
songs = {}
current_song = {}

class music(commands.Cog):
    def __init__(self, client):
        self.client = client

    #TODO: spotify support (if possible?)
    
    @commands.command(help='This command makes the bot join the voice channel')
    async def join(self, ctx):
        global songs, current_song, repeating

        if ctx.author.voice is None:
            await ctx.send('❌ Ur not in a voice channel lmao.')
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
            await ctx.send('❌ Nothing to skip.')
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
            await ctx.send('❌ Nothing to pause.')
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
            await ctx.send('❌ Nothing is paused.')
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
            await ctx.send('❌ Nothing to repeat.')
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
            await ctx.send('❌ Queue is empty, nothing to shuffle.')
            return
        else:
            random.shuffle(songs[ctx.guild.id])
            await ctx.send('🎧 **Queue shuffled.** Check via ``!queue``.')

    @commands.command(help='This command stops the current song and empties the queue')
    async def stop(self, ctx):
        global songs, current_song, repeating

        voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
        if not await self.voice_check(ctx, voice):
            return
        elif not voice.is_playing():
            await ctx.send('❌ Nothing to stop.')
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
            await ctx.send('❌ Queue is empty, nothing to clear.')
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
            await ctx.send('❌ Queue is empty, nothing to remove.')
            return
        else:
            if index > 0 and index <= len(songs[ctx.guild.id]):
                tmp = songs[ctx.guild.id][index - 1]
                del(songs[ctx.guild.id][index - 1])
                await ctx.send(f'🎧 **Removed:** {tmp.title}')
            else:
                await ctx.send('❌ Invalid index. Check for it via ``!queue``.')

    @commands.command(help='This command displays the current queue')
    async def queue(self, ctx):
        voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
        
        if not await self.voice_check(ctx, voice):
            return
        elif not songs[ctx.guild.id]:
            await ctx.send('❌ Queue is empty, nothing to show.')
            return
        else:
            titles = [song.title for song in songs[ctx.guild.id]]
            enum_titles = []

            for idx, val in enumerate(titles, start=1):
                enum_titles.append(f'**{idx}.** {val}')

            durations = [song.duration for song in songs[ctx.guild.id]]
            total_duration = sum(durations)

            try:
                embed = (discord.Embed(title='🎧  Current Queue',
                                    description='\n'.join(enum_titles).format(self),
                                    color=discord.Color.blurple())
                                    .add_field(name='Total time', value=self.parse_duration(duration=total_duration))
                                    )
                await ctx.send(embed=embed)
            except:
                await ctx.send('❌ Too many songs to display!')
                embed = (discord.Embed(title='🎧  Current Queue',
                                    description=f'{len(titles)} songs enqueued.'.format(self),
                                    color=discord.Color.blurple())
                                    .add_field(name='Total time', value=self.parse_duration(duration=total_duration))
                                    )
                await ctx.send(embed=embed)

    # TODO: Add time left / progress bar?
    @commands.command(help='This command displays the current song', aliases=['np'])
    async def nowplaying(self, ctx):
        voice = discord.utils.get(client.voice_clients, guild=ctx.guild)

        if not await self.voice_check(ctx, voice):
            return
        elif current_song[ctx.guild.id] == None or not voice.is_playing():
            await ctx.send('❌ Nothing is being played right now.')
        else:
            await ctx.send(embed=self.create_play_embed(ctx=ctx, song=None))

    @commands.command(help='This command plays songs or adds them to the current queue')
    async def play(self, ctx, *, url):
        global songs, current_song, repeating

        voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
        if ctx.author.voice is None:
            await ctx.send("❌ Ur not in a voice channel lmao.")
            return
        elif voice and ctx.voice_client.channel != ctx.author.voice.channel:
            await ctx.send('❌ Ur not in that voice channel. 🌚')
            return

        if not voice:
            await ctx.invoke(self.client.get_command('join'))

        voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
        if voice:
            sources = await YTDLSource.create_source(ctx, search=url, loop=self.client.loop)
            try:
                songs[ctx.guild.id].extend(sources)
            except:
                songs[ctx.guild.id] = sources

            if not voice.is_playing():
                try:
                    current_song[ctx.guild.id] = songs[ctx.guild.id].pop(0)
                    ctx.voice_client.play(current_song[ctx.guild.id], after=lambda e: print('Player error: %s' % e) if e else asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.client.loop))
                    if len(sources) > 1:
                        await ctx.send(f'🎧 **Enqueued:** {len(sources)} songs')
                    await ctx.send(embed=self.create_play_embed(ctx=ctx, song=None))
                except YTDLError as e:
                    await ctx.send('⚠️ An error occurred while processing this request: {}'.format(str(e)))
            else:
                if len(sources) > 1:
                    await ctx.send(f'🎧 **Enqueued:** {len(sources)} songs')
                else:
                    await ctx.send(embed=self.create_play_embed(ctx=ctx, song=sources[0]))

    async def play_next(self, ctx):
        global songs, current_song, repeating

        if songs[ctx.guild.id] or repeating[ctx.guild.id]:
            try:
                if not repeating[ctx.guild.id]:
                    current_song[ctx.guild.id] = songs[ctx.guild.id].pop(0)
                    ctx.voice_client.play(current_song[ctx.guild.id], after=lambda e: print('Player error: %s' % e) if e else asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.client.loop))
                    await current_song[ctx.guild.id].channel.send(f'🎧 **Now playing:** {current_song[ctx.guild.id].title}') 
                else:
                    repeated_song = await YTDLSource.create_source(ctx, current_song[ctx.guild.id].url, loop=self.client.loop)
                    current_song[ctx.guild.id] = repeated_song[0]
                    ctx.voice_client.play(current_song[ctx.guild.id], after=lambda e: print('Player error: %s' % e) if e else asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.client.loop))
            except YTDLError as e:
                await ctx.send('⚠️ An error occurred while processing this request: {}'.format(str(e)))
        else:
            # inactivity disconnect after 3 minutes
            await asyncio.sleep(210)
            voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
            if not voice.is_playing():
                await ctx.voice_client.disconnect()

                songs[ctx.guild.id] = []
                repeating[ctx.guild.id] = False
                current_song[ctx.guild.id] = None

    # create song overview embed
    def create_play_embed(self, ctx, song):
        if song == None:
            headline = '🎧  Now playing'
            song = current_song[ctx.guild.id]
        else:
            headline = '🎧  Added to queue'

        # prevent embed breaking when playing LIVE video
        if song.duration == '':
            duration = '/'
        else:
            duration = song.duration

        embed = (discord.Embed(title=headline,
                               description=f'{song.title}'.format(self),
                               color=discord.Color.blurple())
                 .add_field(name='Duration', value=self.parse_duration(duration))
                 .add_field(name='Channel', value=f'[{song.uploader}]({song.uploader_url})'.format(self))
                 .add_field(name='URL', value=f'[YouTube]({song.url})'.format(self))
                 .set_thumbnail(url=song.thumbnail)
                 .set_footer(text='Requested by {}'.format(song.requester), icon_url=song.requester.avatar_url))
        return embed

    # check voice_states of member and bot
    async def voice_check(self, ctx, voice):
        if not voice:
            await ctx.send('❌ Huh? I\'m not in a voice channel right now.')
            return False
        elif ctx.author.voice is None:
            await ctx.send("❌ Ur not in a voice channel lmao.")
            return False
        elif ctx.voice_client.channel != ctx.author.voice.channel:
            await ctx.send('❌ Ur not in that voice channel. 🌚')
            return False
        else:
            return True

    # calculate durations for song/queue
    @staticmethod
    def parse_duration(duration):
        if duration == '/':
            return '/'
        
        duration = int(duration)
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

    def setup(client):
        client.add_cog(music(client))

        
# customize !help command
class EmbedHelpCommand(commands.MinimalHelpCommand):
    async def send_pages(self):
        destination = self.get_destination()
        e = discord.Embed(title='🎧  Commands', color=discord.Color.blurple(), description='')
        for page in self.paginator.pages:
            e.description += page
        await destination.send(embed=e)

        
client = commands.Bot(command_prefix='!')
client.help_command = EmbedHelpCommand(no_category='misc')

# load cogs
cogs = [admin, general, music]
for i in range(len(cogs)):
    cogs[i].setup(client)

@client.event
async def change_status():
    await client.change_presence(activity=discord.Game(name="Fortnite"))

# send error messages
@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CommandNotFound):
        await ctx.send("❌ Huh? There is no such command (yet). Check commands via ``!help``.")
    else:
        await ctx.send(f"⚠️ {str(error)}")

# auto-disconnect when alone in channel
@client.event
async def on_voice_state_update(member, before, after):
    global songs, current_song, repeating

    voice_state = member.guild.voice_client
    if voice_state is None:
        return 

    # TODO: Bugged - leaves voice channel if ANY channel in guild has 1 member
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
