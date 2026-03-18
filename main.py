import discord
from discord.ext import commands
from discord import app_commands
import asyncio

TOKEN = "PUT_YOUR_TOKEN_HERE"
LOG_CHANNEL_ID = 1483891442920456263

# 🔥 ايديات الرتب
ROLES = {
    "warn1": 1475095531389714604,  # تحذير اول
    "warn2": 1475097777104097545,  # تحذير ثاني
    "warn3": 1475098153421377567,  # تحذير ثالث
    "dis1": 1473015121906368715,   # انذار اول
    "dis2": 1473015122753749012    # انذار ثاني
}

# ⏱️ المدد بالثواني
DURATIONS = {
    "warn1": 5 * 24 * 60 * 60,
    "warn2": 7 * 24 * 60 * 60,
    "warn3": 14 * 24 * 60 * 60,
    "dis1": 7 * 24 * 60 * 60,
    "dis2": 14 * 24 * 60 * 60,
}

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)


# 🧹 حذف الرتبة بعد مدة
async def remove_role(member, role_id, delay):
    await asyncio.sleep(delay)
    role = member.guild.get_role(role_id)
    if role and role in member.roles:
        await member.remove_roles(role)


# 📋 القائمة
class PunishSelect(discord.ui.Select):
    def __init__(self, member):
        self.member = member

        options = [
            discord.SelectOption(label="القذف", description="انذار دسكورد اول + انذار ثاني + تايم اوت اسبوع", value="1"),
            discord.SelectOption(label="السب", description="تحذير اول + تحذير ثاني", value="2"),
            discord.SelectOption(label="تسحيب", description="باند نهائي", value="3"),
            discord.SelectOption(label="تسحيب متكرر", description="تحذير + انذار", value="4"),
            discord.SelectOption(label="استعمال ادارة", description="كسر رتبة", value="5"),
        ]

        super().__init__(placeholder="اختر العقوبة", options=options)

    async def callback(self, interaction: discord.Interaction):
        log_channel = interaction.guild.get_channel(LOG_CHANNEL_ID)
        result = ""

        # 🔴 القذف
        if self.values[0] == "1":
            role = interaction.guild.get_role(ROLES["dis1"])
            await self.member.add_roles(role)
            asyncio.create_task(remove_role(self.member, role.id, DURATIONS["dis1"]))

            # تايم اوت اسبوع
            await self.member.timeout(discord.utils.utcnow() + discord.timedelta(days=7))

            result = f"📛 القذف → انذار + تايم اوت اسبوع على {self.member}"

        # 🟡 السب
        elif self.values[0] == "2":
            role = interaction.guild.get_role(ROLES["warn1"])
            await self.member.add_roles(role)
            asyncio.create_task(remove_role(self.member, role.id, DURATIONS["warn1"]))

            result = f"⚠️ السب → تحذير على {self.member}"

        # 🔥 تسحيب
        elif self.values[0] == "3":
            await self.member.ban(reason="تسحيب")
            result = f"⛔ تسحيب → باند {self.member}"

        # 🟠 تسحيب متكرر
        elif self.values[0] == "4":
            role = interaction.guild.get_role(ROLES["warn1"])
            await self.member.add_roles(role)
            asyncio.create_task(remove_role(self.member, role.id, DURATIONS["warn1"]))

            result = f"⚠️ تسحيب متكرر → تحذير {self.member}"

        # 🔵 استعمال ادارة
        elif self.values[0] == "5":
            top_role = self.member.top_role
            await self.member.remove_roles(top_role)

            result = f"📉 استعمال ادارة → كسر رتبة {self.member}"

        await interaction.response.send_message("✅ تم تنفيذ العقوبة", ephemeral=True)

        if log_channel:
            await log_channel.send(f"{result} | بواسطة {interaction.user}")


# 🧩 View
class PunishView(discord.ui.View):
    def __init__(self, member):
        super().__init__(timeout=None)
        self.add_item(PunishSelect(member))


# 🚀 أمر /تايم
@bot.tree.command(name="تايم", description="معاقبة عضو")
@app_commands.describe(user="العضو")
async def punish(interaction: discord.Interaction, user: discord.Member):

    embed = discord.Embed(
        title="📋 نظام العقوبات",
        description="اختر نوع المخالفة من القائمة"
    )

    file = discord.File("image.png", filename="image.png")
    embed.set_image(url="attachment://image.png")

    await interaction.response.send_message(
        embed=embed,
        view=PunishView(user),
        file=file
    )


# ✅ تشغيل
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Bot Ready: {bot.user}")


bot.run(TOKEN)
