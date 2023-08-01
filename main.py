import datetime
import string
import discord
from discord import app_commands
from discord.ext import commands
import json
import random
import time
import asyncio
import threading
import os
from enum import Enum
from discord import Button, ButtonStyle
import requests
import math
from flask import Flask, request
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

Config = {
    "Towers" : {
        "WinChance" : 64,  # Percent they will win when they click a tower
        "Multis" : [1.42, 2.02, 2.86, 4.05, 5.69]  # Multipliers On The Blocks
    },
    "Mines" : {
        "House" : 0.075,  # The Multiplier Will Be Multiplied by 1.00 - This
        "Channel" : "" # REQUIRED this is a webhook link, when someome makes a mine game the layout will be posted to this channel. Make sure only you can see the channel this webhook is in
    },
    "Crash" : {
        "InstaCrashChance" : 10,  # Chance That It Will Crash at 1.00x
        "CrashChance" : 2,  # The Lower This Number Is The Higher Your Multipliers Will Average, I find 2 is the best
        "ChannelID" : "1133722538678161519"  # Id of the channel crash games will be in
    },
    "Deposits": {
        "Channel": "1133720318914084885" # Id of Channel Deposits will be shown in
    },
    "Withdraws": {
        "Channel": "1133720389558743110" # Id of Channel withdraws will be shown in
    },
    "Coinflip" : {
        "1v1" : "1133720431577276447",  # Channel That Coinflips Be In
        "House" : 2.5  # House Edge (%)
    },
    "Rains" : {
        "Channel" : "1133720412921016351" # Set to the id the channel rains will be in
    },
    "Rakeback" : 4, # Rakeback %
    "PathToExecutorWorkspace" : "", # Path To Your Executors Workspace (for auto depos and withdraws)
    "RobloxUser" : "fersord",  # Your roblox username, people will deposit to this account
    "DiscordBotToken": "your bot token" # The token of the discord bot
}

def percentage(percent, whole) :
    return (percent * whole) / 100.0
def check_forecast(key, lat, lon) :
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={key}"
    response = requests.get(url)

    if response.status_code == 200:
        return response.json()
    else:
        return None


rb = Config['Rakeback']
username = Config['RobloxUser']
workspacefolder = Config['PathToExecutorWorkspace']
crashid = Config['Crash']['ChannelID']

TowersMultis = [1.0, 1.5, 2, 2.5, 3.0, 3.5]

MineHouseEdge = Config['Mines']['House']


def roll_percentage(percent) :
    random_num = random.uniform(0, 100)
    if random_num <= percent :
        return True
    else :
        return False


def calculate_mines_multiplier(minesamount, diamonds, houseedge) :
    def nCr(n, r) :
        f = math.factorial
        return f(n) // f(r) // f(n - r)

    house_edge = houseedge
    return (1 - house_edge) * nCr(25, diamonds) / nCr(25 - minesamount, diamonds)

def generate_board(minesa) :
    board = [
        ["s", "s", "s", "s", "s"],
        ["s", "s", "s", "s", "s"],
        ["s", "s", "s", "s", "s"],
        ["s", "s", "s", "s", "s"],
        ["s", "s", "s", "s", "s"],
    ]
    for index in range(0, minesa) :
        end = False
        while not end :
            row = random.randint(0, 4)
            collum = random.randint(0, 4)
            if board[row][collum] == "s" :
                board[row][collum] = "m"
                end = True
    return board


class CoinSide(Enum) :
    Heads = "Heads"
    Tails = "Tails"


class RPSSide(Enum) :
    Rock = "Rock"
    Paper = "Paper"
    Scissors = "Scissors"
rpsgames = []
codes = []
words = ['apple', 'banana', 'fruit', 'car', 'base', 'good', 'life', 'up', 'shift', 'left', 'down', 'code']
rains = []
crash = {
    "FinishTime" : 0,
    "Multi" : 0,
    "Users" : []
}
workspacefolder += "/gamble"  # Ignore
os.makedirs(workspacefolder, exist_ok=True)
temp = open(f"{workspacefolder}/withdraws.txt", "w")
temp.close()
temp = open(f"{workspacefolder}/deposits.txt", "w")
temp.close()


def suffix_to_int(s) :
    suffixes = {
        'k' : 3,
        'm' : 6,
        'b' : 9,
        't' : 12
    }

    suffix = s[-1].lower()
    if suffix in suffixes :
        num = float(s[:-1]) * 10 ** suffixes[suffix]
    else :
        num = float(s)

    return int(num)


def readdata() :
    with open("userdata.json", "r") as infile :
        # Load the data from the file into a dictionary
        userdata = json.load(infile)

        # Close the file

        infile.close()
        return (userdata)


def writedata(data) :
    with open("userdata.json", "w") as outfile :
        json.dump(data, outfile)
        outfile.close()

def get_cases() :
    with open("cases.json", "r") as infile :
        # Load the data from the file into a dictionary
        userdata2 = json.load(infile)

        infile.close()
        return userdata2['Cases']

def add_bet(userid, bet, winnings):
    if userid != "757289489373593661" and userid != "950134688683528283":
        with open("bets.json", "r") as infile :
            userdata = json.load(infile)
        userdata['bets'].append([userid, round(time.time()), bet, winnings])
        with open("bets.json", "w") as outfile:
            json.dump(userdata, outfile)
            outfile.close()

caseslist = []
for case in get_cases():
    caseslist.append(case['Name'])
def get_affiliate(uid) :
    data = None
    with open("affiliates.json", "r") as infile :
        data = json.load(infile)
    aff = data['affiliates']
    affiliate = None
    for link in aff :
        affiliator = link[0]
        affiliate = link[1]
        if affiliator == uid :
            return affiliate
    return None


def set_affiliate(uid, uid2) :
    with open("affiliates.json", "r") as infile :
        data = json.load(infile)
    data['affiliates'].append([uid, uid2])
    with open("affiliates.json", "w") as outfile :
        json.dump(data, outfile)
        outfile.close()


def register_user(uid) :
    data = readdata()
    data["gems"].append([uid, 0, 100000000])
    writedata(data)


def is_registered(uid) :
    data = readdata()
    found = False
    for user in data['gems'] :
        if user[0] == uid :
            found = True
    return found


def get_gems(uid) :
    data = readdata()
    gems = 0
    for user in data['gems'] :
        if user[0] == uid :
            gems = user[1]
    return gems


def set_gems(uid, gems) :
    data = readdata()
    count = 0
    for user in data['gems'] :
        if user[0] == uid :
            data['gems'][count][1] = gems
        count += 1
    writedata(data)


def get_rake_back(uid) :
    data = readdata()
    rakeback = 0
    for person in data['gems'] :
        uid2 = person[0]
        if uid2 == uid :
            if not len(person) >= 4 :
                person.append(0)
                writedata(data)
                return 0
            else :
                return person[3]


def set_rake_back(uid, amount) :
    data = readdata()
    rakeback = 0
    for person in data['gems'] :
        uid2 = person[0]
        if uid2 == uid :
            if not len(person) >= 4 :
                person.append(amount)
            else :
                person[3] = amount
    writedata(data)


def add_rake_back(uid, amount) :
    rake_back = get_rake_back(uid)
    set_rake_back(uid, rake_back + amount)


def add_gems(uid, gems) :
    set_gems(uid, get_gems(uid) + gems)


def subtract_gems(uid, gems) :
    set_gems(uid, get_gems(uid) - gems)


add_gems("123", 20)


def set_crash_join(uid, gems) :
    data = readdata()
    count = 0
    for user in data['gems'] :
        if user[0] == uid :
            data['gems'][count][2] = gems
        count += 1
    writedata(data)


def get_crash_join_amount(uid) :
    data = readdata()
    gems = 0
    for user in data['gems'] :
        if user[0] == uid :
            gems = user[2]
    return gems


def send_message(message) :
    f = open(f"{workspacefolder}/withdraws.txt", "a")
    f.write(f"{message}\n")
    f.close()


def add_suffix(inte) :
    gems = inte
    if gems >= 1000000000000 :  # if gems are greater than or equal to 1 trillion
        gems_formatted = f"{gems / 1000000000000:.1f}t"  # display gems in trillions with one decimal point
    elif gems >= 1000000000 :  # if gems are greater than or equal to 1 billion
        gems_formatted = f"{gems / 1000000000:.1f}b"  # display gems in billions with one decimal point
    elif gems >= 1000000 :  # if gems are greater than or equal to 1 million
        gems_formatted = f"{gems / 1000000:.1f}m"  # display gems in millions with one decimal point
    elif gems >= 1000 :  # if gems are greater than or equal to 1 thousand
        gems_formatted = f"{gems / 1000:.1f}k"  # display gems in thousands with one decimal point
    else :  # if gems are less than 1 thousand
        gems_formatted = str(gems)  # display gems as is
    return gems_formatted
class SystemRainButtons(discord.ui.View) :
    def __init__(self, message, entries, amount, ends, emoji) :
        super().__init__(timeout=None)
        self.message = message
        self.entries = entries
        self.amount = amount
        self.ends = ends
        self.emoji = emoji
        self.setup_buttons()

    def setup_buttons(self) :
        button = discord.ui.Button(label="Join", custom_id=f"join", style=discord.ButtonStyle.green, emoji="✅")
        button.callback = self.button_join
        self.add_item(button)

    async def button_join(self, interaction: discord.Interaction) :
        await interaction.response.defer()
        uid = str(interaction.user.id)
        found = False
        for person in self.entries:
            print(person)
            if person == uid:
                found = True
        print(found)
        if not found:
            self.entries.append(uid)
            embed = discord.Embed(title=f"{self.emoji} Rain In Progress",
                                  description=f"A Rain Has Been Started By ``System``",
                                  color=0x2ea4ff)
            embed.set_author(name="Gamble Bot",
                             icon_url="https://cdn.itemsatis.com/uploads/post_images/pet-simulator-x-10b-gems-81004359.png")
            embed.set_footer(text="rains")
            embed.add_field(name="Details",
                            value=f":gem: **Amount:** ``{add_suffix(self.amount)}``\n:money_mouth: **Entries:** ``{len(self.entries)}``\n:gem: **Gems Per Person:** ``{add_suffix(self.amount / len(self.entries))}``\n:clock1: **Ends:** {self.ends}")
            await self.message.edit(embed=embed,
                               view=SystemRainButtons(amount=self.amount, entries=self.entries,
                                                ends=f"{self.ends}",
                                                message=self.message,emoji=self.emoji))
