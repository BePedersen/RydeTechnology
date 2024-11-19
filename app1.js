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

/* ------------------------------------- Legg in Deputy -----------------------------------------------------------------------*/

require('dotenv').config();

client.login(process.env.DISCORD_TOKEN);

client.on('messageCreate', async (msg) => {
    if (msg.content === '!opsplan' && !msg.author.bot) {
        console.log(msg.content)
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

            const selectInactive = new StringSelectMenuBuilder()
                .setCustomId('daysInactiveSelection')
                .setPlaceholder('Inactive')
                .setMinValues(1) // Only allow one selection
                .setMaxValues(1)
                .addOptions(
                    new StringSelectMenuOptionBuilder().setLabel('1').setValue('1'),
                    new StringSelectMenuOptionBuilder().setLabel('2').setValue('2'),
                    new StringSelectMenuOptionBuilder().setLabel('3').setValue('3'),
                    new StringSelectMenuOptionBuilder().setLabel('4').setValue('4')
                );

            // Create action rows
            const rowPerson = new ActionRowBuilder().addComponents(selectPerson);
            const rowPlace = new ActionRowBuilder().addComponents(selectPlace);
            const rowPercentage = new ActionRowBuilder().addComponents(selectPercentage);
            const rowGoalPercentage = new ActionRowBuilder().addComponents(selectGoalPercentage); // New action row for goal percentage
            const rowInactive = new ActionRowBuilder().addComponents(selectInactive); 

            await msg.reply({
                content: 'Please make your selections:',
                components: [rowPerson, rowPlace, rowPercentage, rowGoalPercentage, rowInactive],
            });

            // Initialize userSelections for this user
            userSelections[msg.author.id] = {
                people: [],
                places: [],
                percentage: null,
                goalPercentage: null, 
                daysInactive: null,
                peopleOptions, // Store the options for later reference
                username: msg.author.username || msg.author.tag,  // Log the username being stored
            };
            console.log(`Initialized userSelections for ${msg.author.id}:`, userSelections[msg.author.id]); // Log the user ID correctly

             // Send the message with dropdowns
             
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
        }else if (interaction.customId === 'daysInactiveSelection') {
            userSelections[userId].daysInactive = interaction.values[0]; // Store selected goal percentage
        }

        if (userSelection) {
            const {people, places, percentage, goalPercentage, daysInactive, peopleOptions } = userSelection; // Destructure all relevant variables
        
             // Check for completion of selections
             if (people.length > 0 && places.length > 0 && percentage && goalPercentage && daysInactive) {
                await interaction.reply({
                    content: 'All selections are complete! Please enter your comment below:',
                    ephemeral: true
                });
        
                // Handle comment input as needed ---- see if the messsage under can be worked around
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
                    `- Availability: ${goalPercentage || 90}% \n` +
                    `\n 🚦 **Team and områder**:\n` +

                    // Legger inn person og område de kjører i

                    people.map((person, i) => {
                        const personData = peopleOptions.find(option => option.value === person);
                        const username = personData ? personData.username : 'Unknown User';
                        const name = personData ? personData.label : 'Unknown Name';
                        return `- ${username} ${getRandomWord()} ${places[i]}`;
                    }).join('\n') +


                    `\n\n📊 **Operational Notes**:\n` +
                    `- **Inactivity**: 🔄 ${percentage}% inactive for ** ${daysInactive || 2} days**.\n` +
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

        } 
    }
});




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

// This is the global object to store user selections
const userSelections = {};

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
        console.log(msg.content)
        try {
            const peopleOptions = await readCSV('./Deputy/people_on_shift.csv'); // Path to your people CSV
            
            // Dropdown for selecting people
            const selectPerson = new StringSelectMenuBuilder()
                .setCustomId('personSelection')
                .setPlaceholder('Select people')
                .setMinValues(1)
                .setMaxValues(peopleOptions.length) // Set max choices to the length of peopleOptions
                .addOptions(peopleOptions);

            const rowPerson = new ActionRowBuilder().addComponents(selectPerson);

            userSelections[msg.author.id] = {
                people: [],
                places: [] // Store places for each user
            };

            // Send the people selection message
            await msg.reply({
                content: 'Please select the people you want to assign places to:',
                components: [rowPerson]
            });

        } catch (error) {
            console.error('Error reading or sending message for people selection:', error);
            await msg.reply('There was an error processing your request. Please check the logs for more details.');
        }
    }
});

