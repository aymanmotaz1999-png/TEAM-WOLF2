import discord
from discord import app_commands
import json
import time
import asyncio
import traceback

intents = discord.Intents.default()
intents.members = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# 🔴 حط التوكن
TOKEN = "YOUR_BOT_TOKEN"

# 🔴 روم اللوق
LOG_CHANNEL_ID = 1483891442920456263

# ---------------- DATA ----------------

def load_data():
    try:
        with open("data.json", "r") as f:
            return json.load(f)
    except:
        return []

def save_data(data):
    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)

# ---------------- LOG ----------------

def log_error(error):
    with open("errors.log", "a") as f:
        f.write(f"\n{time.ctime()}:\n{error}\n")

async def send_log(guild, message):
    try:
        channel = guild.get_channel(LOG_CHANNEL_ID)
        if channel:
            await channel.send(message)
    except:
        pass

# ---------------- AUTO REMOVE ----------------

async def check_roles():
    await client.wait_until_ready()

    while not client.is_closed():
        try:
            data = load_data()
            now = int(time.time())

            for entry in data[:]:
                if now >= entry["end_time"]:
                    guild = client.get_guild(entry["guild_id"])

                    if guild:
                        member = guild.get_member(entry["user_id"])
                        role = guild.get_role(entry["role_id"])

                        if member and role:
                            try:
                                await member.remove_roles(role)

                                await send_log(
                                    guild,
                                    f"⏳ انتهاء العقوبة\n👤 {member.mention}\n🎭 {role.name}"
                                )

                            except:
                                log_error(traceback.format_exc())

                    data.remove(entry)
                    save_data(data)

        except:
            log_error(traceback.format_exc())

        await asyncio.sleep(10)

# ---------------- UI ----------------

class PunishMenu(discord.ui.Select):
    def __init__(self, member):
        self.member = member

        options = [
            discord.SelectOption(label="القذف", value="qathf"),
            discord.SelectOption(label="السب", value="sab"),
            discord.SelectOption(label="تسحيب", value="ban"),
            discord.SelectOption(label="تسحيب متكرر", value="drag"),
            discord.SelectOption(label="سوء استخدام الإدارة", value="abuse"),
        ]

        super().__init__(placeholder="اختر العقوبة", options=options)

    async def callback(self, interaction: discord.Interaction):
        try:
            value = self.values[0]

            # 🔴 غير IDs
            roles = {
                "warn1": 111111111111,
                "dis1": 222222222222,
                "demote": 333333333333
            }

            role_id = None
            duration = 0

            if value == "qathf":
                role_id = roles["dis1"]
                duration = 7 * 24 * 60 * 60

            elif value == "sab":
                role_id = roles["warn1"]
                duration = 5 * 24 * 60 * 60

            elif value == "ban":
                await self.member.ban()

                await send_log(
                    interaction.guild,
                    f"🚫 باند\n👮 {interaction.user.mention}\n👤 {self.member.mention}"
                )

                await interaction.response.send_message("تم الباند", ephemeral=True)
                return

            elif value == "drag":
                role_id = roles["dis1"]
                duration = 7 * 24 * 60 * 60

            elif value == "abuse":
                role_id = roles["demote"]

            if role_id:
                role = interaction.guild.get_role(role_id)
                await self.member.add_roles(role)

                await send_log(
                    interaction.guild,
                    f"✅ عقوبة جديدة\n👮 {interaction.user.mention}\n👤 {self.member.mention}\n🎭 {role.name}"
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

            await interaction.response.send_message(
                f"تمت معاقبة {self.member.mention}",
                ephemeral=True
            )

        except:
            log_error(traceback.format_exc())

class PunishView(discord.ui.View):
    def __init__(self, member):
        super().__init__(timeout=None)
        self.add_item(PunishMenu(member))

# ---------------- COMMAND ----------------

@tree.command(name="taim", description="إعطاء عقوبة")
@app_commands.describe(user="اختار العضو")
async def taim(interaction: discord.Interaction, user: discord.Member):
    try:
        await interaction.response.send_message(
            f"📋 اختر العقوبة لـ {user.mention}",
            view=PunishView(user)
        )
    except:
        log_error(traceback.format_exc())

# ---------------- READY ----------------

@client.event
async def on_ready():
    print(f"✅ {client.user}")
    await tree.sync()
    client.loop.create_task(check_roles())

# ---------------- ANTI CRASH ----------------

async def main():
    while True:
        try:
            await client.start(TOKEN)
        except:
            log_error(traceback.format_exc())
            print("🔄 Restarting...")
            await asyncio.sleep(5)

asyncio.run(main())
