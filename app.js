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
                content: `${userSelections[userId].people[personIndex]} has been assigned to ${selectedPlace}. Now, select percentage, goal, and inactive status:`,
                components: [] // Remove the dropdown for this person after they have selected a place
            });

            // After assigning a place, send the dropdowns for percentage, goal, and inactive status
            await interaction.followUp({
                content: 'Please select the percentage, goal, and inactive status for each driver:',
                components: [
                    getPercentageDropdown(),
                    getGoalDropdown(),
                    getInactiveDropdown()
                ]
            });

        } catch (error) {
            console.error('Error in handling place selection:', error);
            await interaction.followUp('There was an error processing your place selection. Please check the logs for more details.');
        }
    }

    // Handle percentage selection
    if (interaction.customId === 'percentageSelection') {
        const selectedPercentage = interaction.values[0];  // Get the selected percentage
        console.log(`${interaction.user.username} selected percentage: ${selectedPercentage}`);
        
        // Store the selected percentage (you can store this in `userSelections[userId]`)
        userSelections[userId].percentage = selectedPercentage;

        await interaction.update({
            content: `You selected: ${selectedPercentage}%. Now, please select a goal:`,
            components: [getGoalDropdown()]  // Show the goal dropdown next
        });
    }

    // Handle goal selection
    if (interaction.customId === 'goalSelection') {
        const selectedGoal = interaction.values[0];  // Get the selected goal
        console.log(`${interaction.user.username} selected goal: ${selectedGoal}`);
        
        // Store the selected goal
        userSelections[userId].goal = selectedGoal;

        await interaction.update({
            content: `You selected: ${selectedGoal}. Now, please select the inactive status:`,
            components: [getInactiveDropdown()]  // Show the inactive dropdown next
        });
    }

    // Handle inactive selection
    if (interaction.customId === 'inactiveSelection') {
        const selectedInactive = interaction.values[0];  // Get the selected inactive status
        console.log(`${interaction.user.username} selected inactive status: ${selectedInactive}`);
        
        // Store the selected inactive status
        userSelections[userId].inactive = selectedInactive;

        await interaction.update({
            content: `You selected: ${selectedInactive}.`,
            components: []  // Remove the dropdown
        });

        // Optionally, you can finalize or show a summary after all selections are done
        if (userSelections[userId].percentage && userSelections[userId].goal && userSelections[userId].inactive) {
            await interaction.followUp({
                content: `You have completed your selections:\n` +
                         `Percentage: ${userSelections[userId].percentage}\n` +
                         `Goal: ${userSelections[userId].goal}\n` +
                         `Inactive status: ${userSelections[userId].inactive}`
            });
        }
    }
});