async def system_rain(amount, duration):
    channel = bot.get_channel(int(Config['Rains']['Channel']))
    rains.append([])
    rain = rains[-1]
    joined = 0
    if joined == 0 :
        joined = 1
    emoji = "🌤️"
    if amount <= 500000000 :
        emoji = "🌤️"
    elif amount <= 2000000000 :
        emoji = "⛅"
    elif amount <= 5000000000 :
        emoji = "🌥️"
    elif amount <= 10000000000 :
        emoji = "🌦️"
    elif amount <= 20000000000 :
        emoji = "🌧️"
    else :
        emoji = "⛈"
    embed = discord.Embed(title=f"{emoji} Rain In Progress",
                          description=f"A Rain Has Been Started By ``System``",
                          color=0x2ea4ff)
    embed.set_author(name="Gamble Bot",
                     icon_url="https://cdn.itemsatis.com/uploads/post_images/pet-simulator-x-10b-gems-81004359.png")
    embed.set_footer(text="rains")
    embed.add_field(name="Details",
                    value=f":gem: **Amount:** ``{add_suffix(amount)}``\n:money_mouth: **Entries:** ``{0}``\n:gem: **Gems Per Person:** ``{add_suffix(amount / joined)}``\n:clock1: **Ends:** <t:{round(time.time() + duration)}:R>")
    message = await channel.send(content=".")
    await message.edit(embed=embed,
                       view=SystemRainButtons(amount=amount, entries=rain, ends=f"<t:{round(time.time() + duration)}:R>",
                                        message=message, emoji=emoji))
    await asyncio.sleep(duration)
    if len(rain) == 0 :
        gpp = amount
    else :
        gpp = amount / len(rain)
    for person in rain :
        add_gems(person, gpp)
    embed = discord.Embed(title=":sunny: Rain Ended",
                          description=f"A Rain Has Been Started By ``System`` (ended)",
                          color=0xffe74d)
    embed.set_author(name="Gamble Bot",
                     icon_url="https://cdn.itemsatis.com/uploads/post_images/pet-simulator-x-10b-gems-81004359.png")
    embed.set_footer(text="rains")
    embed.add_field(name="Details",
                    value=f":gem: **Amount:** ``{add_suffix(amount)}``\n:money_mouth: **Entries:** ``{len(rain)}``\n:gem: **Gems Per Person:** ``{add_suffix(gpp)}``\n:clock1: **Ended:** <t:{round(time.time())}:R>")
    await message.edit(embed=embed, view=None)

def generate_crash_multi() :
    m = 0.98
    if roll_percentage(Config['Crash']['InstaCrashChance']) :
        m = 0.98
        return m
    while 1 :
        m = round(0.01 + m, 2)
        if roll_percentage(Config['Crash']['CrashChance']) :
            return m


crash_info = {}
bot = commands.Bot(command_prefix="?", intents=discord.Intents.all())
async def test_code(code, gems) :
    count = 0
    for item in codes :
        if item[1] == code :
            add_gems(item[0], gems)
            channel = bot.get_channel(int(Config['Deposits']['Channel']))
            embed = discord.Embed(description=f":gem: <@{item[0]}> Deposited {add_suffix(gems)}!", color = 0x8ae2ff)
            await channel.send(embed=embed)
            codes.remove(item)
        count += 1
async def background_function() :
    while 1 :
        await asyncio.sleep(1)
        f = open(f"{workspacefolder}/deposits.txt", "r")
        lines = f.read()
        f.close()
        try :
            messages = lines.split("\n")
            for message in messages :
                msg = message.split(",")
                code = msg[0]
                gems = int(msg[1])
                await test_code(code=code, gems=gems)
        except :
            pass
        f = open(f"{workspacefolder}/deposits.txt", "w")
        f.writelines("")


class CashoutCrash(discord.ui.View) :
    def __init__(self, msg) :
        super().__init__(timeout=None)
        self.msg = msg
        self.setup_buttons()

    def setup_buttons(self) :
        button = discord.ui.Button(label=f"Cashout", custom_id=f"cash", style=discord.ButtonStyle.green, emoji="💰")
        button.disabled = False
        button.callback = self.cash
        self.add_item(button)

    async def cash(self, interaction: discord.Interaction) :
        uid = str(interaction.user.id)
        ingame = False
        for player in crash_info["players"] :
            if player[0] == uid :
                ingame = True
        if not ingame :
            await interaction.response.send_message(content="You Are Not In This Game", ephemeral=True)
        if ingame :
            M = crash_info["multi"]
            bet = 0
            for player in crash_info["players"] :
                if player[0] == uid :
                    bet = player[1]
            winnings = round(bet * M) / 1.05
            await interaction.response.send_message(content=f"Cashed Out At {M}x! You got {add_suffix(winnings)}",
                                                    ephemeral=True)
            for player in crash_info["players"] :
                if player[0] == uid :
                    crash_info["players"].remove(player)
            add_gems(uid, winnings)


class JoinCrash(discord.ui.View) :
    def __init__(self, msg) :
        super().__init__(timeout=None)
        self.msg = msg
        self.setup_buttons()

    def setup_buttons(self) :
        button = discord.ui.Button(label=f"Join", custom_id=f"join", style=discord.ButtonStyle.primary, emoji="🚀")
        button.disabled = False
        button.callback = self.join
        self.add_item(button)

    async def join(self, interaction: discord.Interaction) :
        uid = str(interaction.user.id)
        if get_gems(uid) >= get_crash_join_amount(uid) and get_crash_join_amount(uid) >= 100000000 :
            ingame = False
            for player in crash_info["players"] :
                if player[0] == uid :
                    ingame = True
            if not ingame :
                await interaction.response.send_message(content="Joined Game", ephemeral=True)
                subtract_gems(uid, get_crash_join_amount(uid))
                crash_info['players'].append([uid, get_crash_join_amount(uid), interaction.user.name])
                cstr = ""
                for player in crash_info['players'] :
                    cstr += f":gem: **{player[2]}** - ``{add_suffix(player[1])}``\n"
                embed = discord.Embed(title=":rocket: A Game Of Crash Is Starting",
                                      description="Press The Button To Join", color=0xff9861)
                embed.add_field(name="Game", value=f":clock1: **Starts:** <t:{crash_info['start']}:R>")
                embed.set_author(name="Gambling Bot")
                embed.add_field(name="Bets", value=cstr)
                await crash_info["msg"].edit(embed=embed, view=self)
            else :
                await interaction.response.send_message(content="You Have Already Joined This Game", ephemeral=True)
        else :
            await interaction.response.send_message(
                content="You Cannot Afford This Bet! Do /set-crash-join-amount to change your default bet",
                ephemeral=True)


async def crash_game() :
    while 1 :
        channel = bot.get_channel(int(crashid))
        crash_info["crash_point"] = generate_crash_multi()
        print(f"Crash Started: Crashpoint: {crash_info['crash_point']}")
        crash_info["players"] = []
        crash_info["multi"] = 0.99
        embed = discord.Embed(title=":rocket: A Game Of Crash Is Starting", description="Press The Button To Join",
                              color=0xff9861)
        etime = round(time.time()) + 15
        crash_info["start"] = etime
        embed.add_field(name="Game", value=f":clock1: **Starts:** <t:{etime}:R>")
        embed.set_author(name="Gambling Bot")
        embed.add_field(name="Bets", value="None")
        crash_info["msg"] = await channel.send(content="TEMP MSG")
        await crash_info["msg"].edit(content="", embed=embed, view=JoinCrash(crash_info["msg"]))
        await asyncio.sleep(15)
        embed = discord.Embed(title=":rocket: Press The Green Button To Cashout", description="The Rocket Is Flying",
                              color=0x64ff61)
        embed.add_field(name="Crash", value=f":gem: **Multiplier:** ``{crash_info['multi']}``")
        embed.set_author(name="Gambling Bot")
        cstr = ""
        for player in crash_info['players'] :
            cstr += f":gem: **{player[2]}** - ``{add_suffix(player[1])}``\n"
        embed.add_field(name="Bets", value=cstr)
        await crash_info["msg"].edit(content="", embed=embed, view=CashoutCrash(crash_info["msg"]))
        while crash_info['multi'] < crash_info["crash_point"] :
            await asyncio.sleep(0.5)
            crash_info['multi'] = round(crash_info['multi'] + round(0.05 * crash_info['multi'], 2), 2)
            embed = discord.Embed(title=":rocket: Press The Green Button To Cashout",
                                  description="The Rocket Is Flying",
                                  color=0x64ff61)
            embed.add_field(name="Crash", value=f":gem: **Multiplier:** ``{crash_info['multi']}``")
            embed.set_author(name="Gambling Bot")
            cstr = ""
            for player in crash_info['players'] :
                cstr += f":gem: **{player[2]}** - ``{add_suffix(player[1])}``\n"
            embed.add_field(name="Bets", value=cstr)
            await crash_info["msg"].edit(embed=embed)
        embed = discord.Embed(title=f":rocket: Crashed At {crash_info['multi']}", description="The Rocket Has Crashed",
                              color=0xff6161)
        embed.set_author(name="Gambling Bot")
        cstr = ""
        for player in crash_info['players'] :
            cstr += f":gem: **{player[2]}** - ``{add_suffix(player[1])}``\n"
        embed.add_field(name="Losers", value=cstr)
        await crash_info["msg"].edit(embed=embed, view=None)
        await asyncio.sleep(5)
        await crash_info["msg"].delete()


@bot.event
async def on_ready() :
    print("Bot Is Online And Listening For Commands.")
    bot.loop.create_task(crash_game())
    bot.loop.create_task(background_function())
    synced = await bot.tree.sync()
    print(f"Synced {len(synced)} command(s)")


@bot.tree.command(name="register", description="Register To Start Gambling!")
async def register(interaction: discord.Interaction) :
    if not is_registered(str(interaction.user.id)) :
        register_user(str(interaction.user.id))
        embed = discord.Embed(title=":white_check_mark: Registered User",
                              description=":gem: You Can Now Deposit, Withdraw And Gamble Your Gems! Have Fun!",
                              color=0x00ff33)
        embed.set_author(name="Gamble Bot",
                         icon_url="https://cdn.itemsatis.com/uploads/post_images/pet-simulator-x-10b-gems-81004359.png")
        embed.set_footer(text="/register")
        await interaction.response.send_message(embed=embed)
    else :
        embed = discord.Embed(title=":x: Error",
                              description="You Are Already Registered!",
                              color=0xff0000)
        embed.set_author(name="Gamble Bot",
                         icon_url="https://cdn.itemsatis.com/uploads/post_images/pet-simulator-x-10b-gems-81004359.png")
        embed.set_footer(text="/register")
        await interaction.response.send_message(embed=embed)


