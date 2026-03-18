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
intents.message_content = True

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
async def send_log(guild, text):
    channel = guild.get_channel(LOG_CHANNEL_ID)
    if channel:
        await channel.send(text)

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
                        await send_log(guild, f"✅ انتهت عقوبة {member.mention} وتم سحب {role.name}")

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
                description="إنذار دسكورد + تايم أوت أسبوع",
                value="qathf"
            ),
            discord.SelectOption(
                label="🗣️ السب",
                description="تحذير أول + تحذير ثاني",
                value="sab"
            ),
            discord.SelectOption(
                label="👢 تسحيب",
                description="طرد نهائي",
                value="kick"
            ),
            discord.SelectOption(
                label="🔁 تسحيب متكرر",
                description="تحذيرين",
                value="repeat"
            ),
            discord.SelectOption(
                label="🛠️ استخدام خواص إدارة",
                description="كسر رتبة",
                value="abuse"
            ),
        ]

        super().__init__(placeholder="اختر العقوبة", options=options)

    async def callback(self, interaction: discord.Interaction):
        try:
            value = self.values[0]

            # 🔴 حط IDs الرتب
            roles = {
                "warn1": 111111111111111111,
                "warn2": 222222222222222222,
                "discord1": 333333333333333333,
                "discord2": 444444444444444444,
                "demote": 555555555555555555
            }

            duration_map = {
                "warn1": 5 * 86400,
                "warn2": 7 * 86400,
                "discord1": 7 * 86400,
                "discord2": 14 * 86400
            }

            async def give_role(role_key):
                role_id = roles[role_key]
                role = interaction.guild.get_role(role_id)

                if not role:
                    return await interaction.response.send_message("❌ الرتبة غير موجودة", ephemeral=True)

                await self.member.add_roles(role)

                data = load_data()
                data.append({
                    "user_id": self.member.id,
                    "role_id": role_id,
                    "guild_id": interaction.guild.id,
                    "end_time": int(time.time()) + duration_map.get(role_key, 0)
                })
                save_data(data)

            # -------- الحالات --------
            if value == "qathf":
                await give_role("discord1")
                await give_role("discord2")
                await self.member.timeout(discord.utils.utcnow() + discord.timedelta(days=7))

            elif value == "sab":
                await give_role("warn1")
                await give_role("warn2")

            elif value == "kick":
                await self.member.kick()
                await send_log(interaction.guild, f"👢 تم تسحيب {self.member.mention}")

            elif value == "repeat":
                await give_role("warn1")
                await give_role("warn2")

            elif value == "abuse":
                await give_role("demote")

            await send_log(
                interaction.guild,
                f"⚠️ {interaction.user.mention} عاقب {self.member.mention} | {value}"
            )

            await interaction.response.send_message("✅ تم تنفيذ العقوبة", ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(f"❌ خطأ:\n{e}", ephemeral=True)

# -------- VIEW --------
class PunishView(discord.ui.View):
    def __init__(self, member):
        super().__init__(timeout=None)
        self.add_item(PunishMenu(member))

# -------- COMMAND --------
@tree.command(name="taim", description="معاقبة عضو")
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
