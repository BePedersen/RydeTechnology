const { 
    Client, 
    GatewayIntentBits, 
    StringSelectMenuBuilder, 
    ActionRowBuilder 
} = require('discord.js');

const fs = require('fs');
const csv = require('csv-parser');

const client = new Client({
    intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.MessageContent,
        GatewayIntentBits.DirectMessages,
    ],
});

const randomWord = ['redder','fikser','støvsuger','ordner','steller'];

const userSelections = {};

async function readCSV(filePath) {
    return new Promise((resolve, reject) => {
        const options = [];
        fs.createReadStream(filePath)
            .pipe(csv())
            .on('data', (row) => {
                options.push({
                    label: row.label, 
                    value: row.value,
                    phone: row.phone || 'Not provided',
                    username: row.username || 'Not provided',
                });
            })
            .on('end', () => resolve(options))
            .on('error', (error) => reject(error));
    });
}

function getPeopleDropdown(options) {
    return new ActionRowBuilder().addComponents(
        new StringSelectMenuBuilder()
            .setCustomId('personSelection')
            .setPlaceholder('Select people')
            .setMinValues(1)
            .setMaxValues(options.length)
            .addOptions(options)
    );
}

function getPlaceDropdown(placesOptions, placeholder) {
    return new ActionRowBuilder().addComponents(
        new StringSelectMenuBuilder()
            .setCustomId('placeSelection')
            .setPlaceholder(placeholder)
            .setMinValues(1)
            .setMaxValues(1)
            .addOptions(placesOptions)
    );
}

function getPercentageDropdown() {
    return new ActionRowBuilder().addComponents(
        new StringSelectMenuBuilder()
            .setCustomId('percentageSelection')
            .setPlaceholder('Select a percentage')
            .setMinValues(1)
            .setMaxValues(1)
            .addOptions(
                { label: '30%', value: '30' },
                { label: '35%', value: '35' },
                { label: '40%', value: '40' },
                { label: '45%', value: '45' }
            )
    );
}

// Function to get goal percentage
function getGoalPercentage() {
    return new ActionRowBuilder().addComponents(
        new StringSelectMenuBuilder()
            .setCustomId('goalPercentageSelection')
            .setPlaceholder('Select goal completion percentage')
            .setMinValues(1)
            .setMaxValues(1)
            .addOptions(
                { label: '85%', value: '85' },
                { label: '86%', value: '86' },
                { label: '87%', value: '87' },
                { label: '88%', value: '88' },
                { label: '89%', value: '89' },
                { label: '90%', value: '90' },
                { label: '91%', value: '91' },
                { label: '92%', value: '92' },
                { label: '93%', value: '93' },
                { label: '94%', value: '94' },
                { label: '95%', value: '95' },
                { label: '96', value: '96' },
            )
    );
}

// Function to get inactive days
function getDaysInactive() {
    return new ActionRowBuilder().addComponents(
        new StringSelectMenuBuilder()
            .setCustomId('daysInactiveSelection')
            .setPlaceholder('Select how many days inactive')
            .setMinValues(1)
            .setMaxValues(1)
            .addOptions(
                { label: '1 day', value: '1' },
                { label: '2 days', value: '2' },
                { label: '3 days', value: '3' },
                { label: 'More than 3 days', value: 'More than 3 days' }
            )
    );
}

client.once('ready', () => {
    console.log(`Logged in as ${client.user.tag}`);
});

require('dotenv').config();
client.login(process.env.DISCORD_TOKEN);