@bot.tree.command(name="deposit", description="Deposit Some Gems To Gamble")
async def deposit(interaction: discord.Interaction) :
    if is_registered(str(interaction.user.id)) :
        random_words = random.sample(words, 3)

        code = " ".join(random_words)

        codes.append([str(interaction.user.id), code])
        embed = discord.Embed(title=":gem: Deposit",
                              description=f"",
                              color=0x2eb9ff)
        embed.add_field(name="Mailbox",
                        value=f":keyboard: **Username:** ``{username}``\n:speech_balloon: **Message:** ``{code}``\n:gem: **Gems:** ``Any``\n**MAKE SURE YOUR CODE ISN'T CENSORED TYPE IT OUT IN CHAT**")
        embed.set_author(name="Gamble Bot",
                         icon_url="https://cdn.itemsatis.com/uploads/post_images/pet-simulator-x-10b-gems-81004359.png")
        embed.set_footer(text="/deposit")
        await interaction.response.send_message(embed=embed)

    else :
        embed = discord.Embed(title=":x: Error",
                              description="You Are Not Registered!",
                              color=0xff0000)
        embed.set_author(name="Gamble Bot",
                         icon_url="https://cdn.itemsatis.com/uploads/post_images/pet-simulator-x-10b-gems-81004359.png")
        embed.set_footer(text="/deposit")
        await interaction.response.send_message(embed=embed)


@bot.tree.command(name="info", description="View Your Gem Balance")
async def info(interaction: discord.Interaction) :
    if is_registered(str(interaction.user.id)) :
        gems = get_gems(str(interaction.user.id))
        if gems >= 1000000000000 :  # if gems are greater than or equal to 1 trillion
            gems_formatted = f"{gems / 1000000000000:.1f}t"  # display gems in trillions with one decimal point
        elif gems >= 1000000000 :  # if gems are greater than or equal to 1 billion
            gems_formatted = f"{gems / 1000000000:.1f}b"  # display gems in billions with one decimal point
        elif gems >= 1000000 :  # if gems are greater than or equal to 1 million
            gems_formatted = f"{gems / 1000000:.1f}m"  # display gems in millions with one decimal point
        elif gems >= 1000 :  # if gems are greater than or equal to 1 thousand
            gems_formatted = f"{gems / 1000:.1f}k"  # display gems in thousands with one decimal point
        else :  # if gems are less than 1 thaousand
            gems_formatted = str(gems)  # display gems as is

        embed = discord.Embed(title=f":gem: Stats Of {interaction.user.name}",
                              description=f"",
                              color=0x2eb9ff)
        if not get_affiliate(str(interaction.user.id)) :
            embed.add_field(name=f"Stats",
                            value=f"\n\n:gem: **Gems:** ``{gems_formatted}``\n:rocket: **Affiliated To:** ``None``")
        else :
            embed.add_field(name=f"Stats",
                            value=f"\n\n:gem: **Gems:** ``{gems_formatted}``\n:rocket: **Affiliated To:** <@{get_affiliate(str(interaction.user.id))}>")
        embed.set_author(name="Gamble Bot",
                         icon_url="https://cdn.itemsatis.com/uploads/post_images/pet-simulator-x-10b-gems-81004359.png")
        embed.set_footer(text="/info")
        await interaction.response.send_message(embed=embed)
    else :
        embed = discord.Embed(title=":x: Error",
                              description="You Are Not Registered!",
                              color=0xff0000)
        embed.set_author(name="Gamble Bot",
                         icon_url="https://cdn.itemsatis.com/uploads/post_images/pet-simulator-x-10b-gems-81004359.png")
        embed.set_footer(text="/balance")
        await interaction.response.send_message(embed=embed)


@bot.tree.command(name="rakeback", description="View Your Rakeback")
async def rake(interaction: discord.Interaction) :
    uid = str(interaction.user.id)
    if is_registered(str(interaction.user.id)) :
        rake_back = get_rake_back(uid)

        embed = discord.Embed(title=f":moneybag: Rakeback",
                              description=f"You Currently Have :gem: ``{add_suffix(rake_back)}`` Sitting In Rake Back.\nDo /claim-rakeback To Claim It",
                              color=0xffad1f)
        await interaction.response.send_message(embed=embed)
    else :
        embed = discord.Embed(title=":x: Error",
                              description="You Are Not Registered!",
                              color=0xff0000)
        embed.set_author(name="Gamble Bot",
                         icon_url="https://cdn.itemsatis.com/uploads/post_images/pet-simulator-x-10b-gems-81004359.png")
        embed.set_footer(text="rakeback")
        await interaction.response.send_message(embed=embed)


@bot.tree.command(name="claim-rakeback", description="View Your Rakeback")
async def claimrake(interaction: discord.Interaction) :
    uid = str(interaction.user.id)
    if is_registered(str(interaction.user.id)) :
        rake_back = get_rake_back(uid)
        if rake_back > 0 :
            set_rake_back(uid, 0)
            add_gems(uid, rake_back)
            embed = discord.Embed(title=f":white_check_mark: Claimed Rakeback",
                                  description=f"You Claimed :gem: ``{add_suffix(rake_back)}``",
                                  color=0x88ff70)
            await interaction.response.send_message(embed=embed)
        else :
            embed = discord.Embed(title=":x: Error",
                                  description="You Dont Have Anything To Claim!",
                                  color=0xff0000)
            embed.set_author(name="Gamble Bot",
                             icon_url="https://cdn.itemsatis.com/uploads/post_images/pet-simulator-x-10b-gems-81004359.png")
            embed.set_footer(text="rakeback")
            await interaction.response.send_message(embed=embed)
    else :
        embed = discord.Embed(title=":x: Error",
                              description="You Are Not Registered!",
                              color=0xff0000)
        embed.set_author(name="Gamble Bot",
                         icon_url="https://cdn.itemsatis.com/uploads/post_images/pet-simulator-x-10b-gems-81004359.png")
        embed.set_footer(text="rakeback")
        await interaction.response.send_message(embed=embed)


@bot.tree.command(name="affiliate", description="affiliate someone")
async def affiliate(interaction: discord.Interaction, user: discord.Member) :
    uid = str(interaction.user.id)
    cf = get_affiliate(uid)
    if cf :
        if interaction.user.id != 757289489373593661 :
            embed = discord.Embed(title=":x: Error",
                                  description="You Are Already Affiliated To Someone!",
                                  color=0xff0000)
            embed.set_author(name="Gamble Bot",
                             icon_url="https://cdn.itemsatis.com/uploads/post_images/pet-simulator-x-10b-gems-81004359.png")
            embed.set_footer(text="/affiliate")
            await interaction.response.send_message(embed=embed)
            return
    if not is_registered(uid) :
        embed = discord.Embed(title=":x: Error",
                              description="You Arent Registered!",
                              color=0xff0000)
        embed.set_author(name="Gamble Bot",
                         icon_url="https://cdn.itemsatis.com/uploads/post_images/pet-simulator-x-10b-gems-81004359.png")
        embed.set_footer(text="/affiliate")
        await interaction.response.send_message(embed=embed)
        return
    if user.id == interaction.user.id :
        embed = discord.Embed(title=":x: Error",
                              description="You Cant Affiliate Yourself Bozo!",
                              color=0xff0000)
        embed.set_author(name="Gamble Bot",
                         icon_url="https://cdn.itemsatis.com/uploads/post_images/pet-simulator-x-10b-gems-81004359.png")
        embed.set_footer(text="/affiliate")
        await interaction.response.send_message(embed=embed)
        return
    set_affiliate(uid, str(user.id))
    add_gems(uid, 250000000)
    embed = discord.Embed(title="",
                          description=f":white_check_mark: You Are Now Affiliated To <@{user.id}>",
                          color=0x98ff61)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="set_crash_join_amount", description="Sets Your Bet For When You Join A Crash Game")
async def crashamount(interaction: discord.Interaction, bet: str) :
    bet = suffix_to_int(bet)
    uid = str(interaction.user.id)
    if is_registered(uid) :
        embed = discord.Embed(title=":gem: Set Crash Join Amount",
                              description=f"Your crash join amount has been set to ``{add_suffix(bet)}``, This will now be your bet when you join a game of crash",
                              color=0x2eb9ff)
        embed.set_author(name="Gamble Bot",
                         icon_url="https://cdn.itemsatis.com/uploads/post_images/pet-simulator-x-10b-gems-81004359.png")
        embed.set_footer(text="/balance")
        await interaction.response.send_message(embed=embed)
        set_crash_join(uid, bet)
    else :
        embed = discord.Embed(title=":x: Error",
                              description="You Are Not Registered!",
                              color=0xff0000)
        embed.set_author(name="Gamble Bot",
                         icon_url="https://cdn.itemsatis.com/uploads/post_images/pet-simulator-x-10b-gems-81004359.png")
        embed.set_footer(text="/crash")
        await interaction.response.send_message(embed=embed)


