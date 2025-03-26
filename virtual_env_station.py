import random
import time
import json
import paho.mqtt.client as mqtt
import uuid
import logging
import requests
from datetime import datetime
import sys
import socket

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Sensor:
    def __init__(self, name, min_value, max_value, unit):
        self.name = name
        self.min_value = min_value
        self.max_value = max_value
        self.unit = unit
    
    def generate_reading(self):
        value = random.uniform(self.min_value, self.max_value)
        return round(value, 2)

class EnvironmentalStation:
    def __init__(self, station_id=None):
        # Generate a unique ID if none is provided
        self.station_id = station_id or f"station_{uuid.uuid4().hex[:8]}"
        
        # Initialize sensors
        self.sensors = {
            "temperature": Sensor("Temperature", -50, 50, "Celsius"),
            "humidity": Sensor("Humidity", 0, 100, "%"),
            "co2": Sensor("CO2", 300, 2000, "ppm")
        }
        
        # Load configuration
        try:
            with open('config.json', 'r') as config_file:
                self.config = json.load(config_file)
        except Exception as e:
            logging.error(f"Error loading config.json: {e}")
            sys.exit(1)
        
        # ThingSpeak specific configuration
        self.channel_id = self.config["channel_id"]
        self.write_api_key = self.config["write_api_key"]
        self.read_api_key = self.config["read_api_key"]
        
        # MQTT settings
        self.broker = self.config.get("broker", "mqtt3.thingspeak.com")
        self.port = self.config.get("port", 1883)
        
        # Use the correct topic format based on broker
        if "thingspeak" in self.broker.lower():
            # ThingSpeak requires this specific topic format
            self.topic = f"channels/{self.channel_id}/publish/{self.write_api_key}"
            logging.info(f"Using ThingSpeak MQTT topic format: {self.topic}")
        else:
            # Generic topic format for other brokers
            self.topic = f"iot/environment/{self.station_id}"
            logging.info(f"Using generic MQTT topic format: {self.topic}")
        
        # REST API URL  
        self.rest_api_url = "https://api.thingspeak.com/update"
        
        # Initialize MQTT client with a unique client ID
        client_id = f"python_client_{self.station_id}_{int(time.time())}"
        self.client = mqtt.Client(client_id=client_id, clean_session=True)
        
        # Set callbacks
        self.client.on_connect = self.on_connect
        self.client.on_publish = self.on_publish
        self.client.on_disconnect = self.on_disconnect
        
        # Flag to track if we're using MQTT or REST
        self.using_mqtt = False
        self.connection_attempts = 0
        self.max_attempts = 3
        
        logging.info(f"Environmental Station {self.station_id} initialized with channel ID {self.channel_id}")
    
    def on_connect(self, client, userdata, flags, rc):
        connection_codes = {
            0: "Connection successful",
            1: "Connection refused - incorrect protocol version",
            2: "Connection refused - invalid client identifier",
            3: "Connection refused - server unavailable",
            4: "Connection refused - bad username or password",
            5: "Connection refused - not authorised"
        }
        if rc == 0:
            logging.info(f"Connected to MQTT broker: {self.broker}")
            self.using_mqtt = True
            self.connection_attempts = 0
        else:
            msg = connection_codes.get(rc, f"Unknown error code: {rc}")
            logging.error(f"Failed to connect to MQTT broker: {msg}")
            self.using_mqtt = False
    
    def on_publish(self, client, userdata, mid):
        logging.info(f"Message {mid} published successfully via MQTT")
    
    def on_disconnect(self, client, userdata, rc):
        if rc != 0:
            logging.warning(f"Unexpected disconnection from MQTT broker: {rc}")
        else:
            logging.info("Disconnected from MQTT broker")
        self.using_mqtt = False
    
    # Update your attempt_mqtt_connection method:
    def attempt_mqtt_connection(self):
        """Try to connect to MQTT broker with multiple attempts"""
        if self.connection_attempts >= self.max_attempts:
            logging.warning(f"Max connection attempts ({self.max_attempts}) reached. Using REST API.")
            return False
        
        self.connection_attempts += 1
        
        try:
            logging.info(f"Attempting to connect to {self.broker}:{self.port} (attempt {self.connection_attempts}/{self.max_attempts})")
            
            # For ThingSpeak MQTT, client ID is important
            if "thingspeak" in self.broker.lower():
                # Use channel ID as part of client ID for ThingSpeak
                client_id = self.config["username"]
                # Recreate the client with this ID
                self.client = mqtt.Client(client_id=client_id, clean_session=True)
                # Reassign callbacks
                self.client.on_connect = self.on_connect
                self.client.on_publish = self.on_publish
                self.client.on_disconnect = self.on_disconnect
                
                logging.info(f"Using client ID: {client_id}")
                logging.info(f"Setting ThingSpeak MQTT authentication with username: {self.config['username']}")
                
                # Set username and password (User API Key)
                self.client.username_pw_set(
                    username=self.config["username"],
                    password=self.config["mqtt_api_key"]
                )
                
                # Set the correct topic format
                self.topic = f"channels/{self.channel_id}/publish/{self.write_api_key}"
                logging.info(f"Using topic: {self.topic}")
            
            # Check if broker is reachable before attempting connection
            socket.setdefaulttimeout(5)
            try:
                socket.socket().connect(self.config["username"], self.config["username"], self.config["mqtt_password"])
                logging.info(f"Broker {self.broker}:{self.port} is reachable")
            except socket.error as e:
                logging.error(f"Broker {self.broker}:{self.port} is not reachable: {e}")
                return False
            
            # Connect to MQTT broker
            logging.info("Connecting to MQTT broker...")
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
            
            # Give time for connection to establish
            time.sleep(3)  # Increased wait time
            
            logging.info(f"Connection established? {self.using_mqtt}")
            return self.using_mqtt
        except Exception as e:  
            logging.error(f"MQTT connection error: {e}")
            return False
    
    def disconnect_mqtt(self):
        """Disconnect from MQTT if connected"""
        if hasattr(self, 'client'):
            try:
                self.client.loop_stop()
                self.client.disconnect()
                logging.info("Disconnected from MQTT broker")
            except:
                pass
        self.using_mqtt = False
    
    def generate_sensor_data(self):
        """Generate random sensor readings"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        temperature = self.sensors["temperature"].generate_reading()
        humidity = self.sensors["humidity"].generate_reading()
        co2 = self.sensors["co2"].generate_reading()
        
        data = {
            "station_id": self.station_id,
            "timestamp": timestamp,
            "temperature": temperature,
            "humidity": humidity,
            "co2": co2
        }
        
        return data
    
    def publish_data_mqtt(self, data):
        """Publish data using MQTT"""
        if not self.using_mqtt:
            return False
        
        try:
            # Format payload based on broker type
            if "thingspeak" in self.broker.lower():
                # ThingSpeak requires a comma-separated format: field1,field2,field3,status
                payload = f"{data['temperature']},{data['humidity']},{data['co2']},station_id:{self.station_id}"
                logging.info(f"Using ThingSpeak CSV format for payload: {payload}")
            else:
                # Use JSON format for other brokers
                payload = json.dumps(data)
                logging.info(f"Using JSON format for payload")
            
            logging.info(f"Publishing via MQTT to {self.topic}: Temperature={data['temperature']}°C, Humidity={data['humidity']}%, CO2={data['co2']}ppm")
            result = self.client.publish(self.topic, payload, qos=1)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logging.info("MQTT publish initiated successfully")
                return True
            else:
                logging.error(f"Failed to publish via MQTT: {result.rc}")
                return False
        except Exception as e:
            logging.error(f"Error publishing via MQTT: {e}")
            return False
    
    def publish_data_rest(self, data):
        """Publish data using ThingSpeak REST API"""
        field1 = data["temperature"]
        field2 = data["humidity"]
        field3 = data["co2"]
        
        # ThingSpeak payload
        payload = {
            "api_key": self.write_api_key,
            "field1": field1,
            "field2": field2,
            "field3": field3,
            "status": f"station_id:{self.station_id}"
        }
        
        try:
            logging.info(f"Publishing via REST: Temperature={field1}°C, Humidity={field2}%, CO2={field3}ppm")
            response = requests.get(self.rest_api_url, params=payload)
            if response.status_code == 200 and int(response.text) > 0:
                logging.info(f"Data published successfully via REST API (entry ID: {response.text})")
                return True
            else:
                logging.error(f"Failed to publish via REST API: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logging.error(f"Error publishing via REST API: {e}")
            return False
    
    def publish_data(self, data):
        """Try to publish using MQTT first, then fall back to REST if needed"""
        # For ThingSpeak, if we don't have MQTT credentials, just use REST API
        if "thingspeak" in self.broker.lower() and (
            "username" not in self.config or 
            "mqtt_api_key" not in self.config
        ):
            logging.info("Using REST API for ThingSpeak (MQTT credentials not available)")
            return self.publish_data_rest(data)
        
        # Try MQTT first if connected
        if self.using_mqtt:
            if self.publish_data_mqtt(data):
                return True
            else:
                logging.warning("MQTT publish failed, falling back to REST API")
                # Try to reconnect MQTT for next time
                self.disconnect_mqtt()
                self.attempt_mqtt_connection()
        
        # Fall back to REST API
        return self.publish_data_rest(data)
        
    def run(self, interval=60, duration=None, mqtt_enabled=True):
        """
        Run the environmental station, publishing data at specified intervals
        
        Args:
            interval: Time between readings in seconds (default: 60)
            duration: Total runtime in seconds, None for indefinite (default: None)
            mqtt_enabled: Whether to attempt MQTT connection (default: True)
        """
        # Try MQTT connection if enabled
        if mqtt_enabled:
            self.attempt_mqtt_connection()
        
        logging.info(f"Environmental Station {self.station_id} started")
        if self.using_mqtt:
            logging.info("Using MQTT for data transmission")
        else:
            logging.info("Using REST API for data transmission")
        
        start_time = time.time()
        iteration = 0
        
        try:
            while True:
                iteration += 1
                logging.info(f"Generating data (iteration {iteration})")
                data = self.generate_sensor_data()
                
                # Retry connecting to MQTT if needed
                if mqtt_enabled and not self.using_mqtt and self.connection_attempts < self.max_attempts:
                    self.attempt_mqtt_connection()
                
                success = self.publish_data(data)
                if not success:
                    logging.warning("Failed to publish data via any method. Will try again.")
                
                # Check if duration has elapsed
                if duration and (time.time() - start_time) >= duration:
                    logging.info(f"Duration of {duration}s reached. Stopping.")
                    break
                
                logging.info(f"Waiting {interval}s before next reading...")
                time.sleep(interval)
        except KeyboardInterrupt:
            logging.info("Station operation interrupted by user")
        finally:
            self.disconnect_mqtt()
            logging.info("Environmental Station stopped")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Run a virtual environmental station')
    parser.add_argument('--station-id', help='Custom station ID')
    parser.add_argument('--interval', type=int, default=30, help='Interval between readings in seconds')
    parser.add_argument('--duration', type=int, help='Duration to run in seconds')
    parser.add_argument('--mqtt', action='store_true', help='Force MQTT mode')
    parser.add_argument('--rest', action='store_true', help='Force REST mode')
    
    args = parser.parse_args()
    
    # Create and run an environmental station
    station = EnvironmentalStation(args.station_id)
    
    if args.rest:
        logging.info("Forcing REST API mode as requested")
        mqtt_enabled = False
    else:
        mqtt_enabled = True
    
    # Run station with specified parameters
    station.run(interval=args.interval, duration=args.duration, mqtt_enabled=mqtt_enabled)