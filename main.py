import discord
from discord.ext import commands, tasks
import os, json, time
from datetime import datetime, timedelta, timezone

TOKEN = os.getenv("TOKEN")
LOG_CHANNEL = 1483891442920456263

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ---------- DATABASE ----------
def load():
    try:
        with open("data.json") as f:
            return json.load(f)
    except:
        return {"punishments": []}

def save(data):
    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)

data = load()

# ---------- LOG ----------
async def log(guild, msg):
    ch = guild.get_channel(LOG_CHANNEL)
    if ch:
        await ch.send(msg)

# ---------- READY ----------
@bot.event
async def on_ready():
    print(f"✅ {bot.user} ONLINE")
    if not auto_remove.is_running():
        auto_remove.start()

# ---------- AUTO REMOVE ----------
@tasks.loop(seconds=10)
async def auto_remove():
    now = int(time.time())

    for p in data["punishments"][:]:
        if now >= p["end"]:
            guild = bot.get_guild(p["guild"])
            if guild:
                member = guild.get_member(p["user"])
                role = guild.get_role(p["role"])

                if member and role:
                    try:
                        await member.remove_roles(role)
                        await log(guild, f"✅ انتهت العقوبة: {member.mention}")
                    except:
                        pass

            data["punishments"].remove(p)
            save(data)

# ---------- MENU ----------
class PunishMenu(discord.ui.Select):
    def __init__(self, member):
        self.member = member

        options = [
            discord.SelectOption(label="🚫 إنذار", value="1"),
            discord.SelectOption(label="🗣️ إنذارين", value="2"),
            discord.SelectOption(label="👢 طرد", value="3"),
        ]

        super().__init__(placeholder="اختر العقوبة", options=options)

    async def callback(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ لا تملك صلاحية", ephemeral=True)

        if self.member.top_role >= interaction.user.top_role:
            return await interaction.response.send_message("❌ لا يمكنك معاقبته", ephemeral=True)

        roles = {
            "warn": 111111111111,  # حط ID صحيح
        }

        durations = {
            "warn": 3 * 86400
        }

        async def give(role_key):
            role = interaction.guild.get_role(roles[role_key])
            if not role:
                return False

            await self.member.add_roles(role)

            data["punishments"].append({
                "user": self.member.id,
                "role": role.id,
                "guild": interaction.guild.id,
                "end": int(time.time()) + durations[role_key]
            })
            return True

        await interaction.response.defer(ephemeral=True)

        try:
            v = self.values[0]

            if v == "1":
                await give("warn")

            elif v == "2":
                await give("warn")
                await give("warn")

            elif v == "3":
                await self.member.kick()

            save(data)

            await log(interaction.guild, f"⚠️ {interaction.user} ➜ {self.member}")
            await interaction.followup.send("✅ تم التنفيذ", ephemeral=True)

        except:
            await interaction.followup.send("❌ خطأ", ephemeral=True)

# ---------- VIEW ----------
class PunishView(discord.ui.View):
    def __init__(self, member):
        super().__init__(timeout=60)
        self.add_item(PunishMenu(member))

# ---------- COMMAND ----------
@bot.command()
async def taim(ctx, member: discord.Member):
    await ctx.send(f"⚖️ اختر العقوبة لـ {member.mention}", view=PunishView(member))

# ---------- RUN ----------
bot.run(TOKEN)