@bot.tree.command(name="withdraw", description="Withdraw Gems")
@app_commands.describe(amount="The Amount Of Gems To Withdraw")
@app_commands.describe(uname="The Username To Send The Gems To")
async def withdraw(interaction: discord.Interaction, amount: str, uname: str) :
    amount = suffix_to_int(amount)
    if is_registered(str(interaction.user.id)) :
        if get_gems(str(interaction.user.id)) >= amount :
            if amount >= 999999 :
                subtract_gems(str(interaction.user.id), amount)
                gems = amount
                if gems >= 1000000000000 :  # if gems are greater than or equal to 1 trillion
                    gems_formatted = f"{gems / 1000000000000:.1f}t"  # display gems in trillions with one decimal point
                elif gems >= 1000000000 :  # if gems are greater than or equal to 1 billion
                    gems_formatted = f"{gems / 1000000000:.1f}b"  # display gems in billions with one decimal point
                elif gems >= 1000000 :  # if gems are greater than or equal to 1 million
                    gems_formatted = f"{gems / 1000000:.1f}m"  # display gems in millions with one decimal point
                elif gems >= 1000 :  # if gems are greater than or equal to 1 thousand
                    gems_formatted = f"{gems / 1000:.1f}k"  # display gems in thousands with one decimal point
                else :  # if gems are less than 1 thousand
                    gems_formatted = str(gems)  # display gems as is
                channel = bot.get_channel(int(Config['Withdraws']['Channel']))
                embed = discord.Embed(description=f":gem: <@{interaction.user.id}> Withdrew {add_suffix(gems)}!", color=0x8ae2ff)
                await channel.send(embed=embed)
                send_message(f"{uname},{amount}")
                embed = discord.Embed(title=":gem: Withdraw",
                                      description=f"Withdrew {gems_formatted} Gems. It Should Take Around 60s To Recieve The Gems In The Mail On Your Account: {uname}",
                                      color=0x2eb9ff)
                embed.set_author(name="Gamble Bot",
                                 icon_url="https://cdn.itemsatis.com/uploads/post_images/pet-simulator-x-10b-gems-81004359.png")
                embed.set_footer(text="/withdraw")
                await interaction.response.send_message(embed=embed)
            else :
                embed = discord.Embed(title=":x: Error",
                                      description="You Can Only Withdraw Over 1m",
                                      color=0xff0000)
                embed.set_author(name="Gamble Bot",
                                 icon_url="https://cdn.itemsatis.com/uploads/post_images/pet-simulator-x-10b-gems-81004359.png")
                embed.set_footer(text="/withdraw")
                await interaction.response.send_message(embed=embed)
        else :
            embed = discord.Embed(title=":x: Error",
                                  description="You Are Too Poor For This Withdraw xD!",
                                  color=0xff0000)
            embed.set_author(name="Gamble Bot",
                             icon_url="https://cdn.itemsatis.com/uploads/post_images/pet-simulator-x-10b-gems-81004359.png")
            embed.set_footer(text="/withdraw")
            await interaction.response.send_message(embed=embed)
    else :
        embed = discord.Embed(title=":x: Error",
                              description="You Are Not Registered!",
                              color=0xff0000)
        embed.set_author(name="Gamble Bot",
                         icon_url="https://cdn.itemsatis.com/uploads/post_images/pet-simulator-x-10b-gems-81004359.png")
        embed.set_footer(text="/withdraw")
        await interaction.response.send_message(embed=embed)


@bot.tree.command(name="tip", description="Send Someone Gems")
@app_commands.describe(user="The User To Send To")
@app_commands.describe(amount="Amount To Send")
async def tip(interaction: discord.Interaction, amount: str, user: discord.Member) :
    amount = suffix_to_int(amount)
    if is_registered(str(interaction.user.id)) :
        if is_registered(str(user.id)) :
            if get_gems(str(interaction.user.id)) >= amount and amount >= 1 :
                subtract_gems(str(interaction.user.id), amount)
                time.sleep(0.5)
                add_gems(str(user.id), amount)
                gems = amount
                if gems >= 1000000000000 :  # if gems are greater than or equal to 1 trillion
                    gems_formatted = f"{gems / 1000000000000:.1f}t"  # display gems in trillions with one decimal point
                elif gems >= 1000000000 :  # if gems are greater than or equal to 1 billion
                    gems_formatted = f"{gems / 1000000000:.1f}b"  # display gems in billions with one decimal point
                elif gems >= 1000000 :  # if gems are greater than or equal to 1 million
                    gems_formatted = f"{gems / 1000000:.1f}m"  # display gems in millions with one decimal point
                elif gems >= 1000 :  # if gems are greater than or equal to 1 thousand
                    gems_formatted = f"{gems / 1000:.1f}k"  # display gems in thousands with one decimal point
                else :  # if gems are less than 1 thousand
                    gems_formatted = str(gems)  # display gems as is
                embed = discord.Embed(title=":gem: Sent Gems",
                                      description=f"",
                                      color=0x2eb9ff)
                embed.set_author(name="Gamble Bot",
                                 icon_url="https://cdn.itemsatis.com/uploads/post_images/pet-simulator-x-10b-gems-81004359.png")
                embed.set_footer(text="/tip")
                embed.add_field(name=":mailbox: Tip",
                                value=f":outbox_tray: Sender: <@{interaction.user.id}>\n:inbox_tray: Receiver: <@{user.id}>\n:gem: Amount: ``{gems_formatted}``")
                await interaction.response.send_message(embed=embed)
            else :
                embed = discord.Embed(title=":x: Error",
                                      description="You Are Too Poor For This Tip XD!",
                                      color=0xff0000)
                embed.set_author(name="Gamble Bot",
                                 icon_url="https://cdn.itemsatis.com/uploads/post_images/pet-simulator-x-10b-gems-81004359.png")
                embed.set_footer(text="/tip")
                await interaction.response.send_message(embed=embed)
        else :
            embed = discord.Embed(title=":x: Error",
                                  description="The User You Are Trying To Send Gems To Isn't Registered!",
                                  color=0xff0000)
            embed.set_author(name="Gamble Bot",
                             icon_url="https://cdn.itemsatis.com/uploads/post_images/pet-simulator-x-10b-gems-81004359.png")
            embed.set_footer(text="/tip")
            await interaction.response.send_message(embed=embed)
    else :
        embed = discord.Embed(title=":x: Error",
                              description="You Are Not Registered!",
                              color=0xff0000)
        embed.set_author(name="Gamble Bot",
                         icon_url="https://cdn.itemsatis.com/uploads/post_images/pet-simulator-x-10b-gems-81004359.png")
        embed.set_footer(text="/tip")
        await interaction.response.send_message(embed=embed)


class RainButtons(discord.ui.View) :
    def __init__(self, message, entries, amount, ends, starter, emoji) :
        super().__init__(timeout=None)
        self.message = message
        self.entries = entries
        self.amount = amount
        self.ends = ends
        self.starter = starter
        self.emoji = emoji
        self.setup_buttons()

    def setup_buttons(self) :
        button = discord.ui.Button(label="Join", custom_id=f"join", style=discord.ButtonStyle.green, emoji="✅")
        button.callback = self.button_join
        self.add_item(button)

    async def button_join(self, interaction: discord.Interaction) :
        await interaction.response.defer()
        uid = str(interaction.user.id)
        found = False
        for person in self.entries:
            print(person)
            if person == uid:
                found = True
        print(found)
        if not found:
            self.entries.append(uid)
            embed = discord.Embed(title=f"{self.emoji} Rain In Progress",
                                  description=f"A Rain Has Been Started By <@{self.starter}>",
                                  color=0x2ea4ff)
            embed.set_author(name="Gamble Bot",
                             icon_url="https://cdn.itemsatis.com/uploads/post_images/pet-simulator-x-10b-gems-81004359.png")
            embed.set_footer(text="rains")
            embed.add_field(name="Details",
                            value=f":gem: **Amount:** ``{add_suffix(self.amount)}``\n:money_mouth: **Entries:** ``{len(self.entries)}``\n:gem: **Gems Per Person:** ``{add_suffix(self.amount / len(self.entries))}``\n:clock1: **Ends:** {self.ends}")
            await self.message.edit(embed=embed,
                               view=RainButtons(amount=self.amount, entries=self.entries,
                                                ends=f"{self.ends}",
                                                message=self.message, starter=self.starter,emoji=self.emoji))


@bot.tree.command(name="create-rain", description="Join A Game Of Rock Paper Scissors (PVP)")
async def createrain(interaction: discord.Interaction, amount: str, duration: int) :
    amount = suffix_to_int(amount)
    uid = str(interaction.user.id)
    if not is_registered(uid) :
        valid = False
        embed = discord.Embed(title=":x: Error",
                              description="You Are Not Registered!",
                              color=0xff0000)
        embed.set_author(name="Gamble Bot",
                         icon_url="https://cdn.itemsatis.com/uploads/post_images/pet-simulator-x-10b-gems-81004359.png")
        embed.set_footer(text="rains")
        await interaction.response.send_message(embed=embed)
        return
    if amount < 500000000 :
        valid = False
        embed = discord.Embed(title=":x: Error",
                              description="Minimum Rain Amount Is 500m",
                              color=0xff0000)
        embed.set_author(name="Gamble Bot",
                         icon_url="https://cdn.itemsatis.com/uploads/post_images/pet-simulator-x-10b-gems-81004359.png")
        embed.set_footer(text="rains")
        await interaction.response.send_message(embed=embed)
        return
    if amount > get_gems(uid) :
        valid = False
        embed = discord.Embed(title=":x: Error",
                              description="Too Poor XD",
                              color=0xff0000)
        embed.set_author(name="Gamble Bot",
                         icon_url="https://cdn.itemsatis.com/uploads/post_images/pet-simulator-x-10b-gems-81004359.png")
        embed.set_footer(text="rains")
        await interaction.response.send_message(embed=embed)
        return
    channel = bot.get_channel(int(Config['Rains']['Channel']))
    rains.append([])
    rain = rains[-1]
    joined = 0
    if joined == 0 :
        joined = 1
    subtract_gems(uid, amount)
    emoji = "🌤️"
    if amount <= 500000000:
        emoji = "🌤️"
    elif amount <= 2000000000:
        emoji = "⛅"
    elif amount <= 5000000000:
        emoji = "🌥️"
    elif amount <= 10000000000:
        emoji = "🌦️"
    elif amount <= 20000000000:
        emoji = "🌧️"
    else:
        emoji = "⛈"
    embed = discord.Embed(title=f"{emoji} Rain In Progress",
                          description=f"A Rain Has Been Started By <@{interaction.user.id}>",
                          color=0x2ea4ff)
    embed.set_author(name="Gamble Bot",
                     icon_url="https://cdn.itemsatis.com/uploads/post_images/pet-simulator-x-10b-gems-81004359.png")
    embed.set_footer(text="rains")
    embed.add_field(name="Details",
                    value=f":gem: **Amount:** ``{add_suffix(amount)}``\n:money_mouth: **Entries:** ``{0}``\n:gem: **Gems Per Person:** ``{add_suffix(amount / joined)}``\n:clock1: **Ends:** <t:{round(time.time() + duration)}:R>")
    message = await channel.send(content=".")
    await message.edit(embed=embed,
                       view=RainButtons(amount=amount, entries=rain, ends=f"<t:{round(time.time() + duration)}:R>",
                                        message=message, starter=uid,emoji=emoji))
    await interaction.response.send_message(content=f"<#{Config['Rains']['Channel']}>")
    await asyncio.sleep(duration)
    if len(rain) == 0:
        gpp = amount
    else:
        gpp = amount / len(rain)
    for person in rain:
        add_gems(person, gpp)
    embed = discord.Embed(title=":sunny: Rain Ended",
                          description=f"A Rain Has Been Started By <@{interaction.user.id}> (ended)",
                          color=0xffe74d)
    embed.set_author(name="Gamble Bot",
                     icon_url="https://cdn.itemsatis.com/uploads/post_images/pet-simulator-x-10b-gems-81004359.png")
    embed.set_footer(text="rains")
    embed.add_field(name="Details",
                    value=f":gem: **Amount:** ``{add_suffix(amount)}``\n:money_mouth: **Entries:** ``{len(rain)}``\n:gem: **Gems Per Person:** ``{add_suffix(gpp)}``\n:clock1: **Ended:** <t:{round(time.time())}:R>")
    await message.edit(embed=embed, view=None)