client.on('interactionCreate', async (interaction) => {
    if (!interaction.isStringSelectMenu()) return;

    const userId = interaction.user.id;

    if (interaction.customId === 'personSelection') {
        try {
            // Store the selected people for the user
            userSelections[userId].people = interaction.values;
            console.log('People selected:', interaction.values);

            // Send confirmation message about the people selected
            await interaction.update({
                content: `You selected: ${interaction.values.join(', ')}. Now select a place for each driver:`,
                components: [] // Remove the people selection dropdown
            });

            // Proceed with the place selection
            console.log('Reading places CSV...');
            const placesOptions = await readCSV('./Data/places.csv'); // Path to your places CSV
            console.log('Places options:', placesOptions);

            // Store places options for the user
            userSelections[userId].placesOptions = placesOptions;

            // Create an array to hold all action rows for the place selections
            const actionRows = [];

            // Loop through each selected person (driver) and create a place selection menu for each one
            for (let i = 0; i < interaction.values.length; i++) {
                const selectPlace = new StringSelectMenuBuilder()
                    .setCustomId(`placeSelection_${i}`) // Unique ID for each menu
                    .setPlaceholder(`Select a place for ${interaction.values[i]}`)
                    .setMinValues(1)
                    .setMaxValues(1) // One place per person
                    .addOptions(placesOptions);

                const rowPlace = new ActionRowBuilder().addComponents(selectPlace);
                actionRows.push(rowPlace); // Add each row to the actionRows array
            }

            // Send the place selection dropdowns for each driver
            await interaction.followUp({
                content: 'Please select a place for each driver:',
                components: actionRows
            });

        } catch (error) {
            console.error('Error in handling person selection or reading places CSV:', error);
            await interaction.followUp('There was an error processing your request. Please check the logs for more details.');
        }
    }

    // Handle the interaction for place selection
    if (interaction.customId.startsWith('placeSelection_')) {
        const personIndex = parseInt(interaction.customId.split('_')[1]); // Extract the index from the customId
        const selectedPlace = interaction.values[0]; // Get the selected place

        try {
            // Ensure that the placesOptions are available for this user
            const placesOptions = userSelections[userId].placesOptions;
            if (!placesOptions) {
                throw new Error('Places options not found for this user.');
            }

            // Assign the place to the driver (person)
            userSelections[userId].places[personIndex] = selectedPlace;
            console.log(`${userSelections[userId].people[personIndex]} has been assigned to ${selectedPlace}`);

            // Send confirmation that the place has been assigned
            await interaction.update({
                content: `${userSelections[userId].people[personIndex]} has been assigned to ${selectedPlace}.`,
                components: [] // Remove the dropdown for this person after they have selected a place
            });

            // Optionally, if all drivers have been assigned places, you can finalize the process here
            if (userSelections[userId].places.length === userSelections[userId].people.length) {
                await interaction.followUp({
                    content: `All drivers have been assigned to places:\n` + 
                             userSelections[userId].people.map((person, index) => `${person} → ${userSelections[userId].places[index]}`).join('\n')
                });
            } else {
                // Re-send the remaining dropdowns for people who haven't selected a place
                const remainingActionRows = [];
                for (let i = 0; i < userSelections[userId].people.length; i++) {
                    if (!userSelections[userId].places[i]) { // If the place is not assigned yet
                        const selectPlace = new StringSelectMenuBuilder()
                            .setCustomId(`placeSelection_${i}`)
                            .setPlaceholder(`Select a place for ${userSelections[userId].people[i]}`)
                            .setMinValues(1)
                            .setMaxValues(1)
                            .addOptions(placesOptions);
                        const rowPlace = new ActionRowBuilder().addComponents(selectPlace);
                        remainingActionRows.push(rowPlace);
                    }
                }

                // Send the remaining dropdowns
                await interaction.followUp({
                    content: 'Please select a place for the remaining drivers:',
                    components: remainingActionRows
                });
            }

        } catch (error) {
            console.error('Error in handling place selection:', error);
            await interaction.followUp('There was an error processing your place selection. Please check the logs for more details.');
        }
    }

    if () {

        

    }

});






