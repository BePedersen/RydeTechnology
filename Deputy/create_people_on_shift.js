// Hente innformasjon fra Deputy - kjør Deputytest

// Slette fileinnhold

const fs = require('fs');
const csv = require('csv-parser');

// Function to read the CSV file and process the data
async function readCSV(filePath) {
    return new Promise((resolve, reject) => {
        const options = [];
        console.log(`Reading CSV from ${filePath}`);

        fs.createReadStream(filePath)
            .pipe(csv())
            .on('data', (row) => {
                console.log('Row read:', row); // Log each row for debugging

                // Check for DisplayName field in the first CSV
                if (row.DisplayName) {
                    options.push({
                        label: row.DisplayName.trim() // Ensure DisplayName is trimmed
                    });
                }
            })
            .on('end', () => {
                console.log(`CSV reading completed for ${filePath}`);
                resolve(options);
            })
            .on('error', (error) => {
                console.error('Error reading CSV:', error);
                reject(error);
            });
    });
}

// Function to match on-shift employees with the full employee list
async function matchEmployees() {
    console.log('Starting employee matching process...');

    // Load on-shift employees from employees_displaynames_bergen.csv (only Display Name)
    const onShiftData = await readCSV('./Deputy/employees_displaynames_bergen.csv');
    console.log('On-shift employees read:', onShiftData); // Log the data read from the on-shift file
    const onShiftEmployees = new Set(onShiftData.map(employee => employee.label.toLowerCase().trim())); // Normalize to lowercase and remove extra spaces
    console.log('On-shift employees Set:', onShiftEmployees);

    // Load all employees from people.csv
    const employees = await readCSV('./Data/people.csv');
    console.log('All employees read:', employees.length, 'entries');
    console.log('All employees:', employees); // Log the full employee list for debugging

    // Filter matched employees by checking if Display Name exists in onShiftEmployees set
    const matchedEmployees = employees.filter(employee => {
        const label = employee.label.trim().toLowerCase(); // Normalize the label for matching
        if (onShiftEmployees.has(label)) {
            console.log(`Matched: ${label}`); // Log matched employee
            return true;
        }
        return false;
    });

    console.log('Matched employees:', matchedEmployees);

    // Write matched employees to CSV
    const outputFilePath = './Deputy/people_on_shift.csv';
    const outputStream = fs.createWriteStream(outputFilePath);
    outputStream.write('label,value,phone,username\n');
    matchedEmployees.forEach(employee => {
        outputStream.write(`${employee.label},${employee.value},${employee.phone},${employee.username}\n`);
    });
    outputStream.end();

    console.log(`Matched employees written to ${outputFilePath}`);
}

// Run matching process
matchEmployees();
