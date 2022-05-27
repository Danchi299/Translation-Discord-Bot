
print('Loading...')

#Discord
import discord
import discord.utils
from discord.ext import commands
from discord.ext import tasks

#Dependencies
from googletrans import Translator
from gtts import gTTS
import asyncio
import os

#-------------------------------------------------------------------------------------------

#Variables

bot = commands.Bot(command_prefix = '!')

bot.queue = []
bot.queueing = 0

bot.trans_channel = {''}
bot.read_channel = {''}
bot.lang = {'en'}

#-------------------------------------------------------------------------------------------

#Functions

def save(lang, text):
    
    if not lang: lang = Translator().translate(text ,dest = 'en').src
    
    gTTS(text, lang = lang).save("tts.mp3")


def queue_player(ctx):
    
    if bot.queue:
        
        voice = get_voice(ctx)
        if voice and voice.is_connected():
            
            lang, text = bot.queue[0]
            
            save(lang, text)
            
            voice.play(discord.FFmpegPCMAudio('tts.mp3', **{'before_options': ('-channel_layout mono'), 'options': ('-vn', '-loglevel quiet')}), after = lambda e: After(ctx), )
        
        else:
            bot.queue.pop(0)
            Send(ctx.channel, 'Not Connected To Voice Chat')
            bot.queueing = 0
            
    else: bot.queueing = 0
        

def play_queue(ctx):
    if not bot.queueing:
        if get_voice(ctx):
            bot.queueing = 1
            queue_player(ctx)


def After(ctx):
    bot.queue.pop(0)
    queue_player(ctx)


def Send(channel, text):
    loop = asyncio.get_event_loop()
    loop.create_task(channel.send(text))


def get_voice(ctx):
    return discord.utils.get(bot.voice_clients, guild=ctx.guild)

#voice = {}; exec(f"voice = discord.utils.get({user}, guild=ctx.guild)", locals() | globals(), voice); voice = voice['voice']

#-------------------------------------------------------------------------------------------
        
#Commands


#Class Voice Chat
class Voice_Chat(commands.Cog,name = 'Voice Chat'):
    @commands.command()
    async def join(self, ctx):
        
        voice = get_voice(ctx)
        
        x = 0
        if voice and voice.is_connected(): await voice.disconnect()
        else:  x = 1
        
        if ctx.author.voice: voice = ctx.author.voice.channel
        
        if voice:
            await voice.connect()
            if x: await ctx.channel.send(f"Joined {voice}")
            else: await ctx.channel.send(f"Rejoined {voice}")
        else: await ctx.channel.send("You Are Not In A Voice Channel")

    @commands.command()
    async def leave(self, ctx):
        voice = get_voice(ctx)
        if voice and voice.is_connected():
            await voice.disconnect()
            if random.randint(1,10) == 5: await ctx.channel.send(f"Right, {voice.channel}")
            else: await ctx.channel.send(f"Left {voice.channel}")
        else: await ctx.channel.send("Not Connected To Voice Channel")


    @commands.command(description='says text in voice chat')
    async def say(self, ctx):
        text, text = ctx.message.content.split(' ', 1)
        bot.queue.append((None, text))
        play_queue(ctx)


    @commands.command(description='set current TTS channel to read into voice \n!tts on \n2 - Enable TTS in Every Channel \n1 - Enable TTS in Current Channel \n0 - Disabel TTS in Current Channel \n-1 - Enable TTS in Every Channel')
    async def tts(self, ctx, text):
        text = text.lower()
        
        if text in ['2', 'all']:
            for channel in ctx.guild.text_channels:
                bot.read_channel.add(channel)
                
                
            await ctx.send('Global TTS ON')
            
        elif text in ['1', 'on']:
            bot.read_channel.add(ctx.channel)
            await ctx.send(f"TTS ON in {ctx.channel}")
            
        elif text in ['0', 'off']:
            try:
                bot.read_channel.remove(ctx.channel)
                await ctx.send(f"TTS OFF in {ctx.channel}")
            except Exception as e: 
                await ctx.send(f"TTS Was NOT ON in {ctx.channel}")
                
        elif text in ['-1', 'clear', 'stop']:
            bot.read_channel = {''}
            await ctx.send("TTS OFF")
            

    @commands.command(aliases = ['skip'])
    async def stop(self, ctx, num: int = 1):
        
        if num < 0: num = 1
        elif num > len(bot.queue) or not num:
            num = 0
            bot.queue = []
        
        if not bot.repeat and num != 0: num -= 1
        
        for i in range(num): bot.queue.pop(0)
        
        voice = get_voice(ctx)
        
        if voice and (voice.is_playing() or voice.is_paused()) : voice.stop()
            
        await ctx.message.add_reaction('✅')

