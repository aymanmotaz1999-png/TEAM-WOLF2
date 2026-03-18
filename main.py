import discord
from discord.ext import commands, tasks
import os, json, time, traceback
from datetime import datetime, timedelta, timezone

TOKEN = os.getenv("TOKEN")
LOG_CHANNEL = 1483891442920456263

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# -------- DATABASE --------
def load():
    try:
        with open("data.json") as f:
            return json.load(f)
    except:
        return {"punishments": [], "levels": {}}

def save(data):
    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)

data = load()

# -------- LOG --------
async def log(guild, msg):
    ch = guild.get_channel(LOG_CHANNEL)
    if ch:
        await ch.send(msg)

# -------- READY --------
@bot.event
async def on_ready():
    print(f"🔥 {bot.user} ONLINE")
    if not auto_remove.is_running():
        auto_remove.start()

# -------- ERROR --------
@bot.event
async def on_command_error(ctx, error):
    print("".join(traceback.format_exception(type(error), error, error.__traceback__)))
    await ctx.send(f"❌ {error}")

# -------- LEVEL --------
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    uid = str(message.author.id)

    if uid not in data["levels"]:
        data["levels"][uid] = {"xp": 0, "level": 1}

    data["levels"][uid]["xp"] += 5

    if data["levels"][uid]["xp"] >= data["levels"][uid]["level"] * 50:
        data["levels"][uid]["xp"] = 0
        data["levels"][uid]["level"] += 1
        await message.channel.send(f"🎉 {message.author.mention} لفّل!")

    save(data)

    if len(message.content) > 200:
        try:
            await message.delete()
        except:
            pass

    await bot.process_commands(message)

# -------- AUTO REMOVE --------
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

# -------- MENU --------
class PunishMenu(discord.ui.Select):
    def __init__(self, member):
        self.member = member

        options = [
            discord.SelectOption(label="🚫 القذف", value="1"),
            discord.SelectOption(label="🗣️ السب", value="2"),
            discord.SelectOption(label="👢 طرد", value="3"),
            discord.SelectOption(label="🔁 تكرار", value="4"),
            discord.SelectOption(label="🛠️ كسر رتبة", value="5"),
        ]

        super().__init__(placeholder="اختر العقوبة", options=options)

    async def callback(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ لا تملك صلاحية", ephemeral=True)

        if self.member.top_role >= interaction.user.top_role:
            return await interaction.response.send_message("❌ لا يمكنك معاقبة هذا العضو", ephemeral=True)

        roles = {
            "warn1": 111111111111,
            "warn2": 222222222222,
            "demote": 333333333333
        }

        durations = {
            "warn1": 5*86400,
            "warn2": 7*86400
        }

        async def give(role_key):
            role = interaction.guild.get_role(roles[role_key])
            if not role:
                await interaction.followup.send("❌ الرتبة غير موجودة", ephemeral=True)
                return False

            try:
                await self.member.add_roles(role)
            except:
                await interaction.followup.send("❌ فشل إضافة الرتبة", ephemeral=True)
                return False

            if role_key in durations:
                data["punishments"].append({
                    "user": self.member.id,
                    "role": role.id,
                    "guild": interaction.guild.id,
                    "end": int(time.time()) + durations[role_key]
                })

            return True

        await interaction.response.defer(ephemeral=True)

        v = self.values[0]

        try:
            if v == "1":
                if await give("warn1"):
                    await self.member.timeout(datetime.now(timezone.utc) + timedelta(days=7))

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

            save(data)

            await log(interaction.guild, f"⚠️ {interaction.user} ➜ {self.member}")
            await interaction.followup.send("✅ تم تنفيذ العقوبة", ephemeral=True)

        except Exception as e:
            print(e)
            await interaction.followup.send("❌ خطأ أثناء التنفيذ", ephemeral=True)

# -------- VIEW --------
class PunishView(discord.ui.View):
    def __init__(self, member):
        super().__init__(timeout=60)
        self.add_item(PunishMenu(member))

# -------- COMMAND --------
@bot.command()
async def taim(ctx, member: discord.Member):
    await ctx.send(f"⚖️ اختر العقوبة لـ {member.mention}", view=PunishView(member))

# -------- RUN --------
bot.run(TOKEN)
