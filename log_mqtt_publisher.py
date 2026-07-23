import json
import time

import pandas as pd
import paho.mqtt.client as mqtt


BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC = "shree/frc/robot548/telemetry"

COLUMNS = [
    "Timestamp",
    "NT:/DriveState/Pose/translation/x",
    "NT:/DriveState/Pose/translation/y",
    "NT:/DriveState/Pose/rotation/value",
    "NT:/DriveState/Speeds/vx",
    "NT:/DriveState/Speeds/vy",
    "NT:/DriveState/Speeds/omega",
]


def load_telemetry():
    df = pd.read_csv(
        "robot_log_data.csv",
        usecols=COLUMNS,
        low_memory=False,
    )

    df = df.ffill()

    df = df.dropna(subset=COLUMNS[1:])

    return df


def main():
    data = load_telemetry()

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.connect(BROKER, PORT, 60)
    client.loop_start()

    print(f"Loaded {len(data)} real telemetry rows")
    print("Publishing real robot telemetry. Press Ctrl+C to stop.")

    previous_timestamp = None

    try:
        for _, row in data.iterrows():
            timestamp = float(row["Timestamp"])

            telemetry = {
                "source": "wpilog_replay",
                "timestamp_seconds": round(timestamp, 3),
                "robot_position_x_m": round(
                    float(row["NT:/DriveState/Pose/translation/x"]), 4
                ),
                "robot_position_y_m": round(
                    float(row["NT:/DriveState/Pose/translation/y"]), 4
                ),
                "robot_heading_rad": round(
                    float(row["NT:/DriveState/Pose/rotation/value"]), 4
                ),
                "robot_velocity_x_mps": round(
                    float(row["NT:/DriveState/Speeds/vx"]), 4
                ),
                "robot_velocity_y_mps": round(
                    float(row["NT:/DriveState/Speeds/vy"]), 4
                ),
                "robot_angular_velocity_radps": round(
                    float(row["NT:/DriveState/Speeds/omega"]), 4
                ),
            }

            message = json.dumps(telemetry)

            client.publish(
                TOPIC,
                message,
                qos=0,
            )

            print("Published:", message)

            if previous_timestamp is not None:
                delay = timestamp - previous_timestamp

                if 0 < delay <= 1:
                    time.sleep(delay)
                else:
                    time.sleep(0.02)

            previous_timestamp = timestamp

    except KeyboardInterrupt:
        print("\nReplay stopped.")

    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()