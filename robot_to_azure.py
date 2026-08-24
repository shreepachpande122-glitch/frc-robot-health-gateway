import json
import os
import ssl
import time

import ntcore
import paho.mqtt.client as mqtt


# ============================================================
# ROBOT SETTINGS
# ============================================================

TEAM_NUMBER = 548


# These MUST match what the robot publishes
BATTERY_TOPIC = "/SmartDashboard/RobotHealth/BatteryVoltage"
CURRENT_TOPIC = "/SmartDashboard/RobotHealth/TotalCurrent"
CPU_TOPIC = "/SmartDashboard/RobotHealth/CPU"
CAN_TOPIC = "/SmartDashboard/RobotHealth/CANUtilization"
BROWNOUT_TOPIC = "/SmartDashboard/RobotHealth/Brownout"


# ============================================================
# AZURE SETTINGS
# ============================================================

HOST = "shm-frc-robotics.azure-devices.net"
PORT = 8883

CLIENT_ID = "frc_robot_1"

USERNAME = (
    "shm-frc-robotics.azure-devices.net/"
    "frc_robot_1/?api-version=2021-04-12"
)

PASSWORD = os.getenv("AZURE_IOT_PASSWORD")


# Send data 10 times per second
SEND_DELAY = 0.1


# ============================================================
# MQTT
# ============================================================

azure_connected = False


def on_connect(client, userdata, flags, reason_code, properties):
    global azure_connected

    if reason_code == 0:
        azure_connected = True
        print("Connected to Azure IoT Hub")
    else:
        print(f"Azure connection failed: {reason_code}")


def on_disconnect(
    client,
    userdata,
    disconnect_flags,
    reason_code,
    properties
):
    global azure_connected

    azure_connected = False
    print(f"Disconnected from Azure: {reason_code}")


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
            f"FAILED: {sensor_name}"
        )


# ============================================================
# MAIN
# ============================================================

def main():

    if not PASSWORD:
        print("AZURE_IOT_PASSWORD is not set.")
        print()
        print(
            'Run: $env:AZURE_IOT_PASSWORD="YOUR SAS TOKEN"'
        )
        return


    # --------------------------------------------------------
    # NETWORKTABLES
    # --------------------------------------------------------

    nt = ntcore.NetworkTableInstance.getDefault()

    nt.startClient4(
        "FRC-Monitor360-Gateway"
    )

    nt.setServerTeam(
        TEAM_NUMBER
    )


    battery_sub = (
        nt
        .getDoubleTopic(BATTERY_TOPIC)
        .subscribe(float("nan"))
    )

    current_sub = (
        nt
        .getDoubleTopic(CURRENT_TOPIC)
        .subscribe(float("nan"))
    )

    cpu_sub = (
        nt
        .getDoubleTopic(CPU_TOPIC)
        .subscribe(float("nan"))
    )

    can_sub = (
        nt
        .getDoubleTopic(CAN_TOPIC)
        .subscribe(float("nan"))
    )

    brownout_sub = (
        nt
        .getBooleanTopic(BROWNOUT_TOPIC)
        .subscribe(False)
    )


    # --------------------------------------------------------
    # AZURE
    # --------------------------------------------------------

    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id=CLIENT_ID,
        protocol=mqtt.MQTTv311
    )

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect

    client.username_pw_set(
        USERNAME,
        PASSWORD
    )

    client.tls_set(
        cert_reqs=ssl.CERT_REQUIRED,
        tls_version=ssl.PROTOCOL_TLS_CLIENT
    )


    print("Connecting to Azure...")

    client.connect(
        HOST,
        PORT,
        60
    )

    client.loop_start()


    # --------------------------------------------------------
    # WAIT FOR ROBOT
    # --------------------------------------------------------

    print(
        f"Waiting for Team {TEAM_NUMBER} roboRIO..."
    )

    while not nt.isConnected():
        time.sleep(1)


    print("Connected to roboRIO!")
    print("Sending live robot data to Azure.")
    print("Press Ctrl+C to stop.")
    print()


    # --------------------------------------------------------
    # LIVE LOOP
    # --------------------------------------------------------

    try:

        while True:

            battery = battery_sub.get()
            current = current_sub.get()
            cpu = cpu_sub.get()
            can = can_sub.get()
            brownout = brownout_sub.get()


            if battery == battery:
                publish_sensor(
                    client,
                    "battery_voltage",
                    battery
                )


            if current == current:
                publish_sensor(
                    client,
                    "total_current",
                    current
                )


            if cpu == cpu:
                publish_sensor(
                    client,
                    "roboRIO_CPU",
                    cpu
                )


            if can == can:
                publish_sensor(
                    client,
                    "CAN_utilization",
                    can
                )


            publish_sensor(
                client,
                "brownout_status",
                1 if brownout else 0
            )


            time.sleep(
                SEND_DELAY
            )


    except KeyboardInterrupt:

        print()
        print("Stopped.")


    finally:

        client.loop_stop()
        client.disconnect()

        nt.stopClient()

        print("Disconnected.")


if __name__ == "__main__":
    main()