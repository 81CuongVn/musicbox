'''
Main file for this music bot
* starts the bot
* loads cogs on startup
* key functionality is defined under ./cogs
'''

import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

import platform

# get bot token
load_dotenv()
bot_token = os.getenv("BOT_TOKEN")

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
print('-------------------')
for file in os.listdir('./cogs'):
        if file.endswith('.py'):
            extension = file[:-3]
            try:
                client.load_extension(f'cogs.{extension}')
                print(f'Loaded \'{extension}\' cog')
            except Exception as e:
                exception = f'{type(e).__name__}: {e}'
                print(f'Failed to load cog {extension}!\n{exception}')
print('-------------------')

# set status
@client.event
async def change_status():
    await client.change_presence(activity=discord.Game(name="Fortnite"))

# send error messages
@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CommandNotFound):
        await ctx.send('❌ Huh? There is no such command (yet). Check commands via ``!help``.')
    else:
        await ctx.send(f"⚠️ {str(error)}")

# send first welcome message
@client.event
async def on_guild_join(guild):
    general = discord.utils.find(lambda x: x.name == 'general',  guild.text_channels)
    allgemein = discord.utils.find(lambda x: x.name == 'allgemein',  guild.text_channels)

    if general and general.permissions_for(guild.me).send_messages:
        await general.send(f'🎧 **Hello {guild.name}!** My prefix is \'!\', use ``!help`` for more info :)')
    elif allgemein and allgemein.permissions_for(guild.me).send_messages:
        await allgemein.send(f'🎧 **Hello {guild.name}!** My prefix is \'!\', use ``!help`` for more info :)')
    
    print(f'Joined the server {guild.name}.')

# startup behavior
@client.event
async def on_ready():
    print('MusicBox is up and running!')
    print(f'Python version: {platform.python_version()}')
    print(f'Running on: {platform.system()} {platform.release()} ({os.name})')
    print('-------------------')
    await change_status()

# start the bot
client.run(bot_token)
