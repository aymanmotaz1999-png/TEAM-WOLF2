import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import os
from datetime import timedelta

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

LOG_CHANNEL_ID = 1483891442920456263

roles = {
    "warn1": 1475095531389714604,
    "warn2": 1475097777104097545,
    "disc1": 1473015121906368715,
    "disc2": 1473015122753749012,
    "timeout": 1473015129019908232
}

async def add_role(member, role_id, seconds):
    role = member.guild.get_role(role_id)
    if role:
        await member.add_roles(role)
        await asyncio.sleep(seconds)
        await member.remove_roles(role)

class Menu(discord.ui.Select):
    def __init__(self, member):
        self.member = member
        super().__init__(
            placeholder="⚖️ اختر العقوبة",
            options=[
                discord.SelectOption(label="🚫 القذف", value="1"),
                discord.SelectOption(label="🗣️ السب", value="2"),
                discord.SelectOption(label="⛔ تسحيب", value="3"),
                discord.SelectOption(label="🔁 تسحيب متكرر", value="4"),
                discord.SelectOption(label="🛠️ إساءة استخدام الإدارة", value="5"),
            ]
        )

    async def callback(self, interaction: discord.Interaction):
        member = self.member
        log = interaction.guild.get_channel(LOG_CHANNEL_ID)

        if self.values[0] == "1":
            asyncio.create_task(add_role(member, roles["disc1"], 604800))
            asyncio.create_task(add_role(member, roles["disc2"], 1209600))
            await member.timeout(discord.utils.utcnow() + timedelta(days=7))
            msg = f"🚫 القذف | {member.mention}"

        elif self.values[0] == "2":
            asyncio.create_task(add_role(member, roles["warn1"], 432000))
            asyncio.create_task(add_role(member, roles["warn2"], 604800))
            msg = f"🗣️ السب | {member.mention}"

        elif self.values[0] == "3":
            await member.ban()
            msg = f"⛔ باند | {member}"

        elif self.values[0] == "4":
            asyncio.create_task(add_role(member, roles["disc1"], 604800))
            asyncio.create_task(add_role(member, roles["disc2"], 1209600))
            msg = f"🔁 تسحيب متكرر | {member.mention}"

        elif self.values[0] == "5":
            await member.edit(roles=[])
            msg = f"🛠️ كسر رتبة | {member.mention}"

        await interaction.response.send_message("✅ تمت العقوبة", ephemeral=True)

        if log:
            await log.send(msg)

class View(discord.ui.View):
    def __init__(self, member):
        super().__init__()
        self.add_item(Menu(member))

@bot.tree.command(name="عقوبة")
async def punish(interaction: discord.Interaction, user: discord.Member):

    file = discord.File("teamwolf.png")

    embed = discord.Embed(
        title="⚖️ قائمة العقوبات",
        description=f"اختر العقوبة لـ {user.mention}",
        color=discord.Color.red()
    )

    embed.set_image(url="attachment://teamwolf.png")

    await interaction.response.send_message(embed=embed, view=View(user), file=file)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print("✅ BOT ONLINE")

bot.run(os.getenv("TOKEN"))
