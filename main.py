import discord
from discord import app_commands
import json
import time
import asyncio

intents = discord.Intents.default()
intents.members = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# 📁 تحميل البيانات
def load_data():
    try:
        with open("data.json", "r") as f:
            return json.load(f)
    except:
        return []

# 💾 حفظ البيانات
def save_data(data):
    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)

# ⏳ فحص العقوبات
async def check_roles():
    await client.wait_until_ready()
    while not client.is_closed():
        data = load_data()
        now = int(time.time())

        for entry in data[:]:
            if now >= entry["end_time"]:
                guild = client.get_guild(entry["guild_id"])
                if guild:
                    member = guild.get_member(entry["user_id"])
                    if member:
                        role = guild.get_role(entry["role_id"])
                        if role:
                            try:
                                await member.remove_roles(role)
                                print(f"تم إزالة الرتبة من {member}")
                            except:
                                pass

                data.remove(entry)
                save_data(data)

        await asyncio.sleep(10)

# 🟢 عند تشغيل البوت
@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")
    await tree.sync()
    client.loop.create_task(check_roles())

# 🎯 قائمة العقوبات
class PunishMenu(discord.ui.Select):
    def __init__(self, member: discord.Member):
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
        value = self.values[0]

        # 🔴 غير IDs حسب سيرفرك
        roles = {
            "warn1": 123456789,
            "warn2": 123456789,
            "warn3": 123456789,
            "dis1": 123456789,
            "dis2": 123456789,
            "demote": 123456789
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
            await interaction.response.send_message("🚫 تم الباند", ephemeral=True)
            return

        elif value == "drag":
            role_id = roles["dis1"]
            duration = 7 * 24 * 60 * 60

        elif value == "abuse":
            role_id = roles["demote"]

        if role_id:
            role = interaction.guild.get_role(role_id)
            await self.member.add_roles(role)

        # 💾 تخزين العقوبة
        if duration > 0:
            data = load_data()
            data.append({
                "user_id": self.member.id,
                "role_id": role_id,
                "guild_id": interaction.guild.id,
                "end_time": int(time.time()) + duration
            })
            save_data(data)

        await interaction.response.send_message(f"✅ تم معاقبة {self.member.mention}", ephemeral=True)

# 🧾 واجهة
class PunishView(discord.ui.View):
    def __init__(self, member):
        super().__init__()
        self.add_item(PunishMenu(member))

# 🟢 أمر /taim
@tree.command(name="taim", description="إعطاء عقوبة")
@app_commands.describe(user="اختار العضو")
async def taim(interaction: discord.Interaction, user: discord.Member):
    await interaction.response.send_message(
        f"📋 اختر العقوبة لـ {user.mention}",
        view=PunishView(user)
    )

client.run("YOUR_BOT_TOKEN")
