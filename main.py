const { Client, GatewayIntentBits, ActionRowBuilder, StringSelectMenuBuilder, PermissionsBitField } = require('discord.js');

const client = new Client({
  intents: [GatewayIntentBits.Guilds, GatewayIntentBits.GuildMembers, GatewayIntentBits.GuildVoiceStates]
});

const LOG_CHANNEL = "1483891442920456263";

// IDs
const roles = {
  warn1: "1475095531389714604",
  warn2: "1475097777104097545",
  warn3: "1475098153421377567",
  disc1: "1473015121906368715",
  disc2: "1473015122753749012",
  timeoutRole: "1473015129019908232"
};

// مدد العقوبات (بالملي ثانية)
const durations = {
  warn1: 5 * 24 * 60 * 60 * 1000,
  warn2: 7 * 24 * 60 * 60 * 1000,
  warn3: 14 * 24 * 60 * 60 * 1000,
  disc1: 7 * 24 * 60 * 60 * 1000,
  disc2: 14 * 24 * 60 * 60 * 1000,
  timeout: 7 * 24 * 60 * 60 * 1000
};

// إزالة الرتبة بعد مدة
function addTimedRole(member, roleId, time) {
  member.roles.add(roleId);
  setTimeout(() => {
    member.roles.remove(roleId);
  }, time);
}

client.on("interactionCreate", async (interaction) => {
  if (!interaction.isChatInputCommand()) return;

  if (interaction.commandName === "عقوبة") {
    const user = interaction.options.getUser("user");

    const menu = new StringSelectMenuBuilder()
      .setCustomId(`punish_${user.id}`)
      .setPlaceholder("اختر نوع العقوبة ⚖️")
      .addOptions([
        { label: "🚫 القذف", value: "qazf", description: "انذار دسكورد + تايم اوت" },
        { label: "🗣️ السب", value: "sab", description: "تحذيرات" },
        { label: "⛔ تسحيب", value: "ban", description: "باند نهائي" },
        { label: "🔁 تسحيب متكرر", value: "repeat", description: "انذارات دسكورد" },
        { label: "🛠️ إساءة استخدام الإدارة", value: "abuse", description: "كسر رتبة" }
      ]);

    const row = new ActionRowBuilder().addComponents(menu);

    await interaction.reply({
      content: `اختر العقوبة لـ ${user}`,
      components: [row]
    });
  }
});

// عند اختيار العقوبة
client.on("interactionCreate", async (interaction) => {
  if (!interaction.isStringSelectMenu()) return;

  const userId = interaction.customId.split("_")[1];
  const member = await interaction.guild.members.fetch(userId);

  const logChannel = interaction.guild.channels.cache.get(LOG_CHANNEL);

  let logMsg = "";

  switch (interaction.values[0]) {
    case "qazf":
      addTimedRole(member, roles.disc1, durations.disc1);
      setTimeout(() => {
        addTimedRole(member, roles.disc2, durations.disc2);
      }, 1000);

      member.roles.add(roles.timeoutRole);
      member.timeout(7 * 24 * 60 * 60 * 1000);

      logMsg = `🚫 تم معاقبة ${member} بسبب القذف`;
      break;

    case "sab":
      addTimedRole(member, roles.warn1, durations.warn1);
      setTimeout(() => {
        addTimedRole(member, roles.warn2, durations.warn2);
      }, 1000);

      logMsg = `🗣️ تم إعطاء تحذيرات لـ ${member}`;
      break;

    case "ban":
      await member.ban();
      logMsg = `⛔ تم باند ${member}`;
      break;

    case "repeat":
      addTimedRole(member, roles.disc1, durations.disc1);
      setTimeout(() => {
        addTimedRole(member, roles.disc2, durations.disc2);
      }, 1000);

      logMsg = `🔁 تسحيب متكرر ${member}`;
      break;

    case "abuse":
      member.roles.set([]);
      logMsg = `🛠️ تم كسر رتبة ${member}`;
      break;
  }

  await interaction.reply({ content: "✅ تم تنفيذ العقوبة", ephemeral: true });

  logChannel.send(logMsg);
});

// تايم أوت تلقائي عند الميوت/دفن
client.on("voiceStateUpdate", async (oldState, newState) => {
  if (!newState.member.permissions.has(PermissionsBitField.Flags.Administrator)) return;

  if (oldState.serverMute !== newState.serverMute || oldState.serverDeaf !== newState.serverDeaf) {
    newState.member.timeout(5 * 60 * 1000); // 5 دقائق
  }
});

client.login("TOKEN_HERE");
