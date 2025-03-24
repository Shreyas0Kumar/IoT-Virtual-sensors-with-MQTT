#!/usr/bin/env python3
"""
Virtual Environmental Station using HTTP API instead of MQTT
"""

import random
import time
import json
import uuid
import datetime
import argparse
import sys
import requests

class HttpEnvironmentalStation:
    def __init__(self, station_id=None, channel_id="YOUR_CHANNEL_ID", write_api_key="YOUR_WRITE_API_KEY"):
        # Generate a unique ID if not provided
        self.station_id = station_id if station_id else f"station_{uuid.uuid4().hex[:8]}"
        
        # ThingSpeak configuration
        self.channel_id = channel_id
        self.write_api_key = write_api_key
        self.api_url = f"https://api.thingspeak.com/update"
        
        # Sensor ranges
        self.temp_range = (-50, 50)        # Celsius
        self.humidity_range = (0, 100)     # Percentage
        self.co2_range = (300, 2000)       # ppm
            
    def generate_sensor_data(self):
        """Generate random sensor values within the specified ranges"""
        temperature = round(random.uniform(self.temp_range[0], self.temp_range[1]), 2)
        humidity = round(random.uniform(self.humidity_range[0], self.humidity_range[1]), 2)
        co2 = round(random.uniform(self.co2_range[0], self.co2_range[1]), 2)
        
        timestamp = datetime.datetime.now().isoformat()
        
        data = {
            "station_id": self.station_id,
            "timestamp": timestamp,
            "temperature": temperature,
            "humidity": humidity,
            "co2": co2
        }
        
        return data
    
    def publish_data(self, data):
        """Publish sensor data to ThingSpeak using HTTP API"""
        try:
            # Prepare the parameters for ThingSpeak
            params = {
                "api_key": self.write_api_key,
                "field1": data['temperature'],
                "field2": data['humidity'],
                "field3": data['co2'],
                "field4": data['station_id']
            }
            
            print(f"Publishing to ThingSpeak via HTTP: {params}")
            
            # Send the HTTP request
            response = requests.get(self.api_url, params=params)
            
            # Check the response
            if response.status_code == 200:
                # ThingSpeak returns the entry ID or 0 if there's an error
                entry_id = response.text.strip()
                if entry_id and int(entry_id) > 0:
                    print(f"Data published successfully with entry ID: {entry_id}")
                    return True
                else:
                    print(f"Failed to publish data. Response: {response.text}")
                    return False
            else:
                print(f"HTTP error: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"Error publishing data: {e}")
            return False
    
    def run(self, interval=60, count=None):
        """Run the station, publishing data at the specified interval"""
        print(f"Starting HTTP Environmental Station {self.station_id}")
        print(f"Publishing to ThingSpeak channel {self.channel_id}")
        print(f"Interval: {interval} seconds")
        if count:
            print(f"Will publish {count} messages and then exit")
        else:
            print("Press Ctrl+C to stop")
        
        try:
            iteration = 0
            while True:
                # Generate and publish data
                data = self.generate_sensor_data()
                print(f"\nGenerated data: {json.dumps(data, indent=2)}")
                
                success = self.publish_data(data)
                if not success:
                    print("Failed to publish data")
                
                # Increment counter if we're doing a fixed number of publications
                if count is not None:
                    iteration += 1
                    if iteration >= count:
                        print(f"Published {count} messages. Exiting.")
                        break
                
                # Wait for next interval
                print(f"Waiting {interval} seconds before next publication...")
                sys.stdout.flush()  # Force output to be displayed immediately
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\nStation stopped by user")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HTTP Virtual Environmental Station")
    parser.add_argument("--station-id", help="Unique ID for the station", default=None)
    parser.add_argument("--channel-id", help="ThingSpeak channel ID", required=True)
    parser.add_argument("--write-key", help="ThingSpeak write API key", required=True)
    parser.add_argument("--interval", help="Data publishing interval in seconds", type=int, default=60)
    parser.add_argument("--count", help="Number of messages to publish (default: run indefinitely)", type=int, default=None)
    
    args = parser.parse_args()
    
    station = HttpEnvironmentalStation(
        station_id=args.station_id,
        channel_id=args.channel_id,
        write_api_key=args.write_key
    )
    
    station.run(interval=args.interval, count=args.count)