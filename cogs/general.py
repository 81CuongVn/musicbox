import os

import random
import discord
from discord.ext import commands
import requests
from dotenv import load_dotenv

# get token
load_dotenv()
tenor_token = os.getenv("TENOR_TOKEN")

class general(commands.Cog, name='general'):
    # improve random generator
    sys_random = random.SystemRandom()

    def __init__(self, client):
            self.client = client

    @commands.command(help='This command returns the current latency of the bot.')
    async def ping(self, ctx):
        await ctx.send(f'**Pong:** {round(self.client.latency * 1000)} ms')

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
            "senpai, pls no ;-;", 'Nah ⊙_⊙', 'Yas!!'
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

    @commands.command(help='This command determines a dere-type for someone!')
    async def dere(self, ctx, *, username):
        dere_types = {
            'bakadere': 'is very clumsy and stupid | more often than not, they lack common sense',
            'dandere': 'quiet, silent and asocial | come across as emotionless at times | will suddenly become talkative, sweet, and cute when alone with the right person | actually just shy',
            'darudere': 'often very lazy and dull | will usually ignore others and do whatever they want unless someone they care about asks them to do something or needs their help',
            'deredere': 'very sweet and energetic | usually cheerful and happy | tend to spread joyfulness to others',
            'hinedere': 'has cynical world views | cold-hearted | highly arrogant | has a soft side deep down that may reveal itself once their love interest breaks through',
            'hiyakasudere': 'likes to tease and flirt | sarcastic, mischievous, or at least playful',
            'kamidere': 'feels superior compared to others | highly arrogant, overconfident and proud | aren\'t afraid to speak their minds and show everyone how right they are | stubborn | narcissistic',
            'kanedere': 'attracted to others with money or status | gold digger',
            'kuudere': 'calm and collected on the outside | never panics | shows little emotion | tends to be a leader | often cold, blunt, and cynical | very caring on the inside, at least when it comes to the ones they love',
            'tsundere': 'usually stern, cold or hostile to the person they like and even others | occasionally showing the warm, loving feelings hidden inside | shy, nervous, insecure | can\'t help acting badly in front of their crush',
            'undere': 'says yes to pretty much everything the one they love says | easily manipulated'
        }

        dere_type, dere_info = self.sys_random.choice(list(dere_types.items()))

        mentions_matches = ['<@!','>']
        if all(x in username for x in mentions_matches):
            username = f'{username}'
        else:
            member = ctx.guild.get_member_named(username)
            if member != None:
                username = f'{member.mention}'
            else:
                username = f'{username}'

        embed = discord.Embed(
            title='💞  Dere-type Generator',
            description=f'**Person:** {username}\n**Type:** {dere_type}\n\n{dere_info}',
            color=discord.Color.blurple()
        )

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