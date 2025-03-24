import argparse
import json
import os
import time
import subprocess
import sys
import signal
import logging
from virtual_env_station import EnvironmentalStation

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def check_config():
    """Check if config.json exists and is valid"""
    if not os.path.exists('config.json'):
        logging.error("Config file not found. Please create config.json")
        return False
    
    try:
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
            required_fields = ['channel_id', 'write_api_key', 'read_api_key', 'broker', 'port']
            for field in required_fields:
                if field not in config:
                    logging.error(f"Missing required field '{field}' in config.json")
                    return False
        return True
    except json.JSONDecodeError:
        logging.error("Invalid JSON in config.json")
        return False
    except Exception as e:
        logging.error(f"Error reading config.json: {e}")
        return False

def start_station(interval=30, station_id=None):
    """Start a virtual environmental station"""
    station = EnvironmentalStation(station_id)
    try:
        station.run(interval=interval)
    except KeyboardInterrupt:
        logging.info("Station stopped by user")

def display_menu():
    print("\n=== IoT Environmental Monitoring System ===")
    print("1. Start a virtual environmental station")
    print("2. Display latest sensor data")
    print("3. Display historical sensor data (last 5 hours)")
    print("4. Exit")
    return input("Select an option (1-4): ")

def main():
    # Check config file
    if not check_config():
        return
    
    parser = argparse.ArgumentParser(description='IoT Environmental Monitoring System')
    parser.add_argument('--station', action='store_true', help='Start a virtual environmental station')
    parser.add_argument('--interval', type=int, default=30, help='Interval between readings in seconds')
    parser.add_argument('--id', type=str, help='Custom station ID')
    args = parser.parse_args()
    
    # If station flag is provided, start station and exit
    if args.station:
        start_station(args.interval, args.id)
        return
    
    # Interactive menu
    while True:
        choice = display_menu()
        
        if choice == '1':
            # Get parameters
            interval = input("Enter reading interval in seconds (default 30): ")
            interval = int(interval) if interval.isdigit() else 30
            
            station_id = input("Enter station ID (leave blank for auto-generated): ")
            station_id = station_id if station_id else None
            
            print(f"Starting station with interval {interval}s...")
            # Start in a new process
            try:
                cmd = [sys.executable, __file__, '--station', '--interval', str(interval)]
                if station_id:
                    cmd.extend(['--id', station_id])
                
                subprocess.Popen(cmd, start_new_session=True)
                print("Station started in background")
            except Exception as e:
                print(f"Error starting station: {e}")
        
        elif choice == '2':
            # Display latest data
            refresh = input("Enter refresh rate in seconds (0 for one-time display): ")
            refresh = int(refresh) if refresh.isdigit() else 0
            
            try:
                cmd = [sys.executable, 'display_latest.py']
                if refresh > 0:
                    cmd.extend(['--refresh', str(refresh)])
                
                subprocess.run(cmd)
            except Exception as e:
                print(f"Error displaying data: {e}")
        
        elif choice == '3':
            # Display historical data
            sensor = input("Enter sensor type (temperature, humidity, co2): ").lower()
            if sensor not in ['temperature', 'humidity', 'co2']:
                print("Invalid sensor type. Please choose from: temperature, humidity, co2")
                continue
            
            hours = input("Enter number of hours to look back (default 5): ")
            hours = int(hours) if hours.isdigit() else 5
            
            try:
                cmd = [sys.executable, 'display_historical.py', sensor, '--hours', str(hours)]
                subprocess.run(cmd)
            except Exception as e:
                print(f"Error displaying historical data: {e}")
        
        elif choice == '4':
            print("Exiting program")
            break
        
        else:
            print("Invalid option. Please select 1-4.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram terminated by user")