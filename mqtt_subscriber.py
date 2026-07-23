import json

import paho.mqtt.client as mqtt


BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC = "shree/frc/robot548/telemetry"


def on_connect(
    client: mqtt.Client,
    userdata,
    flags,
    reason_code,
    properties,
) -> None:
    if reason_code == 0:
        print("Connected to the MQTT broker.")
        client.subscribe(TOPIC)
        print(f"Listening on {TOPIC}")
    else:
        print(f"Connection failed. Reason code: {reason_code}")


def on_message(
    client: mqtt.Client,
    userdata,
    message: mqtt.MQTTMessage,
) -> None:
    try:
        decoded_message = message.payload.decode("utf-8")
        telemetry = json.loads(decoded_message)

        print("\nReceived telemetry")
        print(f"Source: {telemetry.get('source')}")
        print(f"Mode: {telemetry.get('robot_mode')}")
        print(f"Battery: {telemetry.get('battery_voltage')} V")
        print(f"Current: {telemetry.get('drive_current_amps')} A")
        print(f"Temperature: {telemetry.get('motor_temperature_c')} C")
        print(f"Speed: {telemetry.get('robot_speed_mps')} m/s")

    except UnicodeDecodeError:
        print("Received a message that was not valid text.")

    except json.JSONDecodeError:
        print("Received a message that was not valid JSON.")


def main() -> None:
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