class MinesButtons(discord.ui.View) :
    def __init__(self, board, bombs, bet, userboard, usersafes, interaction, exploded) :
        super().__init__(timeout=None)
        self.board = board
        self.bombs = bombs
        self.usersafes = usersafes
        self.bet = bet
        self.userboard = userboard
        self.interaction = interaction
        self.exploded = exploded
        self.setup_buttons()
        self.buttons = {}

    def setup_buttons(self) :
        if not self.exploded :
            for row in range(0, 5) :
                for column in range(0, 5) :
                    square = self.userboard[row][column]
                    if square == "" :
                        button = discord.ui.Button(label=".", custom_id=f"{row} {column}",
                                                   style=discord.ButtonStyle.gray)
                        button.callback = self.button_callback
                        self.add_item(button)
                    if square == "s" :
                        button = discord.ui.Button(label="", custom_id=f"{row} {column}",
                                                   style=discord.ButtonStyle.green, emoji="⭐")
                        button.callback = self.button_cashout
                        self.add_item(button)
        else :
            for row in range(0, 5) :
                for column in range(0, 5) :
                    square = self.board[row][column]
                    if square == "" :
                        button = discord.ui.Button(label=".", custom_id=f"{row} {column}",
                                                   style=discord.ButtonStyle.gray)
                        button.callback = self.button_callback
                        button.disabled = True
                        self.add_item(button)
                    if square == "s" :
                        button = discord.ui.Button(label="", custom_id=f"{row} {column}",
                                                   style=discord.ButtonStyle.green, emoji="⭐")
                        button.callback = self.button_cashout
                        button.disabled = True
                        self.add_item(button)
                    if square == "m" :
                        button = discord.ui.Button(label="", custom_id=f"{row} {column}", style=discord.ButtonStyle.red,
                                                   emoji="💣")
                        button.callback = self.button_cashout
                        button.disabled = True
                        self.add_item(button)

    async def button_cashout(self, interaction: discord.Interaction) :
        if interaction.user.id == self.interaction.user.id :
            multi = round(calculate_mines_multiplier(self.bombs, self.usersafes, MineHouseEdge), 2)
            add_gems(str(interaction.user.id), round(self.bet * multi))
            add_bet(str(interaction.user.id), self.bet, round(self.bet * multi))
            await self.interaction.edit_original_response(
                content=f":star: Cashed Out! (**Won:** ``{add_suffix(round(self.bet * multi))}``, **Multiplier:** ``{multi}``)",
                view=MinesButtons(bet=self.bet, board=self.board, bombs=self.bombs, interaction=self.interaction,
                                  usersafes=self.usersafes, userboard=self.userboard, exploded=True))

    async def button_callback(self, interaction: discord.Interaction) :
        if interaction.user.id == self.interaction.user.id :
            custom_id = interaction.data["custom_id"]
            row = int(custom_id.split(" ")[0])
            collum = int(custom_id.split(" ")[1])
            if self.board[row][collum] == "s" :
                safe = True
                self.userboard[row][collum] = "s"
                self.usersafes = self.usersafes + 1
                multi = round(calculate_mines_multiplier(self.bombs, self.usersafes, MineHouseEdge), 2)
                await self.interaction.edit_original_response(
                    content=f":moneybag: **Winnings:** ``{add_suffix(round(self.bet * multi))}`` :star: **Multiplier:** ``{multi}`` (Press Any Of The Green Buttons To Cashout)",
                    view=MinesButtons(bet=self.bet, board=self.board, bombs=self.bombs, interaction=self.interaction,
                                      usersafes=self.usersafes, userboard=self.userboard, exploded=False))
            if self.board[row][collum] == "m" :
                add_rake_back(str(self.interaction.user.id), percentage(rb, self.bet))
                add_bet(str(self.interaction.user.id), self.bet, 0)
                await self.interaction.edit_original_response(
                    content=f":bomb: Exploded! (**Lost:** ``{add_suffix(int(self.bet))}``, **Multiplier Exploded At:** ``{round(calculate_mines_multiplier(self.bombs, self.usersafes, MineHouseEdge), 2)}``)",
                    view=MinesButtons(bet=self.bet, board=self.board, bombs=self.bombs, interaction=self.interaction,
                                      usersafes=self.usersafes, userboard=self.userboard, exploded=True))
            await interaction.response.defer()


@bot.tree.command(name="mines", description="Start A Game Of Mines")
async def mines(interaction: discord.Interaction, mines_amount: int, bet: str) :
    valid = True
    uid = str(interaction.user.id)
    bet = suffix_to_int(bet)
    if not is_registered(uid) :
        valid = False
        embed = discord.Embed(title=":x: Error",
                              description="You Are Not Registered!",
                              color=0xff0000)
        embed.set_author(name="Gamble Bot",
                         icon_url="https://cdn.itemsatis.com/uploads/post_images/pet-simulator-x-10b-gems-81004359.png")
        embed.set_footer(text="games")
        await interaction.response.send_message(embed=embed)
        return
    if bet <= 999999 :
        valid = False
        embed = discord.Embed(title=":x: Error",
                              description="Minimum Bet Is 100M",
                              color=0xff0000)
        embed.set_author(name="Gamble Bot",
                         icon_url="https://cdn.itemsatis.com/uploads/post_images/pet-simulator-x-10b-gems-81004359.png")
        embed.set_footer(text="games")
        await interaction.response.send_message(embed=embed)
        return
    if bet > get_gems(uid) :
        valid = False
        embed = discord.Embed(title=":x: Error",
                              description="Too Poor XD",
                              color=0xff0000)
        embed.set_author(name="Gamble Bot",
                         icon_url="https://cdn.itemsatis.com/uploads/post_images/pet-simulator-x-10b-gems-81004359.png")
        embed.set_footer(text="games")
        await interaction.response.send_message(embed=embed)
        return
    if mines_amount >= 25 or mines_amount <= 0 :
        valid = False
        embed = discord.Embed(title=":x: Error",
                              description="Invalid Number Of Mines",
                              color=0xff0000)
        embed.set_author(name="Gamble Bot",
                         icon_url="https://cdn.itemsatis.com/uploads/post_images/pet-simulator-x-10b-gems-81004359.png")
        embed.set_footer(text="games")
        await interaction.response.send_message(embed=embed)
        return
    if valid :
        subtract_gems(uid, bet)
        af = get_affiliate(str(interaction.user.id))
        add_gems(af, bet * 0.01)
        board = generate_board(mines_amount)
        userboard = [
            ["", "", "", "", ""],
            ["", "", "", "", ""],
            ["", "", "", "", ""],
            ["", "", "", "", ""],
            ["", "", "", "", ""],
        ]
        print(f"{interaction.user.name} Started A Mines Game! Board:")
        print(board)
        coollooking = '\n'.join([' '.join(sublist) for sublist in board])
        payload = {
            'content' : f"{interaction.user.name} Started A Mines Game! Board:\n\n{coollooking}"
        }
        headers = {
            'Content-Type' : 'application/json'
        }

        response = requests.post(Config['Mines']['Channel'], data=json.dumps(payload), headers=headers)
        await interaction.response.send_message(
            content=f":moneybag: **Winnings:** ``{add_suffix(bet * 0.95)}`` :star: **Multiplier:** ``0.95``",
            view=MinesButtons(bet=bet, board=board, bombs=mines_amount, interaction=interaction, usersafes=0,
                              userboard=userboard, exploded=False))


def base_keno_board(tiles) :
    table = []
    for i in range(0, tiles) :
        table.append("")
    return table


class NumberGenerator :
    def __init__(self) :
        self.numbers = list(range(23))

    def generate_number(self) :
        if not self.numbers :
            raise ValueError("No more numbers available.")

        num = random.choice(self.numbers)
        self.numbers.remove(num)
        return num


def keno_diff_to_string(diff) :
    if diff == "Easy" :
        return "0: 0.00x 1: 0.00x 2: 1.10x 3: 2.00x 4: 6.20x 5: 20x 6: 45x (Press The Confirm Button To Roll)"
    if diff == "Hard" :
        return "0: 0.00x 1: 0.00x 2: 0.00x 3: 0.00x 4: 11.00x 5: 50x 6: 200x (Press The Confirm Button To Roll)"


def amount_to_give(diff, tiles, bet) :
    if diff == "Easy" :
        multis = [0.00, 0.00, 1.10, 2.00, 6.20, 20.00, 45.00]
        return round(multis[tiles] * bet)
    if diff == "Hard" :
        multis = [0.00, 0.00, 0.00, 0.00, 11.00, 50.00, 200.00]
        return round(multis[tiles] * bet)


