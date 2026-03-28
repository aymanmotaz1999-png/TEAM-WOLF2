import discord
from discord.ext import commands, tasks
from discord import app_commands
import os
import asyncio
import time

TOKEN = os.getenv("TOKEN")
LOG_CHANNEL_ID = 1483891442920456263  # قناة اللوج

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ============================
# الرتب والأوقات بالثواني
# ============================
ROLES = {
    "تحذير اول": {"id": 1475095531389714604, "duration": 5*24*3600},
    "تحذير تاني": {"id": 1475097777104097545, "duration": 7*24*3600},
    "تحذير ثالث": {"id": 1475098153421377567, "duration": 14*24*3600},
    "انذار دسكورد اول": {"id": 1473015121906368715, "duration": 7*24*3600},
    "انذار دسكورد ثاني": {"id": 1473015122753749012, "duration": 14*24*3600},
    "تايم اوت": {"id": 1473015129019908232, "duration": 7*24*3600}  # مثال، سيتم تايم اوت فعلي
}

# ============================
# خيارات العقوبة
# ============================
PUNISHMENTS = {
    "قذف": ["انذار دسكورد اول", "انذار دسكورد ثاني", "تايم اوت"],
    "سب": ["تحذير اول", "تحذير تاني"],
    "تسحيب": ["باند نهائي"],
    "تسحيب بين الرومات": ["انذار دسكورد اول", "انذار دسكورد ثاني"],
    "استعمال خصائص إدارة": ["كسر رتبة"]
}

# ============================
# قائمة المهام المؤقتة
# ============================
active_timers = {}

# ============================
# صلاحية الإدارة
# ============================
ALLOWED_ROLES = [1473015044643094643, 1473015048443269160]  # رتب المشرفين

def has_permission(member: discord.Member):
    return any(role.id in ALLOWED_ROLES for role in member.roles)

# ============================
# عند تشغيل البوت
# ============================
@bot.event
async def on_ready():
    print(f"Bot Online: {bot.user}")
    await bot.tree.sync()

# ============================
# أمر العقوبة
# ============================
class PunishmentView(discord.ui.View):
    def __init__(self, target: discord.Member):
        super().__init__(timeout=None)
        self.target = target

    @discord.ui.select(
        placeholder="اختر نوع العقوبة التي تريدها",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(label="قذف", description="انذار + تايم اوت"),
            discord.SelectOption(label="سب", description="تحذير اول + ثاني"),
            discord.SelectOption(label="تسحيب", description="باند نهائي"),
            discord.SelectOption(label="تسحيب بين الرومات", description="انذار اول + ثاني"),
            discord.SelectOption(label="استعمال خصائص إدارة", description="كسر رتبة")
        ]
    )
    async def select_callback(self, select: discord.ui.Select, interaction: discord.Interaction):
        if not has_permission(interaction.user):
            await interaction.response.send_message("❌ ليس لديك صلاحية.", ephemeral=True)
            return

        choice = select.values[0]
        roles_to_add = PUNISHMENTS.get(choice, [])
        log_channel = bot.get_channel(LOG_CHANNEL_ID)

        # منطق إضافة الرتب المؤقتة
        for role_name in roles_to_add:
            if role_name not in ROLES:
                continue
            role_id = ROLES[role_name]["id"]
            duration = ROLES[role_name]["duration"]
            role = interaction.guild.get_role(role_id)
            if role:
                await self.target.add_roles(role, reason=f"عقوبة {choice} من {interaction.user}")
                # تسجيل التوقيت للسحب التلقائي
                task = asyncio.create_task(remove_role_after(self.target, role, duration))
                active_timers[(self.target.id, role.id)] = task

        # تسجيل اللوج
        if log_channel:
            await log_channel.send(f"⚠️ {interaction.user} أعطى {self.target.mention} عقوبة: **{choice}**")

        await interaction.response.send_message(f"✅ تم تنفيذ العقوبة {choice} على {self.target.mention}", ephemeral=True)

async def remove_role_after(member: discord.Member, role: discord.Role, delay: int):
    await asyncio.sleep(delay)
    try:
        await member.remove_roles(role, reason="انتهت مدة العقوبة")
    except:
        pass
    # إزالة المهمة من القائمة
    active_timers.pop((member.id, role.id), None)

@bot.tree.command(name="عقوبة", description="اختر عقوبة لعضو")
@app_commands.describe(member="اختر العضو")
async def punishment_command(interaction: discord.Interaction, member: discord.Member):
    view = PunishmentView(member)
    embed = discord.Embed(title="اختر نوع العقوبة التي تريدها")
    embed.set_image(url="attachment://teamwolf.png")  # الصورة سترفق لاحقًا
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True, files=[discord.File("7c199688-170d-49c3-bf65-8247d8390099.png", filename="teamwolf.png")])

# ============================
# تايم اوت تلقائي للإدارة
# ============================
MUTE_ADMIN_ROLE_IDS = ALLOWED_ROLES  # رتب الإدارة
async def check_admin_actions():
    await bot.wait_until_ready()
    while not bot.is_closed():
        for guild in bot.guilds:
            for member in guild.members:
                if any(role.id in MUTE_ADMIN_ROLE_IDS for role in member.roles):
                    # هنا يمكن إضافة منطق كشف الميوت أو دفين
                    # مثال: إذا اكتشف أي سلوك مكرر أعطي تايم اوت 5 دقائق
                    pass
        await asyncio.sleep(60)  # كل دقيقة
bot.loop.create_task(check_admin_actions())

# ============================
# تايم اوت سبام الأعضاء
# ============================
SPAM_TIMEOUT = 180  # 3 دقائق
user_message_times = {}

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    now = time.time()
    user_id = message.author.id

    # رصد السبام
    timestamps = user_message_times.get(user_id, [])
    timestamps = [t for t in timestamps if now - t < 5]  # خلال 5 ثواني
    timestamps.append(now)
    user_message_times[user_id] = timestamps

    if len(timestamps) > 5:  # أكثر من 5 رسائل خلال 5 ثواني
        try:
            await message.author.timeout(duration=SPAM_TIMEOUT, reason="سبام")
        except:
            pass

    await bot.process_commands(message)

bot.run(TOKEN)
