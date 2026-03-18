import discord
from discord import app_commands
import asyncio
import time
import json
import os
from datetime import timedelta

TOKEN = os.getenv("TOKEN")
LOG_CHANNEL_ID = 1483891442920456263

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# -------- DATA --------
def load_data():
    if not os.path.exists("data.json"):
        return []
    with open("data.json", "r") as f:
        return json.load(f)

def save_data(data):
    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)

# -------- LOG --------
async def log(guild, msg):
    channel = guild.get_channel(LOG_CHANNEL_ID)
    if channel:
        await channel.send(msg)

# -------- AUTO REMOVE --------
async def auto_remove():
    await client.wait_until_ready()

    while True:
        data = load_data()
        now = int(time.time())

        for d in data[:]:
            if now >= d["end"]:
                guild = client.get_guild(d["guild"])
                if guild:
                    member = guild.get_member(d["user"])
                    role = guild.get_role(d["role"])

                    if member and role:
                        await member.remove_roles(role)
                        await log(guild, f"✅ انتهت العقوبة: {member.mention}")

                data.remove(d)
                save_data(data)

        await asyncio.sleep(10)

# -------- MENU --------
class Menu(discord.ui.Select):
    def __init__(self, member):
        self.member = member

        options = [
            discord.SelectOption(
                label="🚫 القذف",
                description="إنذار دسكورد + تايم أوت أسبوع",
                value="1"
            ),
            discord.SelectOption(
                label="🗣️ السب",
                description="تحذير أول + ثاني",
                value="2"
            ),
            discord.SelectOption(
                label="👢 تسحيب",
                description="طرد نهائي",
                value="3"
            ),
            discord.SelectOption(
                label="🔁 تسحيب متكرر",
                description="تحذيرين",
                value="4"
            ),
            discord.SelectOption(
                label="🛠️ استخدام خواص إدارة",
                description="كسر رتبة",
                value="5"
            ),
        ]

        super().__init__(placeholder="اختر العقوبة", options=options)

    async def callback(self, interaction: discord.Interaction):
        try:
            roles = {
                "warn1": 111111111111111111,
                "warn2": 222222222222222222,
                "d1": 333333333333333333,
                "d2": 444444444444444444,
                "demote": 555555555555555555
            }

            durations = {
                "warn1": 5 * 86400,
                "warn2": 7 * 86400,
                "d1": 7 * 86400,
                "d2": 14 * 86400
            }

            async def give(role_key):
                role = interaction.guild.get_role(roles[role_key])
                if not role:
                    return

                await self.member.add_roles(role)

                data = load_data()
                data.append({
                    "user": self.member.id,
                    "role": role.id,
                    "guild": interaction.guild.id,
                    "end": int(time.time()) + durations.get(role_key, 0)
                })
                save_data(data)

            v = self.values[0]

            if v == "1":  # القذف
                await give("d1")
                await give("d2")
                await self.member.timeout(discord.utils.utcnow() + timedelta(days=7))

            elif v == "2":  # السب
                await give("warn1")
                await give("warn2")

            elif v == "3":  # تسحيب
                await self.member.kick()

            elif v == "4":  # متكرر
                await give("warn1")
                await give("warn2")

            elif v == "5":  # ادارة
                await give("demote")

            await log(interaction.guild, f"⚠️ {interaction.user.mention} ➜ {self.member.mention}")
            await interaction.response.send_message("✅ تم التنفيذ", ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(f"❌ خطأ: {e}", ephemeral=True)

# -------- VIEW --------
class View(discord.ui.View):
    def __init__(self, member):
        super().__init__(timeout=None)
        self.add_item(Menu(member))

# -------- COMMAND --------
@tree.command(name="taim", description="معاقبة عضو")
async def taim(interaction: discord.Interaction, user: discord.Member):
    await interaction.response.send_message(
        f"اختر العقوبة لـ {user.mention}",
        view=View(user)
    )

# -------- READY --------
@client.event
async def on_ready():
    print(f"🔥 {client.user} شغال")
    await tree.sync()
    client.loop.create_task(auto_remove())

client.run(TOKEN)
