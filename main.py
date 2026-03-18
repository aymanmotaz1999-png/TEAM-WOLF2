import discord
from discord import app_commands
import json
import time
import asyncio
import os

TOKEN = os.getenv("TOKEN")
LOG_CHANNEL_ID = 1483891442920456263

intents = discord.Intents.default()
intents.members = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# -------- DATA --------
def load_data():
    try:
        with open("data.json", "r") as f:
            return json.load(f)
    except:
        return []

def save_data(data):
    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)

# -------- LOG --------
async def send_log(guild, title, desc):
    channel = guild.get_channel(LOG_CHANNEL_ID)
    if channel:
        embed = discord.Embed(title=title, description=desc, color=discord.Color.red())
        await channel.send(embed=embed)

# -------- AUTO REMOVE --------
async def check_roles():
    await client.wait_until_ready()

    while True:
        data = load_data()
        now = int(time.time())

        for entry in data[:]:
            if now >= entry["end_time"]:
                guild = client.get_guild(entry["guild_id"])

                if guild:
                    member = guild.get_member(entry["user_id"])
                    role = guild.get_role(entry["role_id"])

                    if member and role:
                        await member.remove_roles(role)

                        await send_log(
                            guild,
                            "✅ انتهاء العقوبة",
                            f"{member.mention} | {role.name}"
                        )

                data.remove(entry)
                save_data(data)

        await asyncio.sleep(10)

# -------- MENU --------
class PunishMenu(discord.ui.Select):
    def __init__(self, member):
        self.member = member

        options = [
            discord.SelectOption(
                label="🚫 القذف",
                description="حرمان 7 أيام",
                value="qathf"
            ),
            discord.SelectOption(
                label="🗣️ السب",
                description="تحذير 5 أيام",
                value="sab"
            ),
            discord.SelectOption(
                label="👢 تسحيب",
                description="طرد من السيرفر",
                value="kick"
            ),
            discord.SelectOption(
                label="🛠️ استخدام خواص إدارة",
                description="سحب صلاحيات / رتبة",
                value="abuse"
            ),
        ]

        super().__init__(placeholder="اختر العقوبة", options=options)

    async def callback(self, interaction: discord.Interaction):
        try:
            value = self.values[0]

            # 🔴 حط IDs رتبك هون
            roles = {
                "warn1": 123456789012345678,
                "dis1": 987654321098765432,
                "demote": 555555555555555555
            }

            role_id = None
            duration = 0

            if value == "qathf":
                role_id = roles["dis1"]
                duration = 7 * 86400

            elif value == "sab":
                role_id = roles["warn1"]
                duration = 5 * 86400

            elif value == "kick":
                await self.member.kick()

                await send_log(
                    interaction.guild,
                    "👢 تسحيب",
                    f"{interaction.user.mention} ➜ {self.member.mention}"
                )

                return await interaction.response.send_message("تم التسحيب 👢", ephemeral=True)

            elif value == "abuse":
                role_id = roles["demote"]

            if role_id:
                role = interaction.guild.get_role(role_id)

                if not role:
                    return await interaction.response.send_message("❌ الرتبة غير موجودة", ephemeral=True)

                await self.member.add_roles(role)

                await send_log(
                    interaction.guild,
                    "⚠️ عقوبة",
                    f"{interaction.user.mention} ➜ {self.member.mention}"
                )

            if duration > 0:
                data = load_data()
                data.append({
                    "user_id": self.member.id,
                    "role_id": role_id,
                    "guild_id": interaction.guild.id,
                    "end_time": int(time.time()) + duration
                })
                save_data(data)

            await interaction.response.send_message("✅ تم التنفيذ", ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(f"❌ خطأ:\n{e}", ephemeral=True)

# -------- VIEW --------
class PunishView(discord.ui.View):
    def __init__(self, member):
        super().__init__(timeout=None)
        self.add_item(PunishMenu(member))

# -------- COMMAND --------
@tree.command(name="taim", description="عقوبة عضو")
async def taim(interaction: discord.Interaction, user: discord.Member):
    await interaction.response.send_message(
        f"اختر العقوبة لـ {user.mention}",
        view=PunishView(user)
    )

# -------- READY --------
@client.event
async def on_ready():
    print(f"✅ {client.user} شغال")
    await tree.sync()
    client.loop.create_task(check_roles())

client.run(TOKEN)
