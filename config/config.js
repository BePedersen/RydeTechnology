const { Client, GatewayIntentBits } = require('discord.js');


// Destructure the intents we want from GatewayIntentBits
const {
  DirectMessages,
  GuildMessages,
  Guilds,
  MessageContent,
} = GatewayIntentBits;

// Create an array of bot intents
const botIntents = [
  DirectMessages,
  GuildMessages,
  Guilds,
  MessageContent,
];

const commands = {
    getName: 'get-name',
    hi: 'hi',
    plan: 'plan',

  };

const prefix = '!';

// Export the bot intents for use in other files
module.exports = { commands, prefix, botIntents };
