import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import os
import re
from datetime import timedelta

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

LOG_CHANNEL_ID = 1483891442920456263

roles = {
    "warn1": 1475095531389714604,
    "warn2": 1475097777104097545,
    "warn3": 1475098153421377567,
    "disc1": 1473015121906368715,
    "disc2": 1473015122753749012,
    "timeout": 1473015129019908232,
}

durations = {
    "warn1": 5*24*60*60,
    "warn2": 7*24*60*60,
    "warn3": 14*24*60*60,
    "disc1": 7*24*60*60,
    "disc2": 14*24*60*60,
}

async def remove_role_later(member, role, delay):
    await asyncio.sleep(delay)
    if role in member.roles:
        await member.remove_roles(role)

async def log(guild, msg):
    ch = guild.get_channel(LOG_CHANNEL_ID)
    if ch:
        await ch.send(msg)

class Menu(discord.ui.Select):
    def __init__(self, member):
        self.member = member
        options = [
            discord.SelectOption(label="قذف", description="انذار دسكورد اول + ثاني + تايم اوت اسبوع"),
            discord.SelectOption(label="سب", description="تحذير اول + تحذير ثاني"),
            discord.SelectOption(label="تسحيب", description="باند نهائي"),
            discord.SelectOption(label="تسحيب متكرر", description="انذار دسكورد اول + ثاني"),
            discord.SelectOption(label="استعمال ادارة", description="كسر رتبة"),
        ]
        super().__init__(placeholder="اختر العقوبة", options=options)

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        m = self.member

        if self.values[0] == "قذف":
            r1 = guild.get_role(roles["disc1"])
            r2 = guild.get_role(roles["disc2"])
            await m.add_roles(r1, r2)
            await m.timeout(discord.utils.utcnow() + timedelta(days=7))
            bot.loop.create_task(remove_role_later(m, r1, durations["disc1"]))
            bot.loop.create_task(remove_role_later(m, r2, durations["disc2"]))

        elif self.values[0] == "سب":
            r1 = guild.get_role(roles["warn1"])
            r2 = guild.get_role(roles["warn2"])
            await m.add_roles(r1, r2)
            bot.loop.create_task(remove_role_later(m, r1, durations["warn1"]))
            bot.loop.create_task(remove_role_later(m, r2, durations["warn2"]))

        elif self.values[0] == "تسحيب":
            await m.ban(reason="تسحيب")

        elif self.values[0] == "تسحيب متكرر":
            r1 = guild.get_role(roles["disc1"])
            r2 = guild.get_role(roles["disc2"])
            await m.add_roles(r1, r2)

        elif self.values[0] == "استعمال ادارة":
            for role in m.roles:
                if role.permissions.administrator:
                    await m.remove_roles(role)

        await interaction.response.send_message("✅ تم تنفيذ العقوبة", ephemeral=True)
        await log(guild, f"🚨 {interaction.user.mention} عاقب {m.mention}")

class View(discord.ui.View):
    def __init__(self, member):
        super().__init__()
        self.add_item(Menu(member))

@bot.tree.command(name="عقوبة")
@app_commands.describe(member="اختار العضو")
async def punish(interaction: discord.Interaction, member: discord.Member):
    await interaction.response.send_message("اختر العقوبة:", view=View(member), ephemeral=True)

@bot.event
async def on_message(msg):
    if msg.author.bot:
        return

    # سبام
    if len(msg.content) > 200:
        await msg.author.timeout(discord.utils.utcnow() + timedelta(minutes=3))
        await log(msg.guild, f"⚠️ سبام: {msg.author.mention}")

    # روابط
    if re.search(r"discord.gg", msg.content):
        await msg.author.timeout(discord.utils.utcnow() + timedelta(hours=1))
        await log(msg.guild, f"🔗 رابط: {msg.author.mention}")

    await bot.process_commands(msg)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Logged in as {bot.user}")

bot.run(os.getenv("TOKEN"))
