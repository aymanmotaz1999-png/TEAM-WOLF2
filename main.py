import discord
from discord.ext import commands
from discord import app_commands
import os
import asyncio
import time
import json
from datetime import timedelta

TOKEN = os.getenv("TOKEN")
LOG_CHANNEL_ID = 1483891442920456263
DATA_FILE = "punishments.json"

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ============================
# تحميل / حفظ البيانات
# ============================
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

data_store = load_data()

# ============================
ROLES = {
    "تحذير اول": {"id": 1475095531389714604, "duration": 5*24*3600},
    "تحذير تاني": {"id": 1475097777104097545, "duration": 7*24*3600},
    "تحذير ثالث": {"id": 1475098153421377567, "duration": 14*24*3600},
    "انذار دسكورد اول": {"id": 1473015121906368715, "duration": 7*24*3600},
    "انذار دسكورد ثاني": {"id": 1473015122753749012, "duration": 14*24*3600},
    "تايم اوت": {"id": 1473015129019908232, "duration": 7*24*3600}
}

PUNISHMENTS = {
    "قذف": ["انذار دسكورد اول", "انذار دسكورد ثاني", "تايم اوت"],
    "سب": ["تحذير اول", "تحذير تاني"],
    "تسحيب": ["باند نهائي"],
    "تسحيب بين الرومات": ["انذار دسكورد اول", "انذار دسكورد ثاني"],
}

ALLOWED_ROLES = [1473015044643094643, 1473015048443269160]

def has_permission(member):
    return any(role.id in ALLOWED_ROLES for role in member.roles)

# ============================
@bot.event
async def on_ready():
    print(f"Bot Online: {bot.user}")
    await bot.tree.sync()
    asyncio.create_task(load_timers())

# ============================
# استرجاع التايمرات بعد إعادة التشغيل
# ============================
async def load_timers():
    await bot.wait_until_ready()

    while True:
        now = time.time()
        for key, value in list(data_store.items()):
            user_id, role_id = map(int, key.split("-"))
            if now >= value["end"]:
                guild = bot.guilds[0]
                member = guild.get_member(user_id)
                role = guild.get_role(role_id)

                if member and role:
                    try:
                        await member.remove_roles(role)
                    except:
                        pass

                data_store.pop(key)
                save_data(data_store)

        await asyncio.sleep(30)

# ============================
# إزالة رتبة مع حفظ
# ============================
async def remove_role_after(member, role, delay):
    end_time = time.time() + delay
    key = f"{member.id}-{role.id}"

    data_store[key] = {"end": end_time}
    save_data(data_store)

    await asyncio.sleep(delay)

    try:
        await member.remove_roles(role)
    except Exception as e:
        print(e)

    data_store.pop(key, None)
    save_data(data_store)

# ============================
class PunishmentView(discord.ui.View):
    def __init__(self, target):
        super().__init__(timeout=None)
        self.target = target

    @discord.ui.select(
        placeholder="اختر العقوبة",
        options=[discord.SelectOption(label=x) for x in PUNISHMENTS.keys()]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):

        if not has_permission(interaction.user):
            await interaction.response.send_message("❌ ليس لديك صلاحية", ephemeral=True)
            return

        choice = select.values[0]
        log_channel = bot.get_channel(LOG_CHANNEL_ID)

        for role_name in PUNISHMENTS[choice]:

            if role_name == "باند نهائي":
                await self.target.ban(reason=choice)
                continue

            role_data = ROLES.get(role_name)
            if not role_data:
                continue

            role = interaction.guild.get_role(role_data["id"])

            if role:
                await self.target.add_roles(role)

                asyncio.create_task(
                    remove_role_after(self.target, role, role_data["duration"])
                )

        # 📩 DM
        try:
            await self.target.send(f"⚠️ تم معاقبتك: {choice}")
        except:
            pass

        # 📋 Embed Log
        if log_channel:
            embed = discord.Embed(
                title="⚠️ عقوبة جديدة",
                color=discord.Color.red()
            )
            embed.add_field(name="المشرف", value=interaction.user.mention)
            embed.add_field(name="العضو", value=self.target.mention)
            embed.add_field(name="العقوبة", value=choice)

            await log_channel.send(embed=embed)

        await interaction.response.send_message("✅ تم التنفيذ", ephemeral=True)

# ============================
@bot.tree.command(name="عقوبة")
async def punish(interaction: discord.Interaction, member: discord.Member):

    if not has_permission(interaction.user):
        await interaction.response.send_message("❌ ليس لديك صلاحية", ephemeral=True)
        return

    await interaction.response.send_message(
        "اختر العقوبة:",
        view=PunishmentView(member),
        ephemeral=True
    )

# ============================
# فك العقوبة
# ============================
@bot.tree.command(name="فك")
async def unpunish(interaction: discord.Interaction, member: discord.Member):

    if not has_permission(interaction.user):
        return await interaction.response.send_message("❌ ليس لديك صلاحية", ephemeral=True)

    removed = False

    for role_name, data in ROLES.items():
        role = interaction.guild.get_role(data["id"])
        if role in member.roles:
            await member.remove_roles(role)
            removed = True

    if removed:
        await interaction.response.send_message("✅ تم فك العقوبات", ephemeral=True)
    else:
        await interaction.response.send_message("ℹ️ لا يوجد عقوبات", ephemeral=True)

# ============================
bot.run(TOKEN)
