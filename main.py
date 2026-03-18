const {
  Client,
  GatewayIntentBits,
  ActionRowBuilder,
  StringSelectMenuBuilder,
  SlashCommandBuilder
} = require('discord.js');

const fs = require('fs');

const client = new Client({
  intents: [GatewayIntentBits.Guilds, GatewayIntentBits.GuildMembers]
});

const TOKEN = "YOUR_BOT_TOKEN";

// 📁 تحميل البيانات
function loadData() {
  return JSON.parse(fs.readFileSync('./data.json'));
}

// 💾 حفظ البيانات
function saveData(data) {
  fs.writeFileSync('./data.json', JSON.stringify(data, null, 2));
}

// 🟢 عند تشغيل البوت
client.once('ready', () => {
  console.log(`✅ Logged in as ${client.user.tag}`);

  // فحص كل 10 ثواني لإزالة الرتب المنتهية
  setInterval(async () => {
    let data = loadData();
    const now = Date.now();

    for (let i = 0; i < data.length; i++) {
      if (now >= data[i].endTime) {
        try {
          const guild = await client.guilds.fetch(data[i].guildId);
          const member = await guild.members.fetch(data[i].userId);

          await member.roles.remove(data[i].roleId);

          console.log(`❌ تم إزالة الرتبة من ${member.user.tag}`);
        } catch (err) {
          console.log(err);
        }

        data.splice(i, 1);
        i--;
      }
    }

    saveData(data);
  }, 10000);
});


// 🟢 أمر /taim
client.on('interactionCreate', async interaction => {

  if (interaction.isChatInputCommand()) {
    if (interaction.commandName === 'taim') {

      const member = interaction.options.getMember('user');

      const menu = new StringSelectMenuBuilder()
        .setCustomId(`punish_${member.id}`)
        .setPlaceholder('اختر نوع المخالفة')
        .addOptions([
          { label: 'القذف', value: 'qathf' },
          { label: 'السب', value: 'sab' },
          { label: 'تسحيب', value: 'ban' },
          { label: 'تسحيب متكرر', value: 'drag_repeat' },
          { label: 'سوء استخدام الإدارة', value: 'abuse' }
        ]);

      const row = new ActionRowBuilder().addComponents(menu);

      await interaction.reply({
        content: `📋 اختر العقوبة لـ ${member}`,
        components: [row]
      });
    }
  }

  // 🎯 عند اختيار من القائمة
  if (interaction.isStringSelectMenu()) {

    const [type, userId] = interaction.customId.split('_');
    if (type !== 'punish') return;

    const member = await interaction.guild.members.fetch(userId);

    let roleId;
    let duration;

    // 🔴 غير IDs حسب الرتب عندك
    const roles = {
      warn1: "ROLE_ID_WARN1",
      warn2: "ROLE_ID_WARN2",
      warn3: "ROLE_ID_WARN3",
      dis1: "ROLE_ID_DIS1",
      dis2: "ROLE_ID_DIS2",
      demote: "ROLE_ID_DEMOTE"
    };

    switch (interaction.values[0]) {

      case 'qathf': // القذف
        roleId = roles.dis1;
        duration = 7 * 24 * 60 * 60 * 1000;
        break;

      case 'sab': // السب
        roleId = roles.warn1;
        duration = 5 * 24 * 60 * 60 * 1000;
        break;

      case 'ban': // تسحيب
        await member.ban();
        return interaction.reply('🚫 تم الباند النهائي');

      case 'drag_repeat': // تسحيب متكرر
        roleId = roles.dis1;
        duration = 7 * 24 * 60 * 60 * 1000;
        break;

      case 'abuse': // سوء استخدام
        roleId = roles.demote;
        duration = 0;
        break;
    }

    if (roleId) {
      await member.roles.add(roleId);
    }

    await interaction.reply(`✅ تم إعطاء العقوبة لـ ${member}`);

    // ⏳ تخزين العقوبة
    if (duration > 0) {
      let data = loadData();

      data.push({
        userId: member.id,
        roleId: roleId,
        guildId: interaction.guild.id,
        endTime: Date.now() + duration
      });

      saveData(data);
    }
  }
});

client.login(TOKEN);
