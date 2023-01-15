from keys import keys

import discord
from discord.ext import commands, tasks
import steam

import ujson
from urllib.request import urlopen

import asyncio
import aiohttp

from colorthief import ColorThief
import webcolors

from thefuzz import fuzz, process

description = """Be notified about Steam"""

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix = "#", description = description, intents = intents)

newLine = "\n"

with open("multiCountryCurrencies.json", "r") as multiCurrencyFile:
        multiCurrencyData = ujson.loads(multiCurrencyFile.read())["multiCountryCurrencies"]["currency"]
with open("countries.json", "r") as mainCurrencyFile:
    mainCurrencyData = ujson.loads(mainCurrencyFile.read())["countries"]["country"]

@bot.command()
async def search(ctx, cuc: str, *, usrInput: str):
    if usrInput is None:
        embed = discord.Embed()
        embed.description = "A short guide on how to use this command can be found [here](https://gist.github.com/skearya/2fe5a7cec196ba59f6bc9ca3864bd163)."
        await ctx.send(embed = embed)
        return

    cuc = cuc.upper()
    validCurrency = False
    for i in multiCurrencyData:
        if validCurrency:
            break
        if i["currencyCode"] == cuc:
            validCurrency = True
    for i in mainCurrencyData:
        if validCurrency:
            break
        if i["currencyCode"] == cuc:
            validCurrency = True

    if not validCurrency:
        embed = discord.Embed()
        embed.title = "**You Entered an Invalid Currency**"
        embed.description = "A short guide on how to use this command can be found [here](https://gist.github.com/skearya/2fe5a7cec196ba59f6bc9ca3864bd163)."
        await ctx.send(embed = embed)
        return
    
    url = f"http://api.steampowered.com/ISteamApps/GetAppList/v0002/?key={keys.steamAPI.key}&format=json"
    response = urlopen(url)
    dataJSON = ujson.loads(response.read())["applist"]["apps"]

    names = []
    for i in dataJSON:
        names.append((i["name"], fuzz.ratio(i["name"], usrInput), i["appid"]))

    matches = []
    for i in range(0, 10):
        max1 = (None, 0, None)

        for x in range(len(names)):
            if names[x][1] > max1[1]:
                max1 = names[x]
        
        names.remove(max1)
        matches.append(max1)

    embed = discord.Embed()
    embed.title = f'**Search Results For "{usrInput}"**'
    embed.description = (f"""
        **1:** {matches[0][0]}
        
        **2:** {matches[1][0]}
        
        **3:** {matches[2][0]}
        
        **4:** {matches[3][0]}
        
        **5:** {matches[4][0]}
        
        **6:** {matches[5][0]}
        
        **7:** {matches[6][0]}
        
        **8:** {matches[7][0]}
        
        **9:** {matches[8][0]}
        
        **10:** {matches[9][0]}""")

    embed.set_footer(text = f"Command requested by {ctx.author.display_name}", icon_url = ctx.author.avatar.url)
    await ctx.send(embed = embed)

    def check(msg):
        return msg.channel == ctx.channel and int(msg.content) > 0 and int(msg.content) <= 10

    try:
        msg = await bot.wait_for("message", check = check, timeout = 15)
        await game_command_logic(ctx, matches[int(msg.content) - 1][2], cuc)
    except asyncio.TimeoutError:
        embed = discord.Embed()
        embed.title = "**You Didn't Enter a Valid Choice in Time**"
        embed.description = "A short guide on how to use this command can be found [here](https://gist.github.com/skearya/2fe5a7cec196ba59f6bc9ca3864bd163)."
        await ctx.send(embed = embed)


