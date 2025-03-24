# IoT Environmental Monitoring System

A cloud-based IoT system that collects environmental data (temperature, humidity, and CO2 levels) from virtual sensors using ThingSpeak as the backend service. The system supports both MQTT and REST API for data transmission.

## Assignment Overview

This project fulfills the requirements of Assignment 3 for CIS600 Internet of Things: Application Development (Spring 2025). It includes:

1. A cloud-based IoT system collecting data from virtual environmental sensors
2. A display for the latest sensor data from all sensors of a specified station
3. A display for historical sensor data from the last five hours

## System Architecture

The system consists of:

1. **Virtual Environmental Station**: Simulates an IoT device with temperature, humidity, and CO2 sensors
2. **ThingSpeak Backend**: Cloud-based data storage and processing platform
3. **Data Transmission**: Dual support for MQTT and REST API
4. **Data Visualization Tools**: Scripts to display current and historical sensor data

## Getting Started

### Prerequisites

- Python 3.7 or higher
- ThingSpeak account and channel set up
- Required Python packages (see `requirements.txt`)

### Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/iot-environmental-monitoring.git
   cd iot-environmental-monitoring
   ```

2. Install required packages:
   ```
   pip install -r requirements.txt
   ```

3. Configure your ThingSpeak settings:
   - Create a `config.json` file with your ThingSpeak channel details:
   ```json
   {
     "channel_id": "YOUR_CHANNEL_ID",
     "write_api_key": "YOUR_WRITE_API_KEY",
     "read_api_key": "YOUR_READ_API_KEY",
     "broker": "mqtt3.thingspeak.com",
     "port": 1883,
     "username": "YOUR_THINGSPEAK_USERNAME",
     "mqtt_api_key": "YOUR_USER_API_KEY",
     "use_mqtt": true
   }
   ```

### ThingSpeak Channel Setup

1. Create a ThingSpeak account at [thingspeak.com](https://thingspeak.com/)
2. Create a new channel with the following fields:
   - Field 1: Temperature (°C)
   - Field 2: Humidity (%)
   - Field 3: CO2 (ppm)
   - Status field: Station ID
3. Get your Channel ID, Write API Key, and Read API Key from the channel settings
4. Get your User API Key and username from your profile page

## Usage

### Running the System

1. Start the main program:
   ```
   python main.py
   ```

2. Choose from the menu options:
   - Start a virtual environmental station
   - Display latest sensor data
   - Display historical sensor data (last 5 hours)

### Direct Command Line Usage

You can also run components individually:

1. Start a virtual environmental station using MQTT (if possible) with fallback to REST:
   ```
   python main.py --station --interval 30
   ```

2. Start a virtual environmental station using REST API only:
   ```
   python main.py --station --interval 30 --rest
   ```

3. Display latest sensor data:
   ```
   python display_latest.py --refresh 10
   ```

4. Display historical data for a specific sensor:
   ```
   python display_historical.py temperature --hours 5
   ```

## Components

### Virtual Environmental Station (`virtual_env_station.py`)

Simulates an IoT device with multiple sensors:
- Temperature (-50°C to 50°C)
- Humidity (0% to 100%)
- CO2 (300ppm to 2000ppm)

The station can publish data via either MQTT or REST API to ThingSpeak, with automatic fallback to REST if MQTT connection fails.

### Display Latest Data (`display_latest.py`)

Shows the most recent readings from all sensors of a specified environmental station. Can refresh at a specified interval.

### Display Historical Data (`display_historical.py`)

Shows sensor data from the last five hours for a specified sensor type. Can display both tabular data and a time-series plot.

### HTTP Station Alternative (`http_station.py`)

An alternative implementation that uses only the HTTP REST API for data transmission.

### Main System Interface (`main.py`)

Provides a unified interface to all system components, with both interactive menu and command-line options.

## ThingSpeak Integration

### REST API Integration

The system uses ThingSpeak's REST API for reliable data transmission. The API endpoint used is:
```
https://api.thingspeak.com/update
```

### MQTT Integration

The system attempts to use ThingSpeak's MQTT broker for data transmission with the following configuration:
- Broker: mqtt3.thingspeak.com
- Port: 1883
- Topic format: channels/{channel_id}/publish/{write_api_key}
- Authentication: username and User API Key
- Payload format: CSV values for each field

If MQTT connection fails, the system automatically falls back to using the REST API.

## Troubleshooting

### MQTT Connection Issues

If you experience MQTT connection issues:
1. Verify your ThingSpeak username and User API Key are correct
2. Check network connectivity to mqtt3.thingspeak.com:1883
3. Consider using the REST API option if MQTT continues to be problematic

### Data Visibility Issues

If data doesn't appear in ThingSpeak:
1. Verify your channel ID and API keys are correct
2. Check the logs for successful publishing messages
3. Remember ThingSpeak has rate limits (15 seconds between updates)

## File Structure

```
├── config.json                  # ThingSpeak configuration
├── main.py                      # Main system interface
├── virtual_env_station.py       # Virtual sensor implementation (MQTT/REST)
├── http_station.py              # Alternative implementation (REST only)
├── display_latest.py            # Latest data display
├── display_historical.py        # Historical data display
├── requirements.txt             # Required Python packages
└── README.md                    # Project documentation
```

## Notes

- The system supports both MQTT and REST API for data transmission
- All data is stored in ThingSpeak and can be accessed through their web interface
- The system automatically falls back to REST API if MQTT connection fails
- Multiple virtual stations can be run concurrently

## License

This project is created for educational purposes as part of the CIS600 course.