bot.add_cog(Voice_Chat()) #End of Voice Chat Class


@bot.group(aliases = ['lang'], invoke_without_command=True)
async def language(ctx):
    await ctx.send('This Command Requires a SubCommand')
    
    
@language.command(aliases = ['1'])
async def add(ctx, lang: str = 'en'):
    
    lang = lang.lower()
    
    try:
        Translator().translate('0',dest = lang)
        bot.lang.add(lang)
        await ctx.send(f'Added {lang.upper()} to TTC')
        
    except ValueError:
        await ctx.send(f'No Such Code {lang.upper()}')

@language.command(aliases = ['0', 'del'])
async def remove(ctx, lang: str = 'en'):
    
    lang = lang.lower()
    
    bot.lang.remove(lang)
    await ctx.send(f'Removed {lang.upper()} from TTC')
        
@language.command(aliases = ['-1', 'clear'])
async def reset(ctx): 
    bot.lang = {'en'}
    await ctx.send('TTC Languages Reset')
        
        
@bot.command(description='set current Translation channel to read into voice \n!tts on \n2 - Enable Translation in Every Channel \n1 - Enable Translation in Current Channel \n0 - Disabel Translation in Current Channel \n-1 - Disable Translation in Every Channel')
async def ttc(ctx, text):
    text = text.lower()
    
    if text in ['2', 'all']:
        for channel in ctx.guild.text_channels:
            bot.trans_channel.add(channel)
        await ctx.send('Global Translation ON')
        
        
    elif text in ['1', 'on']:
        bot.trans_channel.add(ctx.channel)
        await ctx.send(f"Translation ON in {ctx.channel}")
        
        
    elif text in ['0', 'off']:
        try:
            bot.trans_channel.remove(ctx.channel)
            await ctx.send(f"Translation OFF in {ctx.channel}")
        except Exception as e: 
            await ctx.send(f"Translation Was NOT ON in {ctx.channel}")
        
        
    elif text in ['-1', 'clear', 'stop']:
        bot.trans_channel = {''}
        await ctx.send("Translation OFF")



#-------------------------------------------------------------------------------------------

#Events

@bot.event
async def on_message(ctx):
    
    if not ctx.author.bot:
        if ctx.content != '':
            if ctx.content[0] != '!':
                
                trans = ctx.channel in bot.trans_channel
                read = ctx.channel in bot.read_channel
                
                text = ''
                
                if trans:
                    
                    for i in bot.lang:
                        
                        t = Translator().translate(ctx.content, dest = i)
                        
                        if t.dest != t.src:
                            text += f'{t.dest}: \n{t.text}\n\n'
                            
                        if read: bot.queue.append((t.dest.upper(), t.text.title()))
                    
                    if text:
                        await ctx.channel.send(f'{ctx.author} Said: \n\n{text}')
                        
                    if read:
                        if discord.utils.get(bot.voice_clients, guild=ctx.guild):
                            play_queue(ctx)
                            
                        else:
                            await ctx.channel.send('Not Connected To Voice Chat\nTurning OFF TTS')
                            bot.read_channel = {''}
                    
                    
                elif read:
                    if discord.utils.get(bot.voice_clients, guild=ctx.guild):
                        
                        bot.queue.append((None, ctx.content))
                        play_queue(ctx)
                        
                    else:
                        await ctx.channel.send('Not Connected To Voice Chat\nTurning OFF TTS')
                        bot.read_channel = {''}
             
        await bot.process_commands(ctx)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

#-------------------------------------------------------------------------------------------

bot.run(os.environ['TOKEN'])
