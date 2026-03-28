import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import re
import os
from datetime import timedelta

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

# الرتب المحمية
protected_roles = [
    1473015044643094643,
    1473015048443269160,
    1473015062800367618,
]

# المدد
durations = {
    "warn1": 5 * 24 * 60 * 60,
    "warn2": 7 * 24 * 60 * 60,
    "warn3": 14 * 24 * 60 * 60,
    "disc1": 7 * 24 * 60 * 60,
    "disc2": 14 * 24 * 60 * 60,
}

# تحقق اذا العضو محمي
def is_protected(member):
    return any(role.id in protected_roles for role in member.roles)

# حذف رتبة بعد مدة
async def remove_role_later(member, role, delay):
    await asyncio.sleep(delay)
    if role in member.roles:
        await member.remove_roles(role)

# لوق
async def send_log(guild, msg):
    ch = guild.get_channel(LOG_CHANNEL_ID)
    if ch:
        await ch.send(msg)

# القائمة
class PunishSelect(discord.ui.Select):
    def __init__(self, member):
        self.member = member
        options = [
            discord.SelectOption(label="قذف", description="انذار1 + انذار2 + تايم اوت اسبوع"),
            discord.SelectOption(label="سب", description="تحذير1 + تحذير2"),
            discord.SelectOption(label="تسحيب", description="باند نهائي"),
            discord.SelectOption(label="تسحيب متكرر", description="انذار1 + انذار2"),
            discord.SelectOption(label="استعمال ادارة", description="كسر رتبة"),
        ]
        super().__init__(placeholder="اختر العقوبة", options=options)

    async def callback(self, interaction: discord.Interaction):
        member = self.member
        guild = interaction.guild

        if is_protected(member):
            return await interaction.response.send_message("❌ هذا العضو محمي", ephemeral=True)

        if self.values[0] == "قذف":
            r1 = guild.get_role(roles["disc1"])
            r2 = guild.get_role(roles["disc2"])
            t = guild.get_role(roles["timeout"])

            await member.add_roles(r1, r2, t)
            await member.timeout(discord.utils.utcnow() + timedelta(days=7))

            bot.loop.create_task(remove_role_later(member, r1, durations["disc1"]))
            bot.loop.create_task(remove_role_later(member, r2, durations["disc2"]))
            bot.loop.create_task(remove_role_later(member, t, 7 * 24 * 60 * 60))

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

        await interaction.response.send_message("✅ تم تنفيذ العقوبة", ephemeral=True)
        await send_log(guild, f"تم معاقبة {member.mention} بواسطة {interaction.user.mention}")

class PunishView(discord.ui.View):
    def __init__(self, member):
        super().__init__()
        self.add_item(PunishSelect(member))

# امر سلاش
@bot.tree.command(name="عقوبة")
async def punish(interaction: discord.Interaction, member: discord.Member):
    await interaction.response.send_message("اختر العقوبة:", view=PunishView(member), ephemeral=True)

# 🔥 الحماية
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # سبام
    if len(message.content) > 200:
        await message.author.timeout(discord.utils.utcnow() + timedelta(minutes=3))
        await send_log(message.guild, f"سبام: {message.author.mention}")

    # روابط + حذفها
    if re.search(r"(discord\.gg/|discord\.com/invite)", message.content):
        try:
            await message.delete()
        except:
            pass

        await message.author.timeout(discord.utils.utcnow() + timedelta(hours=1))
        await send_log(message.guild, f"🚫 رابط خارجي + حذف الرسالة: {message.author.mention}")

    await bot.process_commands(message)

# تشغيل
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")

bot.run(os.getenv("TOKEN"))
