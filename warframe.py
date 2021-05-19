import requests, json, asyncio
from datetime import datetime, time, timedelta
import discord
from discord.ext import commands

import meta #"meta" contains a prefix, the discord name, client id and token
            #obvious reasons, it's not public

prefix = meta.prefix
name = meta.name
token = meta.token
clid = meta.clid 

#Time of the daily message
sortieResetTime = time(16, 0, 5)

bot = commands.Bot(command_prefix = prefix)
bot.remove_command("help") #It's done because we make our own help command

#utility function for use as a filter
def to_capital(argument):
    return argument.capitalize()

#sends a GET request to api.warframestat.us and sends the edited responce
#to the discord channel with channel id = channel_id
#fair warning: the responce @everyones, so keep that in mind
#or remove it if you want
async def sortieSend(channel_id : int):
    chn = bot.get_channel(int(channel_id)) #we get the channel from the passed id
    sortieResponce = requests.get("https://api.warframestat.us/pc/sortie")
    sortieJson = json.loads(sortieResponce.text) #get the JSON string
    #and begin formatting the message
    stri='||@everyone||\n```md\n#' #```md is so that it all looks pretty
    stri+=sortieJson["faction"]+' - '+sortieJson['boss']+'\n\n' #the message puts out the faction and boss name
    for i in range(0, 3):
        stri+= sortieJson["variants"][i]["missionType"]+ ' on '+sortieJson["variants"][i]["node"] + '\n'+sortieJson["variants"][i]["modifier"] + "\n\n" #and all the missions with modifiers
    stri+='```'
    await chn.send(stri)

#binds the daily announcements to a certain channel mentioned in a message
@bot.command()
async def setSortieChannel(ctx, channel : discord.TextChannel):
    await ctx.send(f"Bound sortie announcements to {channel.mention}")
    channel_id = int(channel.id)
    
    now = datetime.utcnow()
    if now.time()>sortieResetTime: #waits for a new day if it's later then needed time
        tomorrow = datetime.combine(now.date() + timedelta(days = 1), time(0))
        secondsUntilTomorrow = (tomorrow - now).total_seconds()
        await asyncio.sleep(secondsUntilTomorrow+5)

    #and after that waits until it's time
    now = datetime.utcnow()
    timeUntilTarget = datetime.combine(now.date(), sortieResetTime)
    secondsUntilTarget = (timeUntilTarget-now).total_seconds()
    await asyncio.sleep(secondsUntilTarget+5)
    while True:
        await sortieSend(channel_id)
        await asyncio.sleep(24*60*60)
        #sends a message and sleeps for exactly 24 hours


#utility function to remove the "Z" marker of ZULU timezone contained in the JSON string
def dateTimeToStandard(zDateTime):
    return datetime.fromisoformat(zDateTime.replace("Z", ""))

#utility function to get the current UTC time 
def getCurrentUtcTime():
    dt = datetime.utcnow().isoformat(timespec="milliseconds")
    return dt

#utility function to calculate the difference between dt2 and dt1
def calculateSecondsBetweenTwoDateTimes(dt1, dt2):
    difference = dt2 - dt1
    return difference.total_seconds()

#utility function related to Deimos, returns Fass if the currently active worm is Vome and vice versa
#if you're using this bot for anything else, you can probably remove it
def otherWorm(worm):
    if worm == "vome":
        return "Fass"
    else:
        return "Vome"