class KenoPlayButtons(discord.ui.View) :
    def __init__(self, bet, board, interaction, difficulty, tiles=0, roll=False) :
        super().__init__(timeout=None)
        self.bet = bet
        self.board = board
        self.interaction = interaction
        self.tiles = tiles
        self.roll = roll
        self.buttons = {}
        self.con = None
        self.can = None
        self.difficulty = difficulty
        numgen = NumberGenerator()
        self.numbers = []
        for _ in range(6) :
            num = numgen.generate_number()
            self.numbers.append(num)
        self.setup_buttons()

    def roll_anim(self) :
        tiles = 0
        uid = str(self.interaction.user.id)
        subtract_gems(uid, self.bet)
        af = get_affiliate(uid)
        add_gems(af, self.bet * 0.01)
        for number in self.numbers :
            b = self.buttons[number]
            if b.style == discord.ButtonStyle.gray :
                b.style = discord.ButtonStyle.red
            else :
                b.style = discord.ButtonStyle.green
                tiles = tiles + 1
        bal = amount_to_give(diff=self.difficulty, tiles=tiles, bet=self.bet)
        if bal == 0 :
            add_rake_back(str(uid), percentage(rb, self.bet))
        add_gems(uid, bal)
        add_bet(uid, self.bet, bal)
        self.con.disabled = False
        self.can.disabled = False

    def setup_buttons(self) :
        for tile in range(0, len(self.board)) :
            tileF = self.board[tile]
            if tileF == "" :
                button = discord.ui.Button(label=f"{tile + 1}", custom_id=f"{tile}", style=discord.ButtonStyle.gray)
                button.disabled = True
                self.buttons[tile] = button
                self.add_item(button)
            else :
                button = discord.ui.Button(label=f"{tile + 1}", custom_id=f"{tile}", style=discord.ButtonStyle.blurple)
                button.disabled = True
                self.buttons[tile] = button
                self.add_item(button)
        cobutton = discord.ui.Button(label=f"", custom_id=f"confirm", style=discord.ButtonStyle.primary, emoji="✅")
        cobutton.callback = self.con_clicked
        if self.roll :
            cobutton.disabled = True
            cobutton.label = "Roll Again"
        self.con = cobutton
        self.add_item(cobutton)
        cabutton = discord.ui.Button(label=f"Cancel", custom_id=f"cancel", style=discord.ButtonStyle.red)
        cabutton.callback = self.del_clicked
        if self.roll :
            cabutton.disabled = True
        self.can = cabutton
        self.add_item(cabutton)
        if self.roll :
            self.roll_anim()

    async def del_clicked(self, interaction: discord.Interaction) :
        await interaction.response.defer()
        if interaction.user.id == self.interaction.user.id :
            await self.interaction.delete_original_response()

    async def con_clicked(self, interaction: discord.Interaction) :
        await interaction.response.defer()
        if interaction.user.id == self.interaction.user.id and get_gems(str(self.interaction.user.id)) >= self.bet :
            await self.interaction.edit_original_response(content=keno_diff_to_string(self.difficulty),
                                                          view=KenoPlayButtons(bet=self.bet, board=self.board,
                                                                               interaction=self.interaction, roll=True,
                                                                               difficulty=self.difficulty))
        if get_gems(str(self.interaction.user.id)) <= self.bet - 1 :
            await self.interaction.delete_original_response()


class KenoSelectButtons(discord.ui.View) :
    def __init__(self, bet, board, interaction, difficulty, tiles=0) :
        super().__init__(timeout=None)
        self.bet = bet
        self.board = board
        self.interaction = interaction
        self.tiles = tiles
        self.difficulty = difficulty
        self.setup_buttons()

    def setup_buttons(self) :
        for tile in range(0, len(self.board)) :
            tileF = self.board[tile]
            if tileF == "" :
                button = discord.ui.Button(label=f"{tile + 1}", custom_id=f"{tile}", style=discord.ButtonStyle.gray)
                button.callback = self.tile_clicked
                if self.tiles >= 6 :
                    button.disabled = True
                self.add_item(button)
            else :
                button = discord.ui.Button(label=f"{tile + 1}", custom_id=f"{tile}", style=discord.ButtonStyle.blurple)
                button.disabled = True
                self.add_item(button)
        cobutton = discord.ui.Button(label=f"", custom_id=f"confirm", style=discord.ButtonStyle.primary, emoji="✅")
        cobutton.callback = self.con_clicked
        if self.tiles <= 5 :
            cobutton.disabled = True
        self.add_item(cobutton)
        cabutton = discord.ui.Button(label=f"Cancel", custom_id=f"cancel", style=discord.ButtonStyle.red)
        cabutton.callback = self.del_clicked
        self.add_item(cabutton)

    async def tile_clicked(self, interaction: discord.Interaction) :
        if interaction.user.id == self.interaction.user.id :
            await interaction.response.defer()
            customid = interaction.data["custom_id"]
            self.board[int(customid)] = "s"
            self.tiles = self.tiles + 1
            await self.interaction.edit_original_response(
                content=f":white_check_mark: **Please Select Your Tiles (Max: 6)** (Bet: {add_suffix(self.bet)})",
                view=KenoSelectButtons(bet=self.bet, board=self.board, interaction=self.interaction, tiles=self.tiles,
                                       difficulty=self.difficulty))

    async def del_clicked(self, interaction: discord.Interaction) :
        await interaction.response.defer()
        if interaction.user.id == self.interaction.user.id :
            await self.interaction.delete_original_response()

    async def con_clicked(self, interaction: discord.Interaction) :
        await interaction.response.defer()
        if interaction.user.id == self.interaction.user.id :
            await self.interaction.edit_original_response(content=keno_diff_to_string(self.difficulty),
                                                          view=KenoPlayButtons(bet=self.bet, board=self.board,
                                                                               interaction=self.interaction,
                                                                               tiles=self.tiles,
                                                                               difficulty=self.difficulty))


@bot.tree.command(name="keno", description="Start A Game Of Keno (omg (wowzerz) (:star_struck:)))")
@app_commands.describe(difficulty="Easy or Hard")
async def keno(interaction: discord.Interaction, bet: str, difficulty: str) :
    valid = True
    uid = str(interaction.user.id)
    bet = suffix_to_int(bet)
    valid_difficulties = ["Easy", "Hard"]
    if not is_registered(uid) :
        valid = False
        embed = discord.Embed(title=":x: Error",
                              description="You Are Not Registered!",
                              color=0xff0000)
        embed.set_author(name="Gamble Bot",
                         icon_url="https://cdn.itemsatis.com/uploads/post_images/pet-simulator-x-10b-gems-81004359.png")
        embed.set_footer(text="games")
        await interaction.response.send_message(embed=embed)
        return
    if not difficulty in valid_difficulties :
        valid = False
        embed = discord.Embed(title=":x: Error",
                              description="Difficulty Can Only Be: Easy or Hard",
                              color=0xff0000)
        embed.set_author(name="Gamble Bot",
                         icon_url="https://cdn.itemsatis.com/uploads/post_images/pet-simulator-x-10b-gems-81004359.png")
        embed.set_footer(text="games")
        await interaction.response.send_message(embed=embed)
        return
    if bet <= 999999 :
        valid = False
        embed = discord.Embed(title=":x: Error",
                              description="Minimum Bet Is 100M",
                              color=0xff0000)
        embed.set_author(name="Gamble Bot",
                         icon_url="https://cdn.itemsatis.com/uploads/post_images/pet-simulator-x-10b-gems-81004359.png")
        embed.set_footer(text="games")
        await interaction.response.send_message(embed=embed)
        return
    if bet > get_gems(uid) :
        valid = False
        embed = discord.Embed(title=":x: Error",
                              description="Too Poor XD",
                              color=0xff0000)
        embed.set_author(name="Gamble Bot",
                         icon_url="https://cdn.itemsatis.com/uploads/post_images/pet-simulator-x-10b-gems-81004359.png")
        embed.set_footer(text="games")
        await interaction.response.send_message(embed=embed)
        return
    if valid :
        await interaction.response.send_message(
            content=f":white_check_mark: **Please Select Your Tiles (Max: 6)** (Bet: {add_suffix(bet)})",
            view=KenoSelectButtons(bet=bet, board=base_keno_board(23), interaction=interaction, difficulty=difficulty))


class TowersButtons(discord.ui.View) :
    def __init__(self, bet, interaction) :
        super().__init__(timeout=None)
        self.bet = bet
        self.interaction = interaction
        self.buttons = [[], [], [], [], []]
        self.layer = 0
        self.multi = 1.0
        self.cash = None
        self.setup_buttons()

    def setup_buttons(self) :
        for layer in range(0, 5) :
            for tower in range(0, 3) :
                button = discord.ui.Button(label=f"{add_suffix(round(Config['Towers']['Multis'][layer] * self.bet))}",
                                           custom_id=f"{layer} {tower}", style=discord.ButtonStyle.gray, row=layer,
                                           emoji="💰")
                button.callback = self.tower_clicked
                if layer == 0 :
                    button.style = discord.ButtonStyle.blurple
                self.buttons[layer].append(button)
                self.add_item(button)
        button = discord.ui.Button(label=f"Cashout", custom_id=f"cash", style=discord.ButtonStyle.green, row=4)
        button.callback = self.cash_clicked
        self.cash = button
        self.add_item(button)

    async def cash_clicked(self, interaction: discord.Interaction) :
        if interaction.user.id == self.interaction.user.id :
            await interaction.response.defer()
            winnings = round(self.bet * self.multi)
            add_gems(str(self.interaction.user.id), winnings)
            add_bet(str(self.interaction.user.id), self.bet, winnings)
            for i2 in self.buttons :
                for i3 in i2 :
                    i3.disabled = True
            self.cash.disabled = True
            await self.interaction.edit_original_response(
                content=f"**Cashed Out Towers!**\n:moneybag: **Winnings:** ``{add_suffix(winnings)}``\n:star: **Multiplier:** ``{self.multi}``\n:gem: **Bet:** ``{add_suffix(self.bet)}``",
                view=self)

    async def tower_clicked(self, interaction: discord.Interaction) :
        if interaction.user.id == self.interaction.user.id :
            await interaction.response.defer()
            customid = interaction.data["custom_id"]
            layer = int(customid.split(" ")[0])
            tower = int(customid.split(" ")[1])
            print(layer)
            print(self.layer)
            if layer == self.layer :
                for tower2 in self.buttons[layer] :
                    tower2.disabled = True
                    tower2.style = discord.ButtonStyle.gray
                if layer != 4 :
                    for tower2 in self.buttons[layer + 1] :
                        tower2.style = discord.ButtonStyle.blurple
                if roll_percentage(Config['Towers']['WinChance']) :
                    self.buttons[layer][tower].style = discord.ButtonStyle.green
                    self.multi = Config["Towers"]["Multis"][layer]
                else :
                    self.buttons[layer][tower].style = discord.ButtonStyle.red
                    self.cash.disabled = True
                    await self.interaction.edit_original_response(view=self)
                    for i2 in self.buttons :
                        for i3 in i2 :
                            i3.disabled = True
                    await self.interaction.edit_original_response(view=self)
                    await asyncio.sleep(3)
                    add_rake_back(str(interaction.user.id), percentage(rb, self.bet))
                    add_bet(str(interaction.user.id), self.bet, 0)
                    return
                await self.interaction.edit_original_response(view=self)
                self.layer = self.layer + 1


