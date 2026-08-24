# FRC Robot Health Monitoring Gateway

This project explores how FRC robot telemetry can be converted into
industrial asset-health data and transmitted through MQTT.

## Current Progress

- Created a synthetic FRC telemetry generator in Python
- Generated related values for battery voltage, current, temperature,
  speed, robot mode, and gyro heading
- Published telemetry as JSON through MQTT
- Created an MQTT subscriber to receive and display the telemetry
- Received a real WPILib log for future testing

## Current Data Flow

Synthetic FRC Data -> Python Publisher -> MQTT Broker -> Python Subscriber

## Future Data Flow

FRC Robot -> roboRIO -> NetworkTables -> Python Gateway -> MQTT ->
Cloud Platform -> HBK Monitor360

## Setup

Install the required package:

```bash
python -m pip install -r requirements.txt