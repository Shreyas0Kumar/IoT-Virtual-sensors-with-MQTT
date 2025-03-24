import requests
import json
import argparse
import time
from datetime import datetime, timedelta
from tabulate import tabulate
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter

def load_config():
    with open('config.json', 'r') as config_file:
        return json.load(config_file)

def fetch_historical_data(channel_id, read_api_key, hours=5):
    """
    Fetch data from ThingSpeak for the last specified hours
    """
    # Calculate start time (5 hours ago)
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours)
    
    # Format times for ThingSpeak API
    start_str = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_str = end_time.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # ThingSpeak API endpoint for historical data
    url = f"https://api.thingspeak.com/channels/{channel_id}/feeds.json"
    params = {
        "api_key": read_api_key,
        "start": start_str,
        "end": end_str,
        "results": 8000  # Maximum allowed by ThingSpeak
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching historical data: {e}")
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

def display_historical_data(channel_id, read_api_key, sensor_type, hours=5, plot=True):
    """
    Display historical sensor data for the specified sensor type
    
    Args:
        channel_id: ThingSpeak channel ID
        read_api_key: ThingSpeak read API key
        sensor_type: Type of sensor (temperature, humidity, co2)
        hours: Number of hours to look back
        plot: Whether to generate a plot
    """
    # Map sensor type to field
    sensor_map = {
        "temperature": {"field": "field1", "unit": "°C", "title": "Temperature"},
        "humidity": {"field": "field2", "unit": "%", "title": "Humidity"},
        "co2": {"field": "field3", "unit": "ppm", "title": "CO2"}
    }
    
    if sensor_type.lower() not in sensor_map:
        print(f"Error: Invalid sensor type '{sensor_type}'. Choose from: temperature, humidity, co2")
        return
    
    sensor_info = sensor_map[sensor_type.lower()]
    data = fetch_historical_data(channel_id, read_api_key, hours)
    
    if not data or "feeds" not in data or not data["feeds"]:
        print(f"No data available for the last {hours} hours")
        return
    
    # Extract relevant data
    feeds = data["feeds"]
    timestamps = []
    values = []
    station_id = None
    
    for entry in feeds:
        # Get station ID from the first valid entry
        if not station_id and entry.get("status"):
            station_id = parse_station_id(entry.get("status"))
        
        # Parse timestamp
        try:
            timestamp = datetime.strptime(entry.get("created_at"), "%Y-%m-%dT%H:%M:%SZ")
        except (ValueError, TypeError):
            continue
        
        # Get sensor value
        value = entry.get(sensor_info["field"])
        if value is not None:
            try:
                value = float(value)
                timestamps.append(timestamp)
                values.append(value)
            except (ValueError, TypeError):
                continue
    
    if not timestamps:
        print(f"No valid {sensor_type} data found for the last {hours} hours")
        return
    
    # Display tabular data
    print(f"Historical {sensor_info['title']} Data for the Last {hours} Hours")
    print(f"Station ID: {station_id or 'Unknown'}")
    print("=" * 60)
    
    # Prepare tabular data
    table_data = []
    for i in range(len(timestamps)):
        formatted_time = timestamps[i].strftime("%Y-%m-%d %H:%M:%S")
        table_data.append([formatted_time, f"{values[i]} {sensor_info['unit']}"])
    
    print(tabulate(table_data, headers=["Timestamp", f"{sensor_info['title']} ({sensor_info['unit']})"], tablefmt="grid"))
    
    # Generate plot if requested
    if plot and len(timestamps) > 1:
        plt.figure(figsize=(12, 6))
        plt.plot(timestamps, values, marker='o', linestyle='-', markersize=3)
        plt.title(f"{sensor_info['title']} Readings - Last {hours} Hours")
        plt.xlabel("Time")
        plt.ylabel(f"{sensor_info['title']} ({sensor_info['unit']})")
        plt.grid(True)
        
        # Format the x-axis to show readable time
        plt.gca().xaxis.set_major_formatter(DateFormatter("%H:%M"))
        
        # Rotate date labels for better readability
        plt.gcf().autofmt_xdate()
        
        # Save the plot to a file
        filename = f"{sensor_type}_last_{hours}hours.png"
        plt.savefig(filename)
        print(f"\nPlot saved to {filename}")
        
        # Show the plot
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Display historical sensor data')
    parser.add_argument('sensor', choices=['temperature', 'humidity', 'co2'], 
                        help='Type of sensor data to display')
    parser.add_argument('--hours', type=int, default=5, 
                        help='Number of hours to look back (default: 5)')
    parser.add_argument('--no-plot', action='store_true', 
                        help='Disable plot generation')
    args = parser.parse_args()
    
    config = load_config()
    channel_id = config["channel_id"]
    read_api_key = config["read_api_key"]
    
    display_historical_data(channel_id, read_api_key, args.sensor, args.hours, not args.no_plot)