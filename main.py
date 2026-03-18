import discord
from discord.ext import commands, tasks
import os, json, time, traceback
from datetime import timedelta

TOKEN = os.getenv("TOKEN")
LOG_CHANNEL = 1483891442920456263

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# -------- DATABASE --------
def load():
    try:
        with open("data.json") as f:
            return json.load(f)
    except:
        return {"punishments": [], "levels": {}}

def save(data):
    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)

# -------- LOG --------
async def log(guild, msg):
    ch = guild.get_channel(LOG_CHANNEL)
    if ch:
        await ch.send(msg)

# -------- READY --------
@bot.event
async def on_ready():
    print(f"🔥 {bot.user} ONLINE")
    auto_remove.start()

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

    if uid not in data["levels"]:
        data["levels"][uid] = {"xp": 0, "level": 1}

    data["levels"][uid]["xp"] += 5

    if data["levels"][uid]["xp"] >= data["levels"][uid]["level"] * 50:
        data["levels"][uid]["xp"] = 0
        data["levels"][uid]["level"] += 1
        await message.channel.send(f"🎉 {message.author.mention} لفّل!")

    save(data)

    await bot.process_commands(message)

# -------- ANTI SPAM --------
spam = {}

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    uid = message.author.id
    spam[uid] = spam.get(uid, 0) + 1

    if spam[uid] > 6:
        try:
            await message.author.timeout(discord.utils.utcnow() + timedelta(minutes=5))
            await message.channel.send(f"🚫 سبام: {message.author.mention}")
        except:
            pass

    await bot.process_commands(message)

# -------- AUTO REMOVE ROLES --------
@tasks.loop(seconds=10)
async def auto_remove():
    data = load()
    now = int(time.time())

    for p in data["punishments"][:]:
        if now >= p["end"]:
            guild = bot.get_guild(p["guild"])
            if guild:
                member = guild.get_member(p["user"])
                role = guild.get_role(p["role"])

                if member and role:
                    await member.remove_roles(role)
                    await log(guild, f"✅ انتهت العقوبة: {member.mention}")

            data["punishments"].remove(p)
            save(data)

# -------- MENU --------
class Menu(discord.ui.Select):
    def __init__(self, member):
        self.member = member

        options = [
            discord.SelectOption(label="🚫 قذف", value="1"),
            discord.SelectOption(label="🗣️ سب", value="2"),
            discord.SelectOption(label="👢 تسحيب", value="3"),
            discord.SelectOption(label="🔁 تسحيب متكرر", value="4"),
            discord.SelectOption(label="🛠️ استخدام خواص إدارة", value="5"),
        ]

        super().__init__(placeholder="اختر العقوبة", options=options)

    async def callback(self, interaction: discord.Interaction):
        try:
            roles = {
                "warn1": 111111111111,
                "warn2": 222222222222
            }

            data = load()

            if self.values[0] == "1":
                role = interaction.guild.get_role(roles["warn1"])
                await self.member.add_roles(role)

                data["punishments"].append({
                    "user": self.member.id,
                    "role": role.id,
                    "guild": interaction.guild.id,
                    "end": int(time.time()) + 604800
                })

                await self.member.timeout(discord.utils.utcnow() + timedelta(days=7))

            elif self.values[0] == "3":
                await self.member.kick()

            save(data)

            await log(interaction.guild, f"⚠️ {interaction.user} ➜ {self.member}")
            await interaction.response.send_message("✅ تم", ephemeral=True)

        except Exception as e:
            await interaction.response.send_message("❌ خطأ", ephemeral=True)

# -------- VIEW --------
class View(discord.ui.View):
    def __init__(self, member):
        super().__init__(timeout=None)
        self.add_item(Menu(member))

# -------- COMMAND --------
@bot.command()
async def taim(ctx, member: discord.Member):
    await ctx.send("اختر العقوبة:", view=View(member))

# -------- PANEL --------
@bot.command()
async def panel(ctx):
    await ctx.send("🎛️ لوحة تحكم")

# -------- RUN --------
bot.run(TOKEN)