const { 
    Client, 
    GatewayIntentBits, 
    StringSelectMenuBuilder, 
    ActionRowBuilder,
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

// This is the global object to store user selections
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
                    phone: row.phone || 'Not provided',  // Only add phone if it exists
                    username: row.username || 'Not provided'  // Add username with default if missing
                });
            })
            .on('end', () => {
                resolve(options);
            })
            .on('error', (error) => {
                reject(error);
            });
    });
}

// Define helper functions for dropdowns
function getPercentageDropdown() {
    return new ActionRowBuilder().addComponents(
        new StringSelectMenuBuilder()
            .setCustomId('percentageSelection')
            .setPlaceholder('Select a percentage')
            .setMinValues(1)
            .setMaxValues(1)
            .addOptions(
                { label: '50%', value: '50' },
                { label: '75%', value: '75' },
                { label: '100%', value: '100' }
            )
    );
}

function getGoalDropdown() {
    return new ActionRowBuilder().addComponents(
        new StringSelectMenuBuilder()
            .setCustomId('goalSelection')
            .setPlaceholder('Select a goal')
            .setMinValues(1)
            .setMaxValues(1)
            .addOptions(
                { label: 'Goal A', value: 'goalA' },
                { label: 'Goal B', value: 'goalB' },
                { label: 'Goal C', value: 'goalC' }
            )
    );
}

function getInactiveDropdown() {
    return new ActionRowBuilder().addComponents(
        new StringSelectMenuBuilder()
            .setCustomId('inactiveSelection')
            .setPlaceholder('Select inactive status')
            .setMinValues(1)
            .setMaxValues(1)
            .addOptions(
                { label: 'Active', value: 'active' },
                { label: 'Inactive', value: 'inactive' }
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
            const peopleOptions = await readCSV('./Deputy/people_on_shift.csv'); // Path to your people CSV
            
            // Dropdown for selecting people
            const selectPerson = new StringSelectMenuBuilder()
                .setCustomId('personSelection')
                .setPlaceholder('Select people')
                .setMinValues(1)
                .setMaxValues(peopleOptions.length)
                .addOptions(peopleOptions);

            const rowPerson = new ActionRowBuilder().addComponents(selectPerson);

            userSelections[msg.author.id] = {
                people: [],
                places: [] // Store places for each user
            };

            await msg.reply({
                content: 'Please select the people you want to assign places to:',
                components: [rowPerson]
            });

        } catch (error) {
            console.error('Error in people selection:', error);
            await msg.reply('There was an error processing your request. Please check the logs.');
        }
    }
});

