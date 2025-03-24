import requests
import json
import argparse
import time
from datetime import datetime
from tabulate import tabulate

def load_config():
    with open('config.json', 'r') as config_file:
        return json.load(config_file)

def fetch_latest_data(channel_id, read_api_key):
    """
    Fetch the latest data from ThingSpeak for a specific channel
    """
    url = f"https://api.thingspeak.com/channels/{channel_id}/feeds/last.json?api_key={read_api_key}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def parse_station_id(status_field):
    """Extract station_id from the status field"""
    if not status_field:
        return "Unknown"
    
    try:
        # The status format is "station_id:XXXXX"
        return status_field.split(':')[1]
    except (IndexError, AttributeError):
        return "Unknown"

def display_latest_data(channel_id, read_api_key, refresh_rate=None):
    """
    Display the latest sensor data in a formatted table
    
    Args:
        channel_id: ThingSpeak channel ID
        read_api_key: ThingSpeak read API key
        refresh_rate: Rate in seconds to refresh data (None for one-time display)
    """
    try:
        while True:
            data = fetch_latest_data(channel_id, read_api_key)
            
            if not data:
                print("No data available")
                if not refresh_rate:
                    break
                time.sleep(refresh_rate)
                continue
            
            # Extract and format data
            station_id = parse_station_id(data.get('status'))
            created_at = data.get('created_at')
            
            # Convert time to local time with format
            try:
                dt = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")
                formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, TypeError):
                formatted_time = created_at
            
            # Extract sensor readings
            temperature = data.get('field1')
            humidity = data.get('field2')
            co2 = data.get('field3')
            
            # Prepare data for tabulation
            table_data = [
                ["Station ID", station_id],
                ["Timestamp", formatted_time],
                ["Temperature", f"{temperature} °C"],
                ["Humidity", f"{humidity} %"],
                ["CO2", f"{co2} ppm"]
            ]
            
            # Clear screen and display data
            print("\033c", end="")  # Clear screen
            print("Latest Environmental Sensor Data")
            print("=" * 40)
            print(tabulate(table_data, tablefmt="grid"))
            
            if not refresh_rate:
                break
                
            print(f"\nRefreshing in {refresh_rate} seconds... (Press Ctrl+C to exit)")
            time.sleep(refresh_rate)
            
    except KeyboardInterrupt:
        print("\nExiting display...")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Display latest environmental station data')
    parser.add_argument('--refresh', type=int, help='Refresh rate in seconds')
    args = parser.parse_args()
    
    config = load_config()
    channel_id = config["channel_id"]
    read_api_key = config["read_api_key"]
    
    display_latest_data(channel_id, read_api_key, args.refresh)