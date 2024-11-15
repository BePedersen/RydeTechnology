const { 
    Client, 
    GatewayIntentBits, 
    StringSelectMenuBuilder, 
    StringSelectMenuOptionBuilder, 
    ActionRowBuilder,
} = require('discord.js');

const fs = require('fs');
const csv = require('csv-parser');

// Define an array of words
const actionWords = ["redder", "fikser", "ordner", "steller"];

// Function to get a random word from the array
function getRandomWord() {
    return actionWords[Math.floor(Math.random() * actionWords.length)];
}

const client = new Client({
    intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.MessageContent,
        GatewayIntentBits.DirectMessages,
    ],
});

// Temporary storage for selections
const userSelections = {};

// Function to read CSV files and return options
async function readCSV(filePath) {
    return new Promise((resolve, reject) => {
        const options = [];
        console.log(`Reading CSV from ${filePath}`); // Log the file path
        fs.createReadStream(filePath)
            .pipe(csv())
            .on('data', (row) => {
                console.log('Row read:', row); // Log each row read
                options.push({
                    label: row.label, 
                    value: row.value,
                    phone: row.phone || 'Not provided',  // Only add phone if it exists
                    username: row.username || 'Not provided'  // Add username with default if missing
                });
            })
            .on('end', () => {
                console.log('CSV reading completed.'); // Log when reading is done
                resolve(options);
            })
            .on('error', (error) => {
                console.error('Error reading CSV:', error); // Log the error
                reject(error);
            });
    });
}

client.once('ready', () => {
    console.log(`Logged in as ${client.user.tag}`);
});

require('dotenv').config();

client.login(process.env.DISCORD_TOKEN);

client.on('messageCreate', async (msg) => {
    if (msg.content === '!opsplan' && !msg.author.bot) {
        try {
            const peopleOptions = await readCSV('./Deputy/people_on_shift.csv'); // Path to your people CSV
            const placesOptions = await readCSV('./Data/places.csv'); // Path to your places CSV

            // Dropdown for selecting people
            const selectPerson = new StringSelectMenuBuilder()
                .setCustomId('personSelection')
                .setPlaceholder('Select people')
                .setMinValues(1)
                .setMaxValues(peopleOptions.length) // Set max choices to the length of peopleOptions
                .addOptions(peopleOptions);

            // Dropdown for selecting places
            const selectPlace = new StringSelectMenuBuilder()
                .setCustomId('placeSelection')
                .setPlaceholder('Select places')
                .setMinValues(1)
                .setMaxValues(placesOptions.length) // Set max choices to the length of placesOptions
                .addOptions(placesOptions);

            // Dropdown for selecting percentage (only one)
            const selectPercentage = new StringSelectMenuBuilder()
                .setCustomId('percentageSelection')
                .setPlaceholder('Select a percentage')
                .setMinValues(1) // Only allow one selection
                .setMaxValues(1)
                .addOptions(
                    new StringSelectMenuOptionBuilder().setLabel('30%').setValue('30'),
                    new StringSelectMenuOptionBuilder().setLabel('35%').setValue('35'),
                    new StringSelectMenuOptionBuilder().setLabel('40%').setValue('40'),
                    new StringSelectMenuOptionBuilder().setLabel('45%').setValue('45')
                );

            const selectGoalPercentage = new StringSelectMenuBuilder()
                .setCustomId('goalPercentageSelection')
                .setPlaceholder('Select a goal percentage')
                .setMinValues(1) // Only allow one selection
                .setMaxValues(1)
                .addOptions(
                    new StringSelectMenuOptionBuilder().setLabel('85%').setValue('85'),
                    new StringSelectMenuOptionBuilder().setLabel('87%').setValue('87'),
                    new StringSelectMenuOptionBuilder().setLabel('90%').setValue('90'),
                    new StringSelectMenuOptionBuilder().setLabel('92%').setValue('92'),
                    new StringSelectMenuOptionBuilder().setLabel('93%').setValue('93'),
                    new StringSelectMenuOptionBuilder().setLabel('94%').setValue('94'),
                    new StringSelectMenuOptionBuilder().setLabel('95%').setValue('95'),
                    new StringSelectMenuOptionBuilder().setLabel('96%').setValue('96'),
                    new StringSelectMenuOptionBuilder().setLabel('97%').setValue('97'),
                    new StringSelectMenuOptionBuilder().setLabel('98%').setValue('98'),
                );

            // Create action rows
            const rowPerson = new ActionRowBuilder().addComponents(selectPerson);
            const rowPlace = new ActionRowBuilder().addComponents(selectPlace);
            const rowPercentage = new ActionRowBuilder().addComponents(selectPercentage);
            const rowGoalPercentage = new ActionRowBuilder().addComponents(selectGoalPercentage); // New action row for goal percentage

            await msg.reply({
                content: 'Please select one or more people, places, and a percentage for the task:',
                components: [rowPerson, rowPlace, rowPercentage, rowGoalPercentage]
            });

            // Initialize userSelections for this user
            userSelections[msg.author.id] = {
                people: [],
                places: [],
                percentage: null,
                goalPercentage: null, 
                peopleOptions, // Store the options for later reference
                username: msg.author.username || msg.author.tag,  // Log the username being stored
            };
            console.log(`Initialized userSelections for ${msg.author.id}:`, userSelections[msg.author.id]); // Log the user ID correctly

        } catch (error) {
            console.error('Error reading CSV files:', error);
            await msg.reply('There was an error processing your request.');
        }
    }
});