client.on('messageCreate', async (msg) => {
    if (msg.content === '!opsplan' && !msg.author.bot) {
        try {
            const peopleOptions = await readCSV('./Deputy/people_on_shift.csv');
            const placesOptions = await readCSV('./Data/places.csv');

            // Initialize state for user selections
            userSelections[msg.author.id] = {
                people: [],
                places: [],
                placesOptions,
                peopleOptions, // Store peopleOptions here
                currentDriverIndex: 0,
                currentStep: 'selectPeople',
                percentage: null,
                comment: null,
                inactivePercentage: 0,
                daysInactive: 2, // Default to 2 days inactive if not provided
                goalPercentage: null, // Add goal percentage
            };

            const rowPerson = getPeopleDropdown(peopleOptions);
            await msg.reply({
                content: 'Please select the people you want to assign places to:',
                components: [rowPerson],
            });

        } catch (error) {
            console.error('Error in opsplan:', error);
            await msg.reply('There was an error processing your request. Please check the logs.');
        }
    } else if (
        userSelections[msg.author.id] &&
        userSelections[msg.author.id].currentStep === 'addComment'
    ) {
        // Capture comment
        userSelections[msg.author.id].comment = msg.content;

        const userState = userSelections[msg.author.id];
        const summaryMessage = 
            
            `🦍🦍🛴🛴 **Shift Plan** 🛴🛴🦍🦍\n\n` +
            `Skiftleder: ${msg.author.username}\n` +
            `\n **Goal** \n` + 
            `- Availability: 🎯 ${userState.goalPercentage ? userState.goalPercentage + "%" : "Not set"}\n\n` +  // Check if goalPercentage is set
            `🚦 **Team and Areas**:\n` +

            userState.places.map(({ person, place }) => {
                // Select a random word from the list using the already declared randomWord array
                const selectedWord = randomWord[Math.floor(Math.random() * randomWord.length)];
            
                // Find the corresponding username from the CSV data
                const personData = userState.peopleOptions.find(option => option.label === person);
            
                // Return the formatted string with the random word inserted
                return `- ${personData?.username || person} ${selectedWord} ${place}`;
            }).join('\n') +
            
            `\n\n📊 **Operational Notes**:\n` +
            `- **Inactivity**: 🔄 ${userState.percentage}% inactive for ** ${userState.daysInactive || 2} days**.\n` +
            `- **Clusters**: ${parseInt(userState.percentage) + 10}% in clusters.\n` +
            `- **Redeployment**: 📉 ${parseInt(userState.percentage) + 15}% on inactives.\n\n` +
            `🔒 **Container Codes**:\n` +
            `- Code: **1602**\n\n` +
            `🚨 **Important Reminders**:\n` +
            `- **Use the car** 🚗\n` +
            `- **Send routes** 🗺️\n` +
            `- Ensure **Good Quality Control (QC)**\n` +
            `- **Prioritize Superlows**\n` +
            `- If you receive a **nivel** issue, **fix it within an hour**.\n\n` +
            `📞 **Contact**:\n` +
            userState.places.map(({ person }) => {
                // Find the corresponding person from the CSV data
                const personData = userState.peopleOptions.find(option => option.label === person);
                return `• ${personData?.label}: ${personData?.phone || 'No phone'}`;
            }).join('\n') +
            `\n\n **Comment**:\n${userState.comment || 'No additional comment'}\n` +
            `\n\n 🪫🪫 **Battery Check** 🔋🔋 \n` +
            `Make sure you're charged up and ready to go!`;

        await msg.reply(summaryMessage);
        delete userSelections[msg.author.id]; // Clear user state after completion
    }
});



client.on('interactionCreate', async (interaction) => {
    if (!interaction.isStringSelectMenu()) return;

    const userId = interaction.user.id;
    const userState = userSelections[userId];
    const currentStep = userState.currentStep;

    if (currentStep === 'selectPeople' && interaction.customId === 'personSelection') {
        userState.people = interaction.values;
        userState.currentStep = 'selectPlace';

        const driver = userState.people[userState.currentDriverIndex];
        const rowPlace = getPlaceDropdown(
            userState.placesOptions,
            `Where should ${driver} drive?`
        );

        await interaction.update({
            content: null,
            components: [rowPlace],
        });

    } else if (currentStep === 'selectPlace' && interaction.customId === 'placeSelection') {
        const selectedDriver = userState.people[userState.currentDriverIndex];
        const selectedPlace = interaction.values[0];
        userState.places.push({ person: selectedDriver, place: selectedPlace });

        if (userState.currentDriverIndex < userState.people.length - 1) {
            userState.currentDriverIndex++;
            const nextDriver = userState.people[userState.currentDriverIndex];
            const rowPlace = getPlaceDropdown(
                userState.placesOptions,
                `Where should ${nextDriver} drive?`
            );

            await interaction.update({
                content: null,
                components: [rowPlace],
            });
        } else {
            userState.currentStep = 'selectPercentage';

            const rowPercentage = getPercentageDropdown();
            await interaction.update({
                content: `All drivers have been assigned places. Now, select a percentage:`,
                components: [rowPercentage],
            });
        }
    } else if (currentStep === 'selectPercentage' && interaction.customId === 'percentageSelection') {
        userState.percentage = interaction.values[0];
        userState.currentStep = 'selectGoalPercentage'; // New step for goal percentage

        const rowGoalPercentage = getGoalPercentage();
        await interaction.update({
            content: `You selected ${userState.percentage}%. Now, select the goal completion percentage:`,
            components: [rowGoalPercentage],
        });
    } else if (currentStep === 'selectGoalPercentage' && interaction.customId === 'goalPercentageSelection') {
        userState.goalPercentage = interaction.values[0];
        console.log("Goal Percentage Set: ", userState.goalPercentage); // Log this value
        userState.currentStep = 'selectDaysInactive'; // New step for inactive days
    
        const rowDaysInactive = getDaysInactive();
        await interaction.update({
            content: `You selected a goal percentage of ${userState.goalPercentage}%. Now, select how many days inactive:`,
            components: [rowDaysInactive],
        });
        
    } else if (currentStep === 'selectDaysInactive' && interaction.customId === 'daysInactiveSelection') {
        userState.daysInactive = interaction.values[0];
        userState.currentStep = 'addComment';

        await interaction.update({
            content: `You selected ${userState.daysInactive} days inactive. Please type a comment to finalize the shift plan:`,
            components: [],
        });
    }
});