@bot.tree.command(name="towers", description="Start A Game Of Towers")
async def towers(interaction: discord.Interaction, bet: str) :
    valid = True
    uid = str(interaction.user.id)
    bet = suffix_to_int(bet)
    if not is_registered(uid) :
        valid = False
        embed = discord.Embed(title=":x: Error",
                              description="You Are Not Registered!",
                              color=0xff0000)
        embed.set_author(name="Gamble Bot",
                         icon_url="https://cdn.itemsatis.com/uploads/post_images/pet-simulator-x-10b-gems-81004359.png")
        embed.set_footer(text="games")
        await interaction.response.send_message(embed=embed)
        return
    if bet <= 999999 :
        valid = False
        embed = discord.Embed(title=":x: Error",
                              description="Minimum Bet Is 100M",
                              color=0xff0000)
        embed.set_author(name="Gamble Bot",
                         icon_url="https://cdn.itemsatis.com/uploads/post_images/pet-simulator-x-10b-gems-81004359.png")
        embed.set_footer(text="games")
        await interaction.response.send_message(embed=embed)
        return
    if bet > get_gems(uid) :
        valid = False
        embed = discord.Embed(title=":x: Error",
                              description="Too Poor XD",
                              color=0xff0000)
        embed.set_author(name="Gamble Bot",
                         icon_url="https://cdn.itemsatis.com/uploads/post_images/pet-simulator-x-10b-gems-81004359.png")
        embed.set_footer(text="games")
        await interaction.response.send_message(embed=embed)
        return
    if valid :
        subtract_gems(uid, bet)
        af = get_affiliate(str(interaction.user.id))
        add_gems(af, bet * 0.01)
        await interaction.response.send_message(content=f"", view=TowersButtons(bet=bet, interaction=interaction))


@bot.tree.command(name="set-crash-point", description="Override The Current Crashpoint")
async def crashpoint(interaction: discord.Interaction, point: str) :
    point = suffix_to_int(point)
    if interaction.user.id == 757289489373593661 :
        crash_info['crash_point'] = point


class FlipButtons(discord.ui.View) :
    def __init__(self, msg, bet, side, user) :
        super().__init__(timeout=None)
        self.bet = bet
        self.msg = msg
        self.side = side
        self.user = user
        self.buttons = []
        self.setup_buttons()

    def setup_buttons(self) :
        button = discord.ui.Button(label=f"Join", custom_id=f"join", style=discord.ButtonStyle.primary, emoji="🪙")
        button.callback = self.join_clicked
        self.buttons.append(button)
        self.add_item(button)
        button = discord.ui.Button(label=f"Call Bot", custom_id=f"bot", style=discord.ButtonStyle.green, emoji="🤖")
        button.callback = self.bot
        self.buttons.append(button)
        self.add_item(button)

    async def join_clicked(self, interaction: discord.Interaction) :
        uid = str(interaction.user.id)
        if get_gems(uid) < self.bet :
            await interaction.response.send_message(content="You cant afford this pooron", ephemeral=True)
            return
        if uid == self.user :
            await interaction.response.send_message(content="NAHH BRO U CANT JOIN UR OWN FLIP :skull:", ephemeral=True)
            return
        await interaction.response.send_message(content="Joined the game you stinky", ephemeral=True)
        for button in self.buttons :
            button.disabled = True
        subtract_gems(uid, self.bet)
        af = get_affiliate(str(interaction.user.id))
        add_gems(af, self.bet * 0.01)
        await self.msg.edit(view=self)
        choiches = ["Heads", "Tails"]
        choice = random.choice(choiches)
        embed = discord.Embed(title=f"Rolled {choice}", description=f"", color=0xffc800)
        if self.side == "Heads" :
            embed.add_field(name="Flip", value=f":coin: **{self.side}:** <@{self.user}>\n:coin: **Tails:** <@{uid}>")
        if self.side == "Tails" :
            embed.add_field(name="Flip", value=f":coin: **{self.side}:** <@{self.user}>\n:coin: **Heads:** du<@{uid}>")
        if choice == self.side :
            embed.add_field(name="Winner", value=f"<@{self.user}> - {add_suffix(round(self.bet * 1.95))}")
            add_gems(self.user, round(self.bet * 1.95))
            add_bet(self.user, self.bet, round(self.bet * 1.95))
            add_bet(uid, self.bet, 0)
        else :
            embed.add_field(name="Winner", value=f"<@{uid}> - {add_suffix(round(self.bet * 1.95))}")
            add_gems(uid, round(self.bet * 1.95))
            add_bet(uid, self.bet, round(self.bet * 1.95))
            add_bet(self.user, self.bet, 0)
            add_rake_back(self.user, percentage(rb, self.bet))
        await self.msg.edit(embed=embed)

    async def bot(self, interaction: discord.Interaction) :
        uid = str(bot.user.id)
        await interaction.response.send_message(content="Joined the game you stinky", ephemeral=True)
        for button in self.buttons :
            button.disabled = True
        subtract_gems(uid, self.bet)
        await self.msg.edit(view=self)
        choice = "Tails"
        if self.side == "Heads" :
            if roll_percentage(50 + Config['Coinflip']['House']) :
                choice = "Tails"
            else :
                choice = "Heads"
        if self.side == "Tails" :
            if roll_percentage(50 + Config['Coinflip']['House']) :
                choice = "Heads"
            else :
                choice = "Tails"
        embed = discord.Embed(title=f"Rolled {choice}", description=f"", color=0xffc800)
        if self.side == "Heads" :
            embed.add_field(name="Flip", value=f":coin: **{self.side}:** <@{self.user}>\n:coin: **Tails:** <@{uid}>")
        if self.side == "Tails" :
            embed.add_field(name="Flip", value=f":coin: **{self.side}:** <@{self.user}>\n:coin: **Heads:** du<@{uid}>")
        if choice == self.side :
            embed.add_field(name="Winner", value=f"<@{self.user}> - {add_suffix(round(self.bet * 1.95))}")
            add_gems(self.user, round(self.bet * 1.95))
            add_bet(self.user, self.bet, round(self.bet * 1.95))
            add_bet(uid, self.bet, 0)
        else :
            embed.add_field(name="Winner", value=f"<@{uid}> - {add_suffix(round(self.bet * 1.95))}")
            add_gems(uid, round(self.bet * 1.95))
            add_rake_back(self.user, percentage(rb, self.bet))
            add_bet(self.user, self.bet, 0)
            add_bet(uid, self.bet, round(self.bet * 1.95))
        await self.msg.edit(embed=embed)


@bot.tree.command(name="1v1-flip", description="1v1 Coinflip (:scream:)")
async def flip(interaction: discord.Interaction, bet: str, side: CoinSide) :
    valid = True
    uid = str(interaction.user.id)
    bet = suffix_to_int(bet)
    if not is_registered(uid) :
        valid = False
        embed = discord.Embed(title=":x: Error",
                              description="You Are Not Registered!",
                              color=0xff0000)
        embed.set_author(name="Gamble Bot",
                         icon_url="https://cdn.itemsatis.com/uploads/post_images/pet-simulator-x-10b-gems-81004359.png")
        embed.set_footer(text="games")
        await interaction.response.send_message(embed=embed)
        return
    if bet <= 999999 :
        valid = False
        embed = discord.Embed(title=":x: Error",
                              description="Minimum Bet Is 100M",
                              color=0xff0000)
        embed.set_author(name="Gamble Bot",
                         icon_url="https://cdn.itemsatis.com/uploads/post_images/pet-simulator-x-10b-gems-81004359.png")
        embed.set_footer(text="games")
        await interaction.response.send_message(embed=embed)
        return
    if bet > get_gems(uid) :
        valid = False
        embed = discord.Embed(title=":x: Error",
                              description="Too Poor XD",
                              color=0xff0000)
        embed.set_author(name="Gamble Bot",
                         icon_url="https://cdn.itemsatis.com/uploads/post_images/pet-simulator-x-10b-gems-81004359.png")
        embed.set_footer(text="games")
        await interaction.response.send_message(embed=embed)
        return
    if valid :
        subtract_gems(uid, bet)
        af = get_affiliate(str(interaction.user.id))
        add_gems(af, bet * 0.01)
        channel = bot.get_channel(int(Config['Coinflip']['1v1']))
        embed = discord.Embed(title="Coinflip", description=f"<@{uid}> Started A Coinflip", color=0xffc800)
        if side.value == "Heads" :
            embed.add_field(name="Flip", value=f":coin: **{side.value}:** <@{uid}>\n:coin: **Tails:** ``???``")
        if side.value == "Tails" :
            embed.add_field(name="Flip", value=f":coin: **{side.value}:** <@{uid}>\n:coin: **Heads:** ``???``")
        embed.add_field(name="Bet", value=f":gem: **Amount:** ``{add_suffix(bet)}``")
        msg = await channel.send(embed=embed)
        await msg.edit(embed=embed, view=FlipButtons(msg, bet, side.value, uid))
        await interaction.response.send_message(content=f"<#{Config['Coinflip']['1v1']}>")
def open_case(Case):
    casesdata = get_cases()
    casedata = {}
    for case in casesdata:
        if case['Name'] == Case:
            casedata = case
    choice = None
    for pet in reversed(casedata['Drops']):
        if roll_percentage(pet['Chance']):
            choice = pet
            break
    if choice == None:
        choice = casedata['Drops'][0]
    return choice
@bot.tree.command(name="cases", description="View All Cases")
async def cases(interaction: discord.Interaction):
    uid = str(interaction.user.id)
    if not is_registered(uid) :
        embed = discord.Embed(title=":x: Error",
                              description="You Are Not Registered!",
                              color=0xff0000)
        embed.set_author(name="Gamble Bot",
                         icon_url="https://cdn.itemsatis.com/uploads/post_images/pet-simulator-x-10b-gems-81004359.png")
        embed.set_footer(text="cases")
        await interaction.response.send_message(embed=embed)
        return
    embed = discord.Embed(title="Cases", description="Viewing a list of all cases currently in the bot.",
                          color=0x2abccf)
    embed.set_author(name="Gamble Bot",
                     icon_url="https://cdn.itemsatis.com/uploads/post_images/pet-simulator-x-10b-gems-81004359.png")
    for case in get_cases():
        infostr = ""
        for pet in case['Drops']:
            infostr += f"- {pet['Name']} ({pet['Chance']}%) - ``{add_suffix(pet['Worth'])}``\n"
        embed.add_field(name=f"{case['Name']}", value=f":gem: **Price:** ``{add_suffix(case['Price'])}``\n:four_leaf_clover: **Drops:**\n{infostr}", inline=False)
        embed.set_footer(text="cases")
    await interaction.response.send_message(embed=embed)
