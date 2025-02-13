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
    print(f"Updating {key} in .env with value: {value}")  # Debug log
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
        "https://rydetechnology.eu.deputy.com/api/v1/resource/Roster/QUERY"

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
  
    combined_display_names = []  # List to store all display names from all URL variations
    """
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
                company_name = operational_unit_info.get("CompanyName", {})

                # Check for 'Bergen' in CompanyName and extract DisplayName
                if company_name == "Bergen":
#                    display_name = dp_metadata.get("EmployeeInfo", {}).get("DisplayName")
                    label_with_company = dp_metadata.get("OperationalUnitInfo", {}).get("LabelWithCompany")
                    if label_with_company in ["[BRG] Operations", "[BRG] Night Shift", "[BRG] Operations Training/follow up", "[BRG] Management"] :
                        display_name = dp_metadata.get("EmployeeInfo", {}).get("DisplayName")
                    
                        if display_name:
                            display_names.append(display_name)
                        else:
                            print("DisplayName not found for item:", item)

            # Check if filtered data is empty
            if not display_names:
                print("No timesheets found for employees in company 'Bergen'.")
                continue

            # Write the DisplayName data to a CSV file
            csv_file = "Data/Deputy/Bergen_ops.csv"
            with open(csv_file, mode="w", newline="") as file:
                writer = csv.writer(file)
                
                # Write header
                writer.writerow(["label"])

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
"""
    for url in url_variations:
        print(f"Trying URL: {url}")
        try:
            # Sending POST request with parameters
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            response.raise_for_status()
            data = response.json()  # Get the JSON response

            # Check if data is empty
            if not data:
                print(f"No data found at {url}. Continuing to the next URL.")
                continue  # Skip to the next URL

            # Filter data for CompanyName 'Bergen' and extract DisplayName
            for item in data:
                dp_metadata = item.get("_DPMetaData", {})  # Get metadata or empty dict
                if not dp_metadata:
                    print("Warning: '_DPMetaData' key is missing or None in item:", item)
                    continue  # Skip this iteration if there's no metadata

                operational_unit_info = dp_metadata.get("OperationalUnitInfo", {})  # Get unit info or empty dict
                if operational_unit_info is None:
                    employee_info = dp_metadata.get("EmployeeInfo", {})
                    if isinstance(employee_info, list):
                        for info in employee_info:
                            if isinstance(info, dict):
                                display_name = info.get("DisplayName")
                    print("Warning: 'OperationalUnitInfo' is None in dp_metadata:",display_name)
                    continue  # Skip this iteration if no OperationalUnitInfo

                company_name = operational_unit_info.get("CompanyName", None)

                # Check for 'Bergen' in CompanyName and extract DisplayName
                if company_name == "Bergen":
                    label_with_company = operational_unit_info.get("LabelWithCompany")
                    if label_with_company in ["[BRG] Operations", "[BRG] Night Shift", "[BRG] Operations Training/follow up", "[BRG] Management"]:
                        employee_info = dp_metadata.get("EmployeeInfo", {})
                        
                        # Handle if EmployeeInfo is a list
                        if isinstance(employee_info, list):
                            for info in employee_info:
                                if isinstance(info, dict):
                                    display_name = info.get("DisplayName")
                                    if display_name and display_name not in combined_display_names:  # Avoid duplicates
                                        combined_display_names.append(display_name)
                        # Handle if EmployeeInfo is a dict
                        elif isinstance(employee_info, dict):
                            display_name = employee_info.get("DisplayName")
                            if display_name and display_name not in combined_display_names:  # Avoid duplicates
                                combined_display_names.append(display_name)
                        else:
                            print("Unexpected EmployeeInfo format:", employee_info)
                                    
        except requests.exceptions.RequestException as e:
            print(f"Error accessing timesheets at {url}:", e)
        if response is not None:
            print("Response content is not None")

    # Write the combined DisplayName data to a CSV file
    if combined_display_names:
        csv_file = "Data/Deputy/Bergen_ops.csv"
        with open(csv_file, mode="w", newline="") as file:
            writer = csv.writer(file)
            
            # Write header
            writer.writerow(["label"])

            # Write each DisplayName as a new row
            for name in combined_display_names:
                writer.writerow([name])
  
        print(f"Combined data successfully written to {csv_file}")
        return csv_file  # Return the path to the CSV file
    else:
        print("No valid timesheets found across all URLs.")
        return None
def update_ops():
    # Load environment variables from .env file
    load_dotenv(override=True)
    global ACCESS_TOKEN, REFRESH_TOKEN
    ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
    REFRESH_TOKEN = os.getenv("REFRESH_TOKEN")

    # Get new tokens if necessary
    if not ACCESS_TOKEN or not REFRESH_TOKEN:
        get_access_token()

    # Refresh tokens if access token is expired
    if ACCESS_TOKEN:
        get_access_token()
        test_timesheet_access()