client.on('interactionCreate', async (interaction) => {
    if (!interaction.isStringSelectMenu()) return;

    const userId = interaction.user.id;  // Ensure userId is defined here

    if (interaction.customId === 'personSelection') {
        try {
            // Store the selected people for the user
            userSelections[userId].people = interaction.values;
            console.log('People selected:', interaction.values);

            // Send confirmation message about the people selected
            await interaction.update({
                content: `You selected: ${interaction.values.join(', ')}. Now select a place for each driver:`,
                components: [] // Remove the people selection dropdown
            });

            // Proceed with the place selection
            console.log('Reading places CSV...');
            const placesOptions = await readCSV('./Data/places.csv'); // Path to your places CSV
            console.log('Places options:', placesOptions);

            // Store places options for the user
            userSelections[userId].placesOptions = placesOptions;

            // Create an array to hold all action rows for the place selections
            const actionRows = [];

            // Loop through each selected person (driver) and create a place selection menu for each one
            for (let i = 0; i < interaction.values.length; i++) {
                const selectPlace = new StringSelectMenuBuilder()
                    .setCustomId(`placeSelection_${i}`) // Unique ID for each menu
                    .setPlaceholder(`Select a place for ${interaction.values[i]}`)
                    .setMinValues(1)
                    .setMaxValues(1) // One place per person
                    .addOptions(placesOptions);

                const rowPlace = new ActionRowBuilder().addComponents(selectPlace);
                actionRows.push(rowPlace); // Add each row to the actionRows array
            }

            // Send the place selection dropdowns for each driver
            await interaction.followUp({
                content: 'Please select a place for each driver:',
                components: actionRows
            });

        } catch (error) {
            console.error('Error in handling person selection or reading places CSV:', error);
            await interaction.followUp('There was an error processing your request. Please check the logs for more details.');
        }
    }

    // Handle the interaction for place selection
    if (interaction.customId.startsWith('placeSelection_')) {
        const personIndex = parseInt(interaction.customId.split('_')[1]); // Extract the index from the customId
        const selectedPlace = interaction.values[0]; // Get the selected place

        try {
            // Ensure that the placesOptions are available for this user
            const placesOptions = userSelections[userId].placesOptions;
            if (!placesOptions) {
                throw new Error('Places options not found for this user.');
            }

            // Assign the place to the driver (person)
            userSelections[userId].places[personIndex] = selectedPlace;
            console.log(`${userSelections[userId].people[personIndex]} has been assigned to ${selectedPlace}`);

            // Send confirmation that the place has been assigned
            await interaction.update({
                content: `${userSelections[userId].people[personIndex]} has been assigned to ${selectedPlace}.`,
                components: [] // Remove the dropdown for this person after they have selected a place
            });

            // Optionally, if all drivers have been assigned places, you can finalize the process here
            if (userSelections[userId].places.length === userSelections[userId].people.length) {
                await interaction.followUp({
                    content: `All drivers have been assigned to places:\n` + 
                             userSelections[userId].people.map((person, index) => `${person} → ${userSelections[userId].places[index]}`).join('\n')
                });
            } else {
                // Re-send the remaining dropdowns for people who haven't selected a place
                const remainingActionRows = [];
                for (let i = 0; i < userSelections[userId].people.length; i++) {
                    if (!userSelections[userId].places[i]) { // If the place is not assigned yet
                        const selectPlace = new StringSelectMenuBuilder()
                            .setCustomId(`placeSelection_${i}`)
                            .setPlaceholder(`Select a place for ${userSelections[userId].people[i]}`)
                            .setMinValues(1)
                            .setMaxValues(1)
                            .addOptions(placesOptions);
                        const rowPlace = new ActionRowBuilder().addComponents(selectPlace);
                        remainingActionRows.push(rowPlace);
                    }
                }

                // Send the remaining dropdowns
                await interaction.followUp({
                    content: 'Please select a place for the remaining drivers:',
                    components: remainingActionRows
                });
            }

        } catch (error) {
            console.error('Error in handling place selection:', error);
            await interaction.followUp('There was an error processing your place selection. Please check the logs for more details.');
        }
    }

    // Optionally add additional logic for selecting percentage, goal, and inactive status
    if (interaction.customId === 'percentageGoalInactiveSelection') {
        // Handle the logic for selecting percentage, goal, and inactive status here
    }

});




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
                { label: '50%', value: '50' },
                { label: '75%', value: '75' },
                { label: '100%', value: '100' }
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
                currentDriverIndex: 0,
                currentStep: 'selectPeople',
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
    }
});

client.on('interactionCreate', async (interaction) => {
    if (!interaction.isStringSelectMenu()) return;

    const userId = interaction.user.id;
    const userState = userSelections[userId];
    const currentStep = userState.currentStep;

    if (currentStep === 'selectPeople' && interaction.customId === 'personSelection') {
        userState.people = interaction.values;
        console.log('People selected:', interaction.values);

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

        console.log(`${selectedDriver} has been assigned to ${selectedPlace}.`);

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
        const selectedPercentage = interaction.values[0];
        console.log('Selected percentage:', selectedPercentage);

        await interaction.update({
            content: `You selected ${selectedPercentage}%. Assignment process complete!`,
            components: [],
        });

        // Show a summary
        await interaction.followUp({
            content: `Summary of assignments:\n` +
                userState.places.map(({ person, place }) => `${person} → ${place}`).join('\n') +
                `\nPercentage: ${selectedPercentage}%`,
        });
    }
});

