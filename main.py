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
    "warn3": 1475098153421377567,
    "disc1": 1473015121906368715,
    "disc2": 1473015122753749012,
    "timeout": 1473015129019908232
}

durations = {
    "warn1": 5 * 24 * 60 * 60,
    "warn2": 7 * 24 * 60 * 60,
    "warn3": 14 * 24 * 60 * 60,
    "disc1": 7 * 24 * 60 * 60,
    "disc2": 14 * 24 * 60 * 60
}

async def add_timed_role(member, role_id, duration):
    role = member.guild.get_role(role_id)
    if role:
        await member.add_roles(role)
        await asyncio.sleep(duration)
        await member.remove_roles(role)

class PunishMenu(discord.ui.Select):
    def __init__(self, member):
        self.member = member

        options = [
            discord.SelectOption(label="🚫 القذف", value="qazf"),
            discord.SelectOption(label="🗣️ السب", value="sab"),
            discord.SelectOption(label="⛔ تسحيب", value="ban"),
            discord.SelectOption(label="🔁 تسحيب متكرر", value="repeat"),
            discord.SelectOption(label="🛠️ إساءة استخدام الإدارة", value="abuse"),
        ]

        super().__init__(placeholder="اختر العقوبة ⚖️", options=options)

    async def callback(self, interaction: discord.Interaction):
        member = self.member
        log_channel = interaction.guild.get_channel(LOG_CHANNEL_ID)

        if self.values[0] == "qazf":
            asyncio.create_task(add_timed_role(member, roles["disc1"], durations["disc1"]))
            asyncio.create_task(add_timed_role(member, roles["disc2"], durations["disc2"]))
            await member.add_roles(interaction.guild.get_role(roles["timeout"]))
            await member.timeout(discord.utils.utcnow() + timedelta(days=7))
            log = f"🚫 القذف | {member.mention}"

        elif self.values[0] == "sab":
            asyncio.create_task(add_timed_role(member, roles["warn1"], durations["warn1"]))
            asyncio.create_task(add_timed_role(member, roles["warn2"], durations["warn2"]))
            log = f"🗣️ السب | {member.mention}"

        elif self.values[0] == "ban":
            await member.ban()
            log = f"⛔ باند | {member}"

        elif self.values[0] == "repeat":
            asyncio.create_task(add_timed_role(member, roles["disc1"], durations["disc1"]))
            asyncio.create_task(add_timed_role(member, roles["disc2"], durations["disc2"]))
            log = f"🔁 تسحيب متكرر | {member.mention}"

        elif self.values[0] == "abuse":
            await member.edit(roles=[])
            log = f"🛠️ كسر رتبة | {member.mention}"

        await interaction.response.send_message("✅ تمت العقوبة", ephemeral=True)

        if log_channel:
            await log_channel.send(log)

class PunishView(discord.ui.View):
    def __init__(self, member):
        super().__init__()
        self.add_item(PunishMenu(member))

@bot.tree.command(name="عقوبة", description="إعطاء عقوبة")
async def punish(interaction: discord.Interaction, user: discord.Member):
    file = discord.File("teamwolf.png", filename="teamwolf.png")

    embed = discord.Embed(
        title="⚖️ قائمة العقوبات",
        description=f"اختر العقوبة لـ {user.mention}",
        color=discord.Color.red()
    )

    embed.set_image(url="attachment://teamwolf.png")

    await interaction.response.send_message(embed=embed, view=PunishView(user), file=file)

@bot.event
async def on_voice_state_update(member, before, after):
    if member.guild_permissions.administrator:
        if before.mute != after.mute or before.deaf != after.deaf:
            try:
                await member.timeout(discord.utils.utcnow() + timedelta(minutes=5))
            except:
                pass

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Bot is online: {bot.user}")

bot.run(os.getenv("TOKEN"))
