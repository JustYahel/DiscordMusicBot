import discord
import asyncio
import youtube_dl
from discord.ext import commands

bot = commands.Bot(command_prefix="?", intents=discord.Intents.all())
bot.remove_command('help')
# noinspection SpellCheckingInspection
token = "MTA2NDk1MjcyNTAzODcwNjcwOA.Gc6_rf.rWkAALK_sB7gLup3TEKMeZxmXC3Ops1jKgTLdc"

voice_clients = {}

skip_song = False

# noinspection SpellCheckingInspection
yt_dl_opts = {'format': 'bestaudio/best',
              'postprocessors': [{
                  'key': 'FFmpegExtractAudio',
                  'preferredcodec': 'mp3',
                  'preferredquality': '192',
              }],
              'playliststart': 1,
              'playlistend': 1,
              'cookiefile': 'cookies.firefox-private.txt'
              }
ytdl = youtube_dl.YoutubeDL(yt_dl_opts)

ffmpeg_options = {'options': '-vn'}


@bot.event
async def on_ready():
    print(f"Bot Logged In As {bot.user}.")


async def check_in_vc(ctx):
    if ctx.author.voice is None:
        await ctx.send("You Are Not In A Voice Channel!", delete_after=5)
        return False


async def video_player(ctx, url):
    try:
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
        song = data['url']
        title = data['title']
        await ctx.channel.send(f"Now Playing {title}.", delete_after=data['duration'])
        player = discord.FFmpegPCMAudio(song, **ffmpeg_options)
        voice_clients[ctx.guild.id].play(player)

    except Exception as err:
        print(err)


async def playlist_player(ctx, url):
    try:
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))

        while data['entries'] != 0:
            w_url = data['entries'][0]['url']
            title = data['entries'][0]['title']
            msg = await ctx.channel.send(f"Now Playing {title}.", delete_after=data['entries'][0]['duration'])
            player = discord.FFmpegPCMAudio(w_url, **ffmpeg_options)
            voice_clients[ctx.guild.id].play(player)
            while voice_clients[ctx.guild.id].is_playing():
                await asyncio.sleep(1)
                global skip_song
                if not skip_song and not voice_clients[ctx.guild.id].is_connected():
                    await msg.delete()
                    return
                if skip_song:
                    voice_clients[ctx.guild.id].stop()
                    await msg.delete()
                    skip_song = False
                    break
            # noinspection SpellCheckingInspection
            ytdl.params['playliststart'] += 1
            # noinspection SpellCheckingInspection
            ytdl.params['playlistend'] += 1
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))

    except Exception as err:
        print(err)


@bot.command()
async def help(ctx):
    await ctx.channel.send("```Commands:\n?help    Displays This Panel\n?play [url]\n?pause\n?resume\n?stop\n?skip```",
                           delete_after=30)


# TODO: add search and shuffle support
@bot.command()
async def play(ctx, arg: str = None):
    if await check_in_vc(ctx):
        return

    if voice_clients[ctx.guild.id].is_playing():
        await ctx.send("Already Playing A Song!", delete_after=5)
        return

    if arg is None:
        await ctx.channel.send("Please Enter A URL.", delete_after=5)
        return
    try:
        voice_client = await ctx.author.voice.channel.connect()
        voice_clients[voice_client.guild.id] = voice_client
    except Exception as err:
        print(err)

    if "https://www.youtube.com/watch?v=" in arg and "&list" not in arg:
        await video_player(ctx, arg)

    elif "https://youtu.be/" in arg:
        await video_player(ctx, arg)

    elif "list" in arg:
        await playlist_player(ctx, arg)

    elif "https://www.youtube.com/results?search_query=" in arg:
        await ctx.send("Search Not Supported Yet.", delete_after=5)
        await stop(ctx)

    elif "https://www.youtube.com/channel/" in arg:
        await ctx.send("Channel Links Are Not Supported.", delete_after=5)
        await stop(ctx)

    elif "https://www.youtube.com/user/" in arg:
        await ctx.send("User Links Are Not Supported.", delete_after=5)
        await stop(ctx)

    elif "https://www.spotify.com/" in arg:
        await ctx.send("Spotify Support Coming Soon!", delete_after=5)
        await stop(ctx)

    else:
        await ctx.send("Please provide a valid URL.", delete_after=5)
        await stop(ctx)


@bot.command()
async def pause(ctx):
    if await check_in_vc(ctx):
        return
    try:
        voice_clients[ctx.guild.id].pause()
    except Exception as err:
        print(err)


@bot.command()
async def resume(ctx):
    if await check_in_vc(ctx):
        return
    try:
        voice_clients[ctx.guild.id].resume()
    except Exception as err:
        print(err)


@bot.command()
async def stop(ctx):
    if await check_in_vc(ctx):
        return
    try:
        voice_clients[ctx.guild.id].stop()
        await voice_clients[ctx.guild.id].disconnect()
    except Exception as err:
        print(err)


# TODO: fix this
@bot.command()
async def skip(ctx):
    if await check_in_vc(ctx):
        return
    try:
        global skip_song
        skip_song = True
    except Exception as err:
        print(err)


@bot.event
async def on_message(ctx):
    if ctx.channel.id != 1065361986638073916:
        return
    if ctx.author == bot.user:
        return

    await ctx.delete()
    await bot.process_commands(ctx)


@bot.event
async def del_ctx():
    await bot.wait_until_ready()
    channel = bot.get_channel(1065361986638073916)
    while not bot.is_closed():
        await channel.purge(limit=3)
        await asyncio.sleep(60)


bot.run(token)