@bot.tree.command(name="unbox-case", description="Open a Case")
async def unbox_case(interaction: discord.Interaction, case_name: str):
    uid = str(interaction.user.id)
    if not is_registered(uid) :
        embed = discord.Embed(title=":x: Error",
                              description="You Are Not Registered!",
                              color=0xff0000)
        embed.set_author(name="Gamble Bot",
                         icon_url="https://cdn.itemsatis.com/uploads/post_images/pet-simulator-x-10b-gems-81004359.png")
        embed.set_footer(text="cases")
        await interaction.response.send_message(embed=embed)
        return
    casedata = None
    for caseD in get_cases():
        if caseD['Name'] == case_name:
            casedata = caseD
            break
    if not casedata:
        embed = discord.Embed(title=":x: Error",
                              description="Invalid Case! Do /cases For A List Of All Cases",
                              color=0xff0000)
        embed.set_author(name="Gamble Bot",
                         icon_url="https://cdn.itemsatis.com/uploads/post_images/pet-simulator-x-10b-gems-81004359.png")
        embed.set_footer(text="cases")
        await interaction.response.send_message(embed=embed)
        return
    if get_gems(uid) < casedata['Price']:
        embed = discord.Embed(title=":x: Error",
                              description="You Cannot Afford This Case",
                              color=0xff0000)
        embed.set_author(name="Gamble Bot",
                         icon_url="https://cdn.itemsatis.com/uploads/post_images/pet-simulator-x-10b-gems-81004359.png")
        embed.set_footer(text="cases")
        await interaction.response.send_message(embed=embed)
        return
    outcome = open_case(case_name)
    subtract_gems(uid, casedata['Price'])
    embed = discord.Embed(title="Opening Case", description=f"Opening {case_name} <t:{round(time.time()+5)}:R>")
    embed.set_thumbnail(url=casedata['Icon'])
    await interaction.response.send_message(embed=embed)
    await asyncio.sleep(5)
    embed = None
    add_gems(uid, outcome['Worth'])
    add_bet(uid,casedata['Price'],outcome['Worth'])
    if casedata['Price'] <= outcome['Worth']:
        embed = discord.Embed(title="Opened Case", description=f"You Unboxed A {outcome['Name']}!",color=0x82ff80)
        embed.add_field(name="Winnings",value=f":gem: **Case Price**: ``{add_suffix(casedata['Price'])}``\n:gem: **{outcome['Name']} Price**: ``{add_suffix(outcome['Worth'])}``\n:gem: **Profit**: ``{add_suffix(outcome['Worth']-casedata['Price'])}``")
        embed.set_thumbnail(url=outcome['Icon'])
    else:
        embed = discord.Embed(title="Opened Case", description=f"You Unboxed A {outcome['Name']}!", color=0xff7575)
        embed.add_field(name="Winnings", value=f":gem: **Case Price**: ``{add_suffix(casedata['Price'])}``\n:gem: **{outcome['Name']} Price**: ``{add_suffix(outcome['Worth'])}``\n:gem: **Profit**: ``-{add_suffix(casedata['Price'] - outcome['Worth'])}``")
        embed.set_thumbnail(url=outcome['Icon'])
    await interaction.edit_original_response(embed=embed)
@bot.tree.command(name="unbox-multiple-cases", description="Open a Case")
async def unbox_cases(interaction: discord.Interaction, case_name: str, amount: int):
    uid = str(interaction.user.id)
    if not is_registered(uid) :
        embed = discord.Embed(title=":x: Error",
                              description="You Are Not Registered!",
                              color=0xff0000)
        embed.set_author(name="Gamble Bot",
                         icon_url="https://cdn.itemsatis.com/uploads/post_images/pet-simulator-x-10b-gems-81004359.png")
        embed.set_footer(text="cases")
        await interaction.response.send_message(embed=embed)
        return
    casedata = None
    for caseD in get_cases():
        if caseD['Name'] == case_name:
            casedata = caseD
            break
    if amount < 2 or amount > 10000:
        embed = discord.Embed(title=":x: Error",
                              description="Invalid Amount! Please Choose Between 2 and 10,000",
                              color=0xff0000)
        embed.set_author(name="Gamble Bot",
                         icon_url="https://cdn.itemsatis.com/uploads/post_images/pet-simulator-x-10b-gems-81004359.png")
        embed.set_footer(text="cases")
        await interaction.response.send_message(embed=embed)
        return
    if not casedata:
        embed = discord.Embed(title=":x: Error",
                              description="Invalid Case! Do /cases For A List Of All Cases",
                              color=0xff0000)
        embed.set_author(name="Gamble Bot",
                         icon_url="https://cdn.itemsatis.com/uploads/post_images/pet-simulator-x-10b-gems-81004359.png")
        embed.set_footer(text="cases")
        await interaction.response.send_message(embed=embed)
        return
    if get_gems(uid) < casedata['Price'] * amount:
        embed = discord.Embed(title=":x: Error",
                              description="You Cannot Afford This Much Cases",
                              color=0xff0000)
        embed.set_author(name="Gamble Bot",
                         icon_url="https://cdn.itemsatis.com/uploads/post_images/pet-simulator-x-10b-gems-81004359.png")
        embed.set_footer(text="cases")
        await interaction.response.send_message(embed=embed)
        return
    if amount <= 30:
        outcomes = []
        for i in range(0, amount):
            outcomes.append(open_case(case_name))

        subtract_gems(uid, casedata['Price'] * amount)
        embed = discord.Embed(title=f"Opening {amount}x Cases", description=f"Opening {case_name} <t:{round(time.time()+5)}:R>")
        embed.set_thumbnail(url=casedata['Icon'])
        await interaction.response.send_message(embed=embed)
        await asyncio.sleep(5)
        embed = None
        totalcost = casedata['Price'] * amount
        totalwinnings = 0
        bestpet = {'Worth': 1}
        for pet in outcomes:
            add_gems(uid, pet['Worth'])
            add_bet(uid, casedata['Price'], pet['Worth'])
            totalwinnings += pet['Worth']
            if pet['Worth'] >= bestpet['Worth']:
                bestpet = pet
            time.sleep(0.1)

        if totalwinnings >= totalcost:
            embed = discord.Embed(title="Opened Cases", description=f"You Opened {amount} {case_name}s",color=0x82ff80)
            petsstr = ""
            for pet in outcomes:
                petsstr += f"- **{pet['Name']}** - ``{add_suffix(pet['Worth'])}``\n"
            embed.add_field(name="Pets", value=petsstr)
            embed.add_field(name="Best Pet",
                            value=f":dog: **Pet:** ``{bestpet['Name']}``\n:gem: **Worth:** ``{add_suffix(bestpet['Worth'])}``\n:four_leaf_clover: **Chance:** ``{bestpet['Chance']}%``")
            embed.add_field(name="Winnings",value=f":gem: **Total Price**: ``{add_suffix(casedata['Price'] * amount)}``\n:gem: **Total Winnings**: ``{add_suffix(totalwinnings)}``\n:gem: **Profit**: ``{add_suffix(totalwinnings-totalcost)}``", inline=False)
            embed.set_thumbnail(url=bestpet['Icon'])
        else:
            embed = discord.Embed(title="Opened Cases", description=f"You Opened {amount} {case_name}s", color=0xff7575)
            petsstr = ""
            for pet in outcomes :
                petsstr += f"- **{pet['Name']}** - ``{add_suffix(pet['Worth'])}``\n"
            embed.add_field(name="Pets", value=petsstr)
            embed.add_field(name="Best Pet", value=f":dog: **Pet:** ``{bestpet['Name']}``\n:gem: **Worth:** ``{add_suffix(bestpet['Worth'])}``\n:four_leaf_clover: **Chance:** ``{bestpet['Chance']}%``")
            embed.add_field(name="Winnings",
                            value=f":gem: **Total Price**: ``{add_suffix(casedata['Price'] * amount)}``\n:gem: **Total Winnings**: ``{add_suffix(totalwinnings)}``\n:gem: **Profit**: ``-{add_suffix(totalcost - totalwinnings)}``", inline=False)
            embed.set_thumbnail(url=bestpet['Icon'])
        await interaction.edit_original_response(embed=embed)
    else:
        outcomes = []
        for i in range(0, amount) :
            outcomes.append(open_case(case_name))

        subtract_gems(uid, casedata['Price'] * amount)
        embed = discord.Embed(title=f"Opening {amount}x Cases",
                              description=f"Opening {case_name} <t:{round(time.time() + 5)}:R>")
        embed.set_thumbnail(url=casedata['Icon'])
        await interaction.response.send_message(embed=embed)
        await asyncio.sleep(5)
        embed = None
        totalcost = casedata['Price'] * amount
        totalwinnings = 0
        bestpet = {'Worth' : 1}
        for pet in outcomes :
            totalwinnings += pet['Worth']
        add_gems(uid,totalwinnings)
        add_bet(uid, totalcost, totalwinnings)
        if totalwinnings >= totalcost :
            embed = discord.Embed(title="Opened Cases", description=f"You Opened {amount} {case_name}s", color=0x82ff80)
            petsstr = ""
            for pet in outcomes :
                petsstr += f"- **{pet['Name']}** - ``{add_suffix(pet['Worth'])}``\n"
            embed.add_field(name="Pets", value="Open Less Than 30 Cases To See The Pets You Got")
            embed.add_field(name="Winnings",
                            value=f":gem: **Total Price**: ``{add_suffix(casedata['Price'] * amount)}``\n:gem: **Total Winnings**: ``{add_suffix(totalwinnings)}``\n:gem: **Profit**: ``{add_suffix(totalwinnings - totalcost)}``",
                            inline=False)
        else :
            embed = discord.Embed(title="Opened Cases", description=f"You Opened {amount} {case_name}s", color=0xff7575)
            petsstr = ""
            for pet in outcomes :
                petsstr += f"- **{pet['Name']}** - ``{add_suffix(pet['Worth'])}``\n"
            embed.add_field(name="Pets", value="Open Less Than 30 Cases To See The Pets You Got")
            embed.add_field(name="Winnings",
                            value=f":gem: **Total Price**: ``{add_suffix(casedata['Price'] * amount)}``\n:gem: **Total Winnings**: ``{add_suffix(totalwinnings)}``\n:gem: **Profit**: ``-{add_suffix(totalcost - totalwinnings)}``",
                            inline=False)
        await interaction.edit_original_response(embed=embed)
def billions(x, pos) :
    'The two args are the value and tick position'
    return '%1.1fB' % (x * 1e-9)

bot.run(Config['DiscordBotToken'])