import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from datetime import timedelta

TOKEN = "PUT_YOUR_TOKEN_HERE"
LOG_CHANNEL_ID = 1483891442920456263

# 🔥 ايديات الرتب (غيرهم)
ROLES = {
    "warn1": 111111111111,
    "warn2": 222222222222,
    "warn3": 333333333333,
    "dis1": 444444444444,
    "dis2": 555555555555,
}

# ⏱️ المدد
DURATIONS = {
    "warn1": 5 * 24 * 60 * 60,
    "warn2": 7 * 24 * 60 * 60,
    "warn3": 14 * 24 * 60 * 60,
    "dis1": 7 * 24 * 60 * 60,
    "dis2": 14 * 24 * 60 * 60,
}

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)


# حذف الرتبة بعد مدة
async def remove_role(member, role_id, delay):
    await asyncio.sleep(delay)
    role = member.guild.get_role(role_id)
    if role and role in member.roles:
        await member.remove_roles(role)


# القائمة
class PunishSelect(discord.ui.Select):
    def __init__(self, member):
        self.member = member

        options = [
            discord.SelectOption(label="القذف", description="انذار + تايم اوت اسبوع", value="1"),
            discord.SelectOption(label="السب", description="تحذير", value="2"),
            discord.SelectOption(label="تسحيب", description="باند نهائي", value="3"),
            discord.SelectOption(label="تسحيب متكرر", description="تحذير", value="4"),
            discord.SelectOption(label="استعمال ادارة", description="كسر رتبة", value="5"),
        ]

        super().__init__(placeholder="اختر العقوبة", options=options)

    async def callback(self, interaction: discord.Interaction):
        log_channel = interaction.guild.get_channel(LOG_CHANNEL_ID)
        result = ""

        # القذف
        if self.values[0] == "1":
            role = interaction.guild.get_role(ROLES["dis1"])
            if role:
                await self.member.add_roles(role)
                asyncio.create_task(remove_role(self.member, role.id, DURATIONS["dis1"]))

            await self.member.timeout(timedelta(days=7))
            result = f"📛 القذف → انذار + تايم اوت اسبوع على {self.member}"

        # السب
        elif self.values[0] == "2":
            role = interaction.guild.get_role(ROLES["warn1"])
            if role:
                await self.member.add_roles(role)
                asyncio.create_task(remove_role(self.member, role.id, DURATIONS["warn1"]))

            result = f"⚠️ السب → تحذير {self.member}"

        # تسحيب
        elif self.values[0] == "3":
            await self.member.ban(reason="تسحيب")
            result = f"⛔ تم باند {self.member}"

        # تسحيب متكرر
        elif self.values[0] == "4":
            role = interaction.guild.get_role(ROLES["warn1"])
            if role:
                await self.member.add_roles(role)
                asyncio.create_task(remove_role(self.member, role.id, DURATIONS["warn1"]))

            result = f"⚠️ تسحيب متكرر → تحذير {self.member}"

        # استعمال ادارة
        elif self.values[0] == "5":
            top_role = self.member.top_role
            await self.member.remove_roles(top_role)
            result = f"📉 كسر رتبة {self.member}"

        await interaction.response.send_message("✅ تم تنفيذ العقوبة", ephemeral=True)

        if log_channel:
            await log_channel.send(f"{result} | بواسطة {interaction.user}")


# View
class PunishView(discord.ui.View):
    def __init__(self, member):
        super().__init__(timeout=None)
        self.add_item(PunishSelect(member))


# الأمر
@bot.tree.command(name="تايم", description="معاقبة عضو")
@app_commands.describe(user="اختر العضو")
async def punish(interaction: discord.Interaction, user: discord.Member):

    embed = discord.Embed(
        title="📋 نظام العقوبات",
        description="اختر نوع المخالفة"
    )

    file = discord.File("image.png", filename="image.png")
    embed.set_image(url="attachment://image.png")

    await interaction.response.send_message(
        embed=embed,
        view=PunishView(user),
        file=file
    )


@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Bot Ready: {bot.user}")


bot.run(TOKEN)
