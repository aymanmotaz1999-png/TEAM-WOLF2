import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
import re

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

LOG_CHANNEL_ID = 1483891442920456263

# الرتب
roles = {
    "warn1": 1475095531389714604,
    "warn2": 1475097777104097545,
    "warn3": 1475098153421377567,
    "disc1": 1473015121906368715,
    "disc2": 1473015122753749012,
    "timeout": 1473015129019908232,
}

# مدد العقوبات (بالثواني)
durations = {
    "warn1": 5 * 24 * 60 * 60,
    "warn2": 7 * 24 * 60 * 60,
    "warn3": 14 * 24 * 60 * 60,
    "disc1": 7 * 24 * 60 * 60,
    "disc2": 14 * 24 * 60 * 60,
}

# إزالة الرتبة بعد مدة
async def remove_role_later(member, role, delay):
    await asyncio.sleep(delay)
    if role in member.roles:
        await member.remove_roles(role)

# لوق
async def send_log(guild, message):
    channel = guild.get_channel(LOG_CHANNEL_ID)
    if channel:
        await channel.send(message)

# القائمة
class PunishSelect(discord.ui.Select):
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
        member = self.member

        if self.values[0] == "قذف":
            r1 = guild.get_role(roles["disc1"])
            r2 = guild.get_role(roles["disc2"])
            await member.add_roles(r1, r2)
            await member.timeout(discord.utils.utcnow() + discord.timedelta(days=7))

            bot.loop.create_task(remove_role_later(member, r1, durations["disc1"]))
            bot.loop.create_task(remove_role_later(member, r2, durations["disc2"]))

        elif self.values[0] == "سب":
            r1 = guild.get_role(roles["warn1"])
            r2 = guild.get_role(roles["warn2"])
            await member.add_roles(r1, r2)

            bot.loop.create_task(remove_role_later(member, r1, durations["warn1"]))
            bot.loop.create_task(remove_role_later(member, r2, durations["warn2"]))

        elif self.values[0] == "تسحيب":
            await member.ban(reason="تسحيب")

        elif self.values[0] == "تسحيب متكرر":
            r1 = guild.get_role(roles["disc1"])
            r2 = guild.get_role(roles["disc2"])
            await member.add_roles(r1, r2)

        elif self.values[0] == "استعمال ادارة":
            for role in member.roles:
                if role.permissions.administrator:
                    await member.remove_roles(role)

        await interaction.response.send_message("تم تنفيذ العقوبة ✅", ephemeral=True)
        await send_log(guild, f"تم معاقبة {member.mention} بواسطة {interaction.user.mention}")

class PunishView(discord.ui.View):
    def __init__(self, member):
        super().__init__()
        self.add_item(PunishSelect(member))

# أمر سلاش
@bot.tree.command(name="عقوبة")
@app_commands.describe(member="اختار العضو")
async def punish(interaction: discord.Interaction, member: discord.Member):
    await interaction.response.send_message("اختر العقوبة:", view=PunishView(member), ephemeral=True)

# 🛑 Anti Spam
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # سبام
    if len(message.content) > 200:
        await message.author.timeout(discord.utils.utcnow() + discord.timedelta(minutes=3))
        await send_log(message.guild, f"سبام: {message.author.mention}")

    # روابط
    if re.search(r"discord.gg/", message.content):
        await message.author.timeout(discord.utils.utcnow() + discord.timedelta(hours=1))
        await send_log(message.guild, f"رابط خارجي: {message.author.mention}")

    await bot.process_commands(message)

bot.run("YOUR_TOKEN_HERE")
