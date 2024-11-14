import requests
import os
import csv
import json
from dotenv import load_dotenv, set_key
from datetime import datetime, timedelta

#https://once.deputy.com/my/oauth/login?client_id=7e1fb2caa48adcef84c3dafe17ff801df8ab5ced&redirect_uri=http://localhost&response_type=code&scope=longlife_refresh_token


# Load environment variables from .env file
load_dotenv()
DEPUTY_API_KEY = os.getenv("DEPUTY_API_KEY")
DEPUTY_API_SECRET = os.getenv("DEPUTY_API_SECRET")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
REFRESH_TOKEN = os.getenv("REFRESH_TOKEN")
ENV_PATH = '.env'  # Path to your .env file

def update_env_variable(key, value):
    """Updates the specified key-value pair in the .env file."""
    set_key(ENV_PATH, key, value)

def get_access_token():
    """Gets a new access token using the refresh token and saves it to the .env file."""
    url = "https://rydetechnology.eu.deputy.com/oauth/access_token"
    payload = {
        "client_id": DEPUTY_API_KEY,
        "client_secret": DEPUTY_API_SECRET,
        "redirect_uri": "http://localhost",
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN,
        "scope": "longlife_refresh_token"
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    try:
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()  # Raise error for bad status codes
        data = response.json()
        
        # Extract new access and refresh tokens
        access_token = data.get("access_token")
        refresh_token = data.get("refresh_token")
        
        # Save the new tokens in the .env file
        update_env_variable("ACCESS_TOKEN", access_token)
        update_env_variable("REFRESH_TOKEN", refresh_token)
        
        print("Access Token Obtained:", access_token)
        print("New Refresh Token Saved:", refresh_token)
        
        return access_token, refresh_token
    
    except requests.exceptions.RequestException as e:
        print("Error renewing access token:", e)
        return None, None

def test_timesheet_access():
    """Uses the access token to query the timesheet data and saves it to a CSV file."""
    url_variations = [
        "https://rydetechnology.eu.deputy.com/api/v1/resource/Timesheet/QUERY",
    ]
    
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }
    # Calculate today's start and end times as Unix timestamps
    today_start = int(datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
    today_end = int(datetime.now().replace(hour=23, minute=59, second=59, microsecond=0).timestamp())
    
    # JSON payload to retrieve timesheets with StartTime within today's Unix time range
    payload = {
        "search": {
            "s1": {
                "field": "StartTime",
                "data": today_start,
                "type": "ge"
            },
            "s2": {
                "field": "StartTime",
                "data": today_end,
                "type": "le"
            }
        }
    }
  
    
    for url in url_variations:
        print(f"Trying URL: {url}")
        try:
            # Sending POST request with parameters
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            response.raise_for_status()
            data = response.json()  # Get the JSON response

                # Check if data is empty
            if not data:
                print("No data found.")
                return None
            # Filter data for CompanyName 'Bergen' and extract DisplayName
            display_names = []
            for item in data:
                dp_metadata = item.get("_DPMetaData", {})
                operational_unit_info = dp_metadata.get("OperationalUnitInfo", {})
                company_name = operational_unit_info.get("CompanyName")
                
                # Check for 'Bergen' in CompanyName and extract DisplayName
                if company_name == "Bergen":
                    display_name = dp_metadata.get("EmployeeInfo", {}).get("DisplayName")
                    if display_name:
                        display_names.append(display_name)
                    else:
                        print("DisplayName not found for item:", item)

            # Check if filtered data is empty
            if not display_names:
                print("No timesheets found for employees in company 'Bergen'.")
                return None
            
            # Ensure the Deputy folder exists
            if not os.path.exists("Deputy"):
                os.makedirs("Deputy")

            # Write the DisplayName data to a CSV file
            csv_file = "Deputy/employees_displaynames_bergen.csv"
            with open(csv_file, mode="w", newline="") as file:
                writer = csv.writer(file)
                
                # Write header
                writer.writerow(["DisplayName"])

                # Write each DisplayName as a new row
                for name in display_names:
                    writer.writerow([name])

            print(f"Data successfully written to {csv_file}")
            return csv_file  # Return the path to the CSV file


        except requests.exceptions.RequestException as e:
            print(f"Error accessing timesheets at {url}:", e)
            print("Response content:", response.text)

    print("No valid timesheet endpoint found.")
    return None

def main():
    # Get new tokens if necessary
    if not ACCESS_TOKEN or not REFRESH_TOKEN:
        get_access_token()

    # Refresh tokens if access token is expired
    if ACCESS_TOKEN:
        get_access_token()
        test_timesheet_access()

if __name__ == "__main__":
    main()