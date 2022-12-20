from keys import keys

import discord
from discord.ext import commands, tasks
import steam

import json
from urllib.request import urlopen

import asyncio
import aiohttp
import requests
import random

from colorthief import ColorThief
import webcolors

from thefuzz import fuzz, process

description = """Be notified about Steam"""

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix = "#", description = description, intents = intents)

newLine = "\n"

@bot.command()
async def search(ctx, input):
    if input is None:
        embed = discord.Embed()
        embed.description = "A short guide on how to use this command can be found [here](https://gist.github.com/skearya/2fe5a7cec196ba59f6bc9ca3864bd163)."
        await ctx.send(embed = embed)
        return
    
    url = f"http://api.steampowered.com/ISteamApps/GetAppList/v0002/?key={keys.steamAPI.key}&format=json"
    response = urlopen(url)
    _dataJSON = json.loads(response.read())[f"{id}"]

@bot.command()
async def game(ctx, id: int = None, cuc: str = "USD"):
    cuc = cuc.upper()
    if id is None:
        embed = discord.Embed()
        embed.description = "A short guide on how to use this command can be found [here](https://gist.github.com/skearya/2fe5a7cec196ba59f6bc9ca3864bd163)."
        await ctx.send(embed = embed)
        return

    with open("multiCountryCurrencies.json", "r") as multiCurrencyFile:
        multiCurrencyData = json.loads(multiCurrencyFile.read())["multiCountryCurrencies"]["currency"]
    with open("countries.json", "r") as mainCurrencyFile:
        mainCurrencyData = json.loads(mainCurrencyFile.read())["countries"]["country"]
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
    _dataJSON = json.loads(response.read())[f"{id}"]
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

            **Retail Price:** {f"{str(float(basePrice / 100))}{currency}" if hasPrice else "Free" if isFree else "TBA"}
            **Current Price:** {f'{str(float(currentPrice / 100))}{currency} {f"***({discount}% off)***" if discount != 0 else ""}' if hasPrice else "Free" if isFree else "TBA"}""")
        if not isDLC:
            embedDescription = embedDescription + f"{newLine}**DLC:** {dlcCount}"
        else:
            embedDescription = f"**DLC for {baseGame} *(ID: {baseGameID})***" + newLine + embedDescription
        embed.description = embedDescription
    else:
        embed = discord.Embed()
        embed.title = f"**Error**"

        embed.set_footer(text = f"Command requested by {ctx.author.display_name}", icon_url = ctx.author.avatar.url)
        
        embed.color = int("0xE36D6D", 16) 

        embed.description = "**The app you requested does not exist**"

    await ctx.send(embed = embed)

@bot.command()
async def user(ctx, id: str = None):
    if id is None:
        embed = discord.Embed()
        embed.description = "A short guide on how to use this command can be found [here](https://gist.github.com/skearya/2fe5a7cec196ba59f6bc9ca3864bd163)."
        await ctx.send(embed = embed)
        return
    
    await ctx.send(f"https://steamcommunity.com/id/{id}")

@bot.command()
async def prestonpc(ctx):
    if ctx.message.author.id == keys.ids.user.uuid1:
        await ctx.send('nah')
        return
    else:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.catboys.com/img") as resp:
                data = await resp.json()
                await ctx.send(data["url"])

@bot.command()
async def shutdown(ctx):
    exit()

bot.run(keys.bot.token)