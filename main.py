import discord
from discord.ext import commands, tasks
import os
import json
import asyncio
import traceback
from datetime import timedelta

# -------- AUTO FIX --------
try:
    import discord
except:
    os.system("pip install discord.py")

# -------- SETUP --------
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

TOKEN = os.getenv("TOKEN")

# -------- DATABASE --------
def load():
    try:
        with open("data.json") as f:
            return json.load(f)
    except:
        return {}

def save(data):
    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)

# -------- READY --------
@bot.event
async def on_ready():
    print(f"🔥 BOT READY: {bot.user}")
    anti_spam.start()

# -------- ERROR SYSTEM --------
@bot.event
async def on_command_error(ctx, error):
    err = "".join(traceback.format_exception(type(error), error, error.__traceback__))
    print(err)
    await ctx.send(f"❌ Error:\n```{error}```")

# -------- LEVEL SYSTEM --------
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    data = load()
    uid = str(message.author.id)

    if uid not in data:
        data[uid] = {"xp": 0, "level": 1}

    data[uid]["xp"] += 5

    if data[uid]["xp"] >= data[uid]["level"] * 50:
        data[uid]["xp"] = 0
        data[uid]["level"] += 1
        await message.channel.send(f"🎉 {message.author.mention} لفّل إلى {data[uid]['level']}!")

    save(data)

    await bot.process_commands(message)

# -------- AUTO REPLY --------
@bot.event
async def on_message_edit(before, after):
    if "سلام" in after.content:
        await after.channel.send("👋 وعليكم السلام!")

# -------- ANTI SPAM --------
spam = {}

@tasks.loop(seconds=5)
async def anti_spam():
    for user in list(spam):
        if spam[user] > 5:
            spam[user] = 0

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    uid = message.author.id
    spam[uid] = spam.get(uid, 0) + 1

    if spam[uid] > 6:
        try:
            await message.author.timeout(discord.utils.utcnow() + timedelta(minutes=5))
            await message.channel.send(f"🚫 تم معاقبة {message.author.mention} سبام")
        except:
            pass

    await bot.process_commands(message)

# -------- BUTTON MENU --------
class Panel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔨 Ban", style=discord.ButtonStyle.danger)
    async def ban(self, interaction, button):
        await interaction.response.send_message("استخدم الأمر !ban", ephemeral=True)

    @discord.ui.button(label="👢 Kick", style=discord.ButtonStyle.secondary)
    async def kick(self, interaction, button):
        await interaction.response.send_message("استخدم الأمر !kick", ephemeral=True)

# -------- PANEL COMMAND --------
@bot.command()
async def panel(ctx):
    await ctx.send("🎛️ لوحة التحكم", view=Panel())

# -------- BASIC COMMANDS --------
@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong!")

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member):
    await member.kick()
    await ctx.send("👢 تم الطرد")

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member):
    await member.ban()
    await ctx.send("🔨 تم الباند")

# -------- RUN --------
bot.run(TOKEN)
