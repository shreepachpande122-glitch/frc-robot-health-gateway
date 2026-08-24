import json
import os
import ssl
import time

import pandas as pd
import paho.mqtt.client as mqtt


CSV_FILE = "2026_05_01 16_36_12 Fri Qualification_108.csv"

HOST = "shm-frc-robotics.azure-devices.net"
PORT = 8883

CLIENT_ID = "frc_robot_1"

USERNAME = (
    "shm-frc-robotics.azure-devices.net/"
    "frc_robot_1/?api-version=2021-04-12"
)

PASSWORD = os.getenv("AZURE_IOT_PASSWORD")

SEND_DELAY = 0.1

connected = False


def on_connect(client, userdata, flags, reason_code, properties):
    global connected

    print(f"MQTT connect result: {reason_code}")

    if reason_code == 0:
        connected = True
        print("CONNECTED TO AZURE")
    else:
        print("AZURE CONNECTION FAILED")


def on_disconnect(
    client,
    userdata,
    disconnect_flags,
    reason_code,
    properties
):
    global connected

    connected = False

    print()
    print(f"DISCONNECTED FROM AZURE: {reason_code}")


def publish_sensor(client, sensor_name, value):

    topic = (
        f"devices/{CLIENT_ID}/messages/events/"
        f"{sensor_name}"
    )

    payload = {
        "sensor": sensor_name,
        "value": float(value),
        "ts": int(time.time() * 1000)
    }

    message = json.dumps(payload)

    result = client.publish(
        topic,
        message,
        qos=1
    )

    if result.rc == mqtt.MQTT_ERR_SUCCESS:
        print(
            f"SENT: {sensor_name} = {value}"
        )
    else:
        print(
            f"PUBLISH FAILED: {sensor_name}"
        )

        print(
            f"MQTT ERROR CODE: {result.rc}"
        )


def main():

    global connected

    if not PASSWORD:
        print("ERROR: AZURE_IOT_PASSWORD is not set")
        print()
        print(
            '$env:AZURE_IOT_PASSWORD="YOUR SAS TOKEN"'
        )
        return


    print("Loading CSV...")

    df = pd.read_csv(CSV_FILE)

    print(f"Loaded {len(df)} rows")


    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id=CLIENT_ID,
        protocol=mqtt.MQTTv311
    )

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect


    client.username_pw_set(
        username=USERNAME,
        password=PASSWORD
    )


    client.tls_set(
        cert_reqs=ssl.CERT_REQUIRED,
        tls_version=ssl.PROTOCOL_TLS_CLIENT
    )


    print()
    print("Connecting to Azure IoT Hub...")


    try:
        client.connect(
            HOST,
            PORT,
            keepalive=60
        )

    except Exception as e:
        print()
        print("CONNECTION ERROR:")
        print(e)
        return


    client.loop_start()


    # Wait up to 15 seconds for Azure
    for i in range(15):

        if connected:
            break

        print(
            f"Waiting for Azure... {i + 1}/15"
        )

        time.sleep(1)


    if not connected:

        print()
        print("Azure never connected.")
        print("DO NOT start publishing.")

        client.loop_stop()
        client.disconnect()

        return


    print()
    print("Azure connected successfully.")
    print("Starting telemetry replay...")
    print()


    try:

        for _, row in df.iterrows():

            # Stop immediately if Azure disconnects
            if not connected:

                print()
                print(
                    "Azure disconnected. "
                    "Stopping replay."
                )

                break


            voltage = row["Voltage"]

            if (
                pd.notna(voltage)
                and 0 <= voltage <= 20
            ):
                publish_sensor(
                    client,
                    "battery_voltage",
                    voltage
                )


            total_current = row["Total PDP"]

            if pd.notna(total_current):
                publish_sensor(
                    client,
                    "total_current",
                    total_current
                )


            cpu = row["roboRIO CPU"]

            if pd.notna(cpu):
                publish_sensor(
                    client,
                    "roboRIO_CPU",
                    cpu
                )


            can = row["CAN"]

            if pd.notna(can):
                publish_sensor(
                    client,
                    "CAN_utilization",
                    can
                )


            brownout = row["Brownout"]

            if pd.notna(brownout):

                publish_sensor(
                    client,
                    "brownout_status",
                    1 if bool(brownout) else 0
                )


            time.sleep(SEND_DELAY)


    except KeyboardInterrupt:
        print()
        print("Stopped by user.")


    finally:

        time.sleep(1)

        client.loop_stop()

        client.disconnect()

        print()
        print("Finished.")


if __name__ == "__main__":
    main()