async def game_command_logic(ctx, id: int = None, cuc: str = "USD"):
    cuc = cuc.upper()
    if id is None:
        embed = discord.Embed()
        embed.description = "A short guide on how to use this command can be found [here](https://gist.github.com/skearya/2fe5a7cec196ba59f6bc9ca3864bd163)."
        await ctx.send(embed = embed)
        return

    cc = "us"
    if cuc != "USD":
        for i in multiCurrencyData:
            if i["currencyCode"] == cuc:
                cc = i["countryCode"].lower()
        if cc == "us":
            for i in mainCurrencyData:
                if i["currencyCode"] == cuc:
                    cc = i["countryCode"].lower()

    url = f"http://store.steampowered.com/api/appdetails?appids={id}&cc={cc}"
    response = urlopen(url)
    _dataJSON = ujson.loads(response.read())[f"{id}"]
    if _dataJSON["success"] == True:
        dataJSON = _dataJSON["data"]

        name = dataJSON["name"]
        img = dataJSON["header_image"]
        
        dev = dataJSON["developers"][0]
        publisher = dataJSON["publishers"][0]
        
        isFree = dataJSON["is_free"]
        hasPrice = False
        if "price_overview" in dataJSON:
            priceDATA = dataJSON["price_overview"]
            basePrice = priceDATA["initial"]
            currentPrice = priceDATA["final"]
            currency = priceDATA["currency"]
            discount = priceDATA["discount_percent"]
            hasPrice = True
        releaseDate = dataJSON["release_date"]["date"]
        isComingSoon = dataJSON["release_date"]["coming_soon"]

        isDLC = False
        baseGame = None
        if dataJSON["type"] == "dlc":
            isDLC = True
            baseGame = dataJSON["fullgame"]["name"]
            baseGameID = dataJSON["fullgame"]["appid"]
        dlcCount = None
        if "dlc" in dataJSON:
            dlcCount = len(dataJSON["dlc"]) - 1

        embed = discord.Embed()
        embed.title = f"**{name}**"
        embed.set_image(url = img)

        embed.set_footer(text = f"Command requested by {ctx.author.display_name}", icon_url = ctx.author.avatar.url)
        
        imageColorThief = ColorThief(urlopen(img))
        mainColor = imageColorThief.get_color(quality = 1)
        embed.color = int(webcolors.rgb_to_hex(mainColor).replace("#", "0x"), 16)
        
        embedDescription = (f"""
            https://store.steampowered.com/app/{id}/

            **Devloper:** {dev}
            **Publisher:** {publisher}

            **Release Date:** {releaseDate if not isComingSoon else f"Coming Soon ({releaseDate})"}

            **Retail Price:** {f"{str(float(basePrice / 100))} **{currency}**" if hasPrice else "Free" if isFree else "TBA"}
            **Current Price:** {f'{str(float(currentPrice / 100))} **{currency}** {f"***({discount}% off)***" if discount != 0 else ""}' if hasPrice else "Free" if isFree else "TBA"}""")
        
        if not isDLC:
            embedDescription = embedDescription + f"{newLine}**DLC:** {dlcCount}"
        else:
            embedDescription = f"**DLC for {baseGame}** {newLine}{embedDescription}"
        embed.description = embedDescription
    else:
        embed = discord.Embed()
        embed.title = f"**Error**"

        embed.set_footer(text = f"Command requested by {ctx.author.display_name}", icon_url = ctx.author.avatar.url)
        
        embed.color = int("0xE36D6D", 16) 

        embed.description = "**The app you requested does not exist**"

    await ctx.send(embed = embed)

@bot.command()
async def game(ctx, id: int = None, cuc: str = "USD"):
    await game_command_logic(ctx, id, cuc)

@bot.command()
async def user(ctx, id: str = None):
    if id is None:
        embed = discord.Embed()
        embed.description = "A short guide on how to use this command can be found [here](https://gist.github.com/skearya/2fe5a7cec196ba59f6bc9ca3864bd163)."
        await ctx.send(embed = embed)
        return
    
    await ctx.send(f"https://steamcommunity.com/id/{id}")

@bot.command()
async def shutdown(ctx):
    exit()

bot.run(keys.bot.token)