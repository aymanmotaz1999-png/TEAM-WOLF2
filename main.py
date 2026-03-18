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
    try:
        with open("data.json", "r") as f:
            return json.load(f)
    except:
        return []

def save_data(data):
    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)

# -------- LOG --------
async def log(guild, msg):
    try:
        ch = guild.get_channel(LOG_CHANNEL_ID)
        if ch:
            await ch.send(msg)
    except:
        pass

# -------- ERROR LOGGER --------
async def log_error(guild, error):
    try:
        ch = guild.get_channel(LOG_CHANNEL_ID)
        if ch:
            await ch.send(f"❌ Error:\n```{error}```")
    except:
        pass

# -------- AUTO REMOVE --------
async def auto_remove():
    await client.wait_until_ready()

    while True:
        try:
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

        except Exception as e:
            print("AUTO ERROR:", e)

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
            # -------- CHECKS --------
            if not interaction.guild:
                return await interaction.response.send_message("❌ داخل السيرفر فقط", ephemeral=True)

            if not interaction.user.guild_permissions.administrator:
                return await interaction.response.send_message("❌ ما عندك صلاحية", ephemeral=True)

            if self.member == interaction.user:
                return await interaction.response.send_message("❌ ما تقدر تعاقب نفسك", ephemeral=True)

            if self.member.top_role >= interaction.user.top_role:
                return await interaction.response.send_message("❌ ما تقدر تعاقب عضو أعلى منك", ephemeral=True)

            # -------- ROLE IDS --------
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
                    await interaction.followup.send(f"❌ الرتبة {role_key} غير موجودة", ephemeral=True)
                    return

                await self.member.add_roles(role)

                if role_key in durations:
                    data = load_data()
                    data.append({
                        "user": self.member.id,
                        "role": role.id,
                        "guild": interaction.guild.id,
                        "end": int(time.time()) + durations[role_key]
                    })
                    save_data(data)

            v = self.values[0]

            # -------- ACTIONS --------
            if v == "1":
                await give("d1")
                await give("d2")
                await self.member.timeout(discord.utils.utcnow() + timedelta(days=7))

            elif v == "2":
                await give("warn1")
                await give("warn2")

            elif v == "3":
                await self.member.kick()

            elif v == "4":
                await give("warn1")
                await give("warn2")

            elif v == "5":
                await give("demote")

            await log(interaction.guild, f"⚠️ {interaction.user.mention} ➜ {self.member.mention}")
            await interaction.response.send_message("✅ تم التنفيذ", ephemeral=True)

        except discord.Forbidden:
            await interaction.response.send_message("❌ البوت ما عنده صلاحيات", ephemeral=True)

        except discord.HTTPException:
            await interaction.response.send_message("❌ خطأ في ديسكورد", ephemeral=True)

        except Exception as e:
            await log_error(interaction.guild, e)
            await interaction.response.send_message("❌ خطأ غير متوقع", ephemeral=True)

# -------- VIEW --------
class View(discord.ui.View):
    def __init__(self, member):
        super().__init__(timeout=None)
        self.add_item(Menu(member))

# -------- COMMAND --------
@tree.command(name="taim", description="معاقبة عضو")
async def taim(interaction: discord.Interaction, user: discord.Member):
    try:
        await interaction.response.send_message(
            f"اختر العقوبة لـ {user.mention}",
            view=View(user)
        )
    except Exception as e:
        await log_error(interaction.guild, e)

# -------- READY --------
@client.event
async def on_ready():
    print(f"🔥 {client.user} ONLINE")
    await tree.sync()
    client.loop.create_task(auto_remove())

client.run(TOKEN)
