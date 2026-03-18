# 🔥 AUTO INSTALL (يحل مشكلة discord نهائياً)
import os
try:
    import discord
except:
    os.system("pip install discord.py")
    import discord

from discord import app_commands
import json
import time
import asyncio
import traceback

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
    try:
        with open("data.json", "w") as f:
            json.dump(data, f, indent=4)
    except:
        pass

# -------- LOG --------
async def send_log(guild, title, desc):
    try:
        channel = guild.get_channel(LOG_CHANNEL_ID)
        if channel:
            embed = discord.Embed(title=title, description=desc, color=discord.Color.red())
            embed.timestamp = discord.utils.utcnow()
            await channel.send(embed=embed)
    except:
        pass

# -------- ERROR FIXER --------
async def auto_fix(error, guild=None):
    print("❌ Error:", error)
    traceback.print_exc()

    try:
        if guild:
            ch = guild.get_channel(LOG_CHANNEL_ID)
            if ch:
                await ch.send(f"❌ Error:\n```{error}```")
    except:
        pass

# -------- AUTO TASK SAFE --------
async def safe_loop(task):
    while True:
        try:
            await task()
        except Exception as e:
            await auto_fix(e)
            await asyncio.sleep(5)

# -------- AUTO REMOVE --------
async def check_roles():
    await client.wait_until_ready()

    while True:
        try:
            data = load_data()
            now = int(time.time())

            for entry in data[:]:
                try:
                    if now >= entry["end_time"]:
                        guild = client.get_guild(entry["guild_id"])

                        if guild:
                            member = guild.get_member(entry["user_id"])
                            role = guild.get_role(entry["role_id"])

                            if member and role:
                                await member.remove_roles(role)

                                await send_log(
                                    guild,
                                    "انتهاء العقوبة",
                                    f"{member.mention} | {role.name}"
                                )

                        data.remove(entry)
                        save_data(data)

                except Exception as e:
                    await auto_fix(e)

        except Exception as e:
            await auto_fix(e)

        await asyncio.sleep(10)

# -------- UI --------
class PunishMenu(discord.ui.Select):
    def __init__(self, member):
        self.member = member

        options = [
            discord.SelectOption(label="القذف", value="qathf"),
            discord.SelectOption(label="السب", value="sab"),
            discord.SelectOption(label="باند", value="ban"),
            discord.SelectOption(label="سوء استخدام", value="abuse"),
        ]

        super().__init__(placeholder="اختر العقوبة", options=options)

    async def callback(self, interaction: discord.Interaction):
        try:
            value = self.values[0]

            roles = {
                "warn1": 111111111111,
                "dis1": 222222222222,
                "demote": 333333333333
            }

            role_id = None
            duration = 0

            if value == "qathf":
                role_id = roles["dis1"]
                duration = 7 * 86400

            elif value == "sab":
                role_id = roles["warn1"]
                duration = 5 * 86400

            elif value == "ban":
                await self.member.ban()

                await send_log(
                    interaction.guild,
                    "باند",
                    f"{interaction.user.mention} ➜ {self.member.mention}"
                )

                return await interaction.response.send_message("تم الباند", ephemeral=True)

            elif value == "abuse":
                role_id = roles["demote"]

            if role_id:
                role = interaction.guild.get_role(role_id)
                await self.member.add_roles(role)

                await send_log(
                    interaction.guild,
                    "عقوبة",
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

            await interaction.response.send_message("تم ✅", ephemeral=True)

        except Exception as e:
            await auto_fix(e, interaction.guild)
            await interaction.response.send_message("خطأ ❌", ephemeral=True)

class PunishView(discord.ui.View):
    def __init__(self, member):
        super().__init__(timeout=None)
        self.add_item(PunishMenu(member))

# -------- COMMAND --------
@tree.command(name="taim", description="عقوبة عضو")
async def taim(interaction: discord.Interaction, user: discord.Member):
    try:
        await interaction.response.send_message(
            f"اختر العقوبة لـ {user.mention}",
            view=PunishView(user)
        )

        await send_log(
            interaction.guild,
            "استخدام أمر",
            f"{interaction.user.mention} ➜ {user.mention}"
        )

    except Exception as e:
        await auto_fix(e, interaction.guild)

# -------- READY --------
@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")

    try:
        await tree.sync()
    except Exception as e:
        await auto_fix(e)

    client.loop.create_task(safe_loop(check_roles))

client.run(TOKEN)