#because Digital Extremes decided that changing the JSON format on their third open world is a nice idea
#we have to make our own formatted string with remaining time
#this gets the int number of seconds and a string and formats them together
def shortStringDeimos(secondsRemaining, currentWorm):
    s = ""
    #the following basically splices the seconds up into a Xh Ym Zs format
    if (secondsRemaining//3600)>0:
        s+=str(int(secondsRemaining//3600))+"h "
        secondsRemaining=secondsRemaining%3600
    if (secondsRemaining//60)>0:
        s+=str(int(secondsRemaining//60))+"m "
        secondsRemaining=secondsRemaining%60
    if (secondsRemaining)>0:
        s+=str(int(secondsRemaining))+"s "
    #and this adds the other worm. again, if you're using this for anything other than warframe, you can remove it
    s+="to " + otherWorm(currentWorm)
    return s

#a command that gets the open world and returns it's time of day, heat cycle or worm, getting the data from api.warframestat.us
#uses the aforementioned to_capital function, so the argument passed by the user is case-insensitive
@bot.command()
async def worldState(ctx, world: to_capital):
    if world not in {"Earth", "Venus", "Deimos"}:
        #if the argument passed isn't valid, we say exactly that
        await ctx.send("Wrong argument")

    elif world in {"Earth", "Venus"}:
        #if it's one of the first two open worlds, we just use the shortString parameter of the JSON string
        #to get the remaing cycle time
        if world == "Earth":
            location = "cetus"
        elif world == "Venus":
            location = "vallis"
        stri = "https://api.warframestat.us/pc/"+location+"Cycle"
        #we just GET the string from api.warframestat.us
        worldStateResponse = requests.get(stri)
        worldStateJson = json.loads(worldStateResponse.text)
        stri = "It is currently "+worldStateJson["state"]+" on "+world+", "+worldStateJson["shortString"]
        #format it and send it
        await ctx.send(stri)
        
    else:
        location = "cambion"
        #but if we're looking for info on Deimos, we have to get the time remaining ourselves
        stri = "https://api.warframestat.us/pc/"+location+"Cycle"
        worldStateResponse = requests.get(stri)
        worldStateJson = json.loads(worldStateResponse.text)
        #so we do, by using the calculate time difference and get utc now functions we made earlier. and the worm function is used there, too
        stri = to_capital(worldStateJson["active"])+" is currently active on "+world+", "+shortStringDeimos(calculateSecondsBetweenTwoDateTimes(dateTimeToStandard(getCurrentUtcTime()), dateTimeToStandard(worldStateJson["expiry"])), worldStateJson["active"])
        await ctx.send(stri) 

#literally just credits the creator. it's BSD licence, you can remove it if you want
@bot.command()
async def credits(ctx):
    s = "Made by <@293196219461664768> for Reservoir Dogs using Discord.py"
    await ctx.send(s)

#multiple commands in one, so we use @bot.group()

#it's a help command, nothing less and nothing more
@bot.group(invoke_without_command = True)
async def help(ctx):
    em = discord.Embed(title = "Help", description = "Use ^help <command> for more info")
    #embeds are used because they look pretty
    #value="" contains all commands that can be used. that is not automatic, so if you add any more commands
    #you probably should edit this field, too
    em.add_field(name = "Commands", value = "worldState\nsetSortieChannel\ncredits")

    await ctx.send(embed = em)

#all of the following commands provide extended info on certain commands
#"color" is unnecessary, but it looks nice

@help.command()
async def worldState(ctx):
    em = discord.Embed(title = "WorldState", description = "Shows you the open world status on a given planet", color = discord.Color.blue())
    em.add_field(name = "Syntax", value = "^worldState <earth, venus, deimos>")
    await ctx.send(embed = em)

@help.command()
async def setSortieChannel(ctx):
    em = discord.Embed(title = "SetSortieChannel", description = "Binds sortie announcements to a certain channel", color = discord.Color.blue())
    em.add_field(name = "Syntax", value = "^setSortieChannel <#channel>")
    await ctx.send(embed = em)

@help.command()
async def credits(ctx):
    em = discord.Embed(title = "Credits", description = "Shows the credits for this bot", color = discord.Color.blue())
    em.add_field(name = "Syntax", value = "^credits")
    await ctx.send(embed =em)
    
#again, nake your own meta.py file and put your own token in
bot.run(token)
    