client.on('interactionCreate', async (interaction) => {
    if (interaction.isStringSelectMenu()) {
        const userId = interaction.user.id;
        const userSelection = userSelections[userId]; // Get the user's selections
        console.log('User ID from interaction:', userId); // Log the user ID
        console.log('Current userSelections:', userSelections); // Log the current selections


        // Log user selections for debugging
        console.log('User selections:', userSelections[userId]); // Log user selections

         // Log user selections for debugging
         if (userSelections[userId]) {
            console.log('User selections:', userSelections[userId]); // Log user selections
        } else {
            console.log(`No selections found for user ${userId}.`); // Log if no selections are found
        }

        if (interaction.customId === 'personSelection') {
            userSelections[userId].people = interaction.values; // Store selected people
        } else if (interaction.customId === 'placeSelection') {
            userSelections[userId].places = interaction.values; // Store selected places
        } else if (interaction.customId === 'percentageSelection') {
            userSelections[userId].percentage = interaction.values[0]; // Store selected percentage
        } else if (interaction.customId === 'goalPercentageSelection') {
            userSelections[userId].goalPercentage = interaction.values[0]; // Store selected goal percentage
        }

        if (userSelection) {
            const { people, places, percentage, goalPercentage, peopleOptions } = userSelection; // Destructure all relevant variables
        
            // Check for completion of selections
            if (people.length > 0 && places.length > 0 && percentage && goalPercentage) {
                await interaction.reply({
                    content: 'All selections are complete! Please enter your comment below:',
                    ephemeral: true
                });
        
                // Handle comment input as needed
            } else {
                await interaction.reply({ content: 'Please complete all selections.', ephemeral: true });
            }
        
            // Wait for the user to send their comment
            const filter = response => response.author.id === userId && !response.author.bot;
            const collector = interaction.channel.createMessageCollector({ filter, time: 30000 }); // Collect for 30 seconds
        
            collector.on('collect', async commentMessage => {
                const comment = commentMessage.content; // Capture the comment

                // Construct the message with contact information
                const contactInfo = people.map(person => {
                    const personData = peopleOptions.find(option => option.value === person);
                    return `${personData.label}: ${personData.phone}`; // Format as Person: Phone
                }).join('\n'); // Join contact info into a string

                console.log('User ID:', userId); // Log the user ID
                console.log('User selections:', userSelections[userId]); // Log user selections to check their values
                const username = userSelections[userId] ? userSelections[userId].username : 'Unknown User';
                console.log('Username:', username); // Log the username being used


                const message = `🦍🦍🛴🛴 **Skift Plan** 🛴🛴🦍🦍\n\n` +
                    `Skiftleder: ${username}\n` +
                    `\n **Goal** \n` + 
                    `- Availability: ${goalPercentage || goalPercentage}% \n` +
                    `\n 🚦 **Team and områder**:\n` +
                    people.map((person, i) => {
                        const personData = peopleOptions.find(option => option.value === person);
                        const username = personData ? personData.username : 'Unknown User';
                        const name = personData ? personData.label : 'Unknown Name';
                        return `- ${username} ${getRandomWord()} ${places[i]}`;
                    }).join('\n') +
                    `\n\n📊 **Operational Notes**:\n` +
                    `- **Inactivity**: 🔄 ${percentage}% inactive for **2 days**.\n` +
                    `- **Clusters**: ${parseInt(percentage) + 10}% in clusters.\n` +
                    `- **Redeployment**: 📉 ${parseInt(percentage) + 15}% on inactives.\n\n` +
                    `🔒 **Container Codes**:\n` +
                    `- Code: **1602**\n\n` +
                    `🚨 **Important Reminders**:\n` +
                    `- **Use the car** 🚗\n` +
                    `- **Send routes** 🗺️\n` +
                    `- Ensure **Good Quality Control (QC)**\n` +
                    `- **Prioritize Superlows**\n` +
                    `- If you receive a **nivel** issue, **fix it within an hour**.\n\n` +
                    `📞 **Contact**:\n` +
                    people.map((person, i) => `• ${person}: ${peopleOptions[i].phone}`).join('\n') + // Using • for bullet points
                    `\n\n **Comment**: \n` + 
                    `${comment}\n` +
                    `\n\n 🪫🪫 **Battery Check** 🔋🔋 \n` +
                    `Make sure you're charged up and ready to go!`;

               // Respond with the constructed message
               await interaction.followUp(message); // Use followUp instead of reply

               // Check if the message exists before attempting to delete
                try {
                    await commentMessage.delete(); // Attempt to delete the comment after processing
                    } catch (error) {
                        console.error('Failed to delete the comment message:', error); // Log any errors that occur during deletion
                    }

                collector.stop(); // Stop the collector after processing the comment
            });
    
            collector.on('end', collected => {
                if (collected.size === 0) {
                    interaction.followUp({ content: 'No comment was provided. Please try again.', ephemeral: true });
                }
            });    

        } else {
            // Inform the user that selections are still incomplete
            await interaction.reply({ content: 'Please complete all selections.', ephemeral: true });
        }
    }
});