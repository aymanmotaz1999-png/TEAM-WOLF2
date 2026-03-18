const { 
  Client, 
  GatewayIntentBits, 
  EmbedBuilder, 
  ActionRowBuilder, 
  StringSelectMenuBuilder, 
  PermissionsBitField 
} = require('discord.js');

const client = new Client({
  intents: [GatewayIntentBits.Guilds, GatewayIntentBits.GuildMembers]
});

const TOKEN = "PUT_YOUR_TOKEN_HERE";

// ايدي روم اللوق
const LOG_CHANNEL_ID = "1483891442920456263";

// ايدي الرتب (حط ايديات الرتب من سيرفرك)
const roles = {
  warn1: "ROLE_ID_1",
  warn2: "ROLE_ID_2",
  warn3: "ROLE_ID_3",
  dis1: "ROLE_ID_4",
  dis2: "ROLE_ID_5"
};

// مدد العقوبات (بالملي ثانية)
const durations = {
  warn1: 5 * 24 * 60 * 60 * 1000,
  warn2: 7 * 24 * 60 * 60 * 1000,
  warn3: 14 * 24 * 60 * 60 * 1000,
  dis1: 7 * 24 * 60 * 60 * 1000,
  dis2: 14 * 24 * 60 * 60 * 1000
};

client.once("ready", () => {
  console.log(`Logged in as ${client.user.tag}`);
});

client.on("interactionCreate", async (interaction) => {

  // أمر /تايم
  if (interaction.isChatInputCommand()) {
    if (interaction.commandName === "تايم") {

      const member = interaction.options.getMember("user");

      const embed = new EmbedBuilder()
        .setTitle("📋 نظام العقوبات")
        .setDescription("اختر نوع المخالفة")
        .setImage("attachment://image.png"); // الصورة

      const menu = new StringSelectMenuBuilder()
        .setCustomId("punishment")
        .setPlaceholder("اختر العقوبة")
        .addOptions([
          {
            label: "القذف",
            value: "1",
            description: "انذار دسكورد اول + اندار ثاني + تايم اوت اسبوع"
          },
          {
            label: "السب",
            value: "2",
            description: "تحذير اول + تحذير ثاني"
          },
          {
            label: "تسحيب",
            value: "3",
            description: "باند نهائي"
          },
          {
            label: "تسحيب متكرر",
            value: "4",
            description: "تحذير + انذار"
          },
          {
            label: "استعمال ادارة",
            value: "5",
            description: "كسر رتبة"
          }
        ]);

      const row = new ActionRowBuilder().addComponents(menu);

      await interaction.reply({
        embeds: [embed],
        components: [row],
        files: ["./image.png"] // حط الصورة بنفس اسم الملف
      });

      interaction.targetMember = member;
    }
  }

  // عند اختيار من القائمة
  if (interaction.isStringSelectMenu()) {

    const member = interaction.message.interaction?.options?.getMember("user");
    const logChannel = interaction.guild.channels.cache.get(LOG_CHANNEL_ID);

    let logMsg = "";

    switch (interaction.values[0]) {

      case "1":
        await member.roles.add(roles.dis1);
        setTimeout(() => member.roles.remove(roles.dis1), durations.dis1);

        logMsg = `تم معاقبة ${member} بسبب القذف`;
        break;

      case "2":
        await member.roles.add(roles.warn1);
        setTimeout(() => member.roles.remove(roles.warn1), durations.warn1);

        logMsg = `تم تحذير ${member}`;
        break;

      case "3":
        await member.ban();
        logMsg = `تم باند ${member}`;
        break;

      case "4":
        await member.roles.add(roles.warn1);
        setTimeout(() => member.roles.remove(roles.warn1), durations.warn1);

        logMsg = `تحذير بسبب التسحيب المتكرر`;
        break;

      case "5":
        // كسر رتبة (مثال: إزالة أعلى رتبة)
        const highest = member.roles.highest;
        await member.roles.remove(highest);

        logMsg = `تم كسر رتبة ${member}`;
        break;
    }

    await interaction.reply({ content: "✅ تم تنفيذ العقوبة", ephemeral: true });

    if (logChannel) {
      logChannel.send(`📜 ${logMsg} | بواسطة ${interaction.user}`);
    }
  }
});

client.login(TOKEN);
