import json
import random
import time

import paho.mqtt.client as mqtt


BROKER = "broker.hivemq.com"
PORT = 1883

# Make the topic more unique so another person does not accidentally
# publish to the exact same public topic.
TOPIC = "shree/frc/robot548/telemetry"


def create_client() -> mqtt.Client:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.connect(BROKER, PORT, 60)
    client.loop_start()
    return client


def main() -> None:
    client = create_client()

    match_time = 0
    motor_temperature = 30.0
    gyro_heading = 0.0

    print("Publishing synthetic FRC telemetry.")
    print("Press Ctrl+C to stop.")

    try:
        while True:
            match_time += 1

            if match_time <= 15:
                mode = "autonomous"
                robot_speed = random.uniform(1.5, 3.5)
                drive_current = random.uniform(25.0, 55.0)

            elif match_time <= 135:
                mode = "teleop"
                robot_speed = random.uniform(0.5, 4.5)
                drive_current = random.uniform(15.0, 65.0)

            elif match_time <= 150:
                mode = "endgame"
                robot_speed = random.uniform(0.2, 2.0)
                drive_current = random.uniform(30.0, 80.0)

            else:
                mode = "disabled"
                robot_speed = 0.0
                drive_current = random.uniform(2.0, 6.0)

            # Higher current causes the simulated battery voltage to sag.
            battery_voltage = 12.7 - (drive_current * 0.018)
            battery_voltage += random.uniform(-0.05, 0.05)

            # Motors warm up while operating and cool slightly while disabled.
            if mode == "disabled":
                motor_temperature -= 0.05
            else:
                motor_temperature += drive_current * 0.003

            motor_temperature = max(28.0, min(motor_temperature, 95.0))

            # Simulate the robot changing direction.
            gyro_heading += random.uniform(-8.0, 8.0)
            gyro_heading %= 360.0

            telemetry = {
                "source": "synthetic",
                "match_time_seconds": match_time,
                "robot_mode": mode,
                "enabled": mode != "disabled",
                "battery_voltage": round(battery_voltage, 2),
                "drive_current_amps": round(drive_current, 1),
                "motor_temperature_c": round(motor_temperature, 1),
                "robot_speed_mps": round(robot_speed, 2),
                "gyro_heading_degrees": round(gyro_heading, 1),
                "brownout_warning": battery_voltage < 10.5,
            }

            message = json.dumps(telemetry)

            result = client.publish(
                topic=TOPIC,
                payload=message,
                qos=0,
            )

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print("Published:", message)
            else:
                print("Publish failed with code:", result.rc)

            time.sleep(1)

    except KeyboardInterrupt:
        print("\nPublisher stopped.")

    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()