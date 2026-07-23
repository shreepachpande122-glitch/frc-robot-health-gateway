import json

import paho.mqtt.client as mqtt


BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC = "shree/frc/robot548/telemetry"


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("Connected to the MQTT broker.")
        client.subscribe(TOPIC)
        print(f"Listening on {TOPIC}")
    else:
        print(f"Connection failed: {reason_code}")


def on_message(client, userdata, message):
    try:
        telemetry = json.loads(message.payload.decode("utf-8"))

        print("\nReceived telemetry")
        print(f"Source: {telemetry.get('source')}")
        print(f"Timestamp: {telemetry.get('timestamp_seconds')} s")
        print(f"X position: {telemetry.get('robot_position_x_m')} m")
        print(f"Y position: {telemetry.get('robot_position_y_m')} m")
        print(f"Heading: {telemetry.get('robot_heading_rad')} rad")
        print(f"X velocity: {telemetry.get('robot_velocity_x_mps')} m/s")
        print(f"Y velocity: {telemetry.get('robot_velocity_y_mps')} m/s")
        print(
            "Angular velocity: "
            f"{telemetry.get('robot_angular_velocity_radps')} rad/s"
        )

    except json.JSONDecodeError:
        print("Received invalid JSON.")


def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(BROKER, PORT, 60)

    print("Waiting for telemetry. Press Ctrl+C to stop.")

    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("\nSubscriber stopped.")
    finally:
        client.disconnect()


if __name__ == "__main__":
    main()