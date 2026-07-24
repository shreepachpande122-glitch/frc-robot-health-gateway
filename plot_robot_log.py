import math
import mmap
import struct
from pathlib import Path

import matplotlib.pyplot as plt


# Exact name of your attached log file
LOG_NAME = "FRC_20250315_163507_MIBKN_Q12.wpilog"

# This finds the log in the same folder as this Python file
LOG_FILE = Path(__file__).resolve().parent / LOG_NAME

POSE_TOPIC = "NT:/DriveState/Pose"
SPEEDS_TOPIC = "NT:/DriveState/Speeds"
ENABLED_TOPIC = "DS:enabled"


def read_string(payload, position):
    length = int.from_bytes(
        payload[position:position + 4],
        "little"
    )

    position += 4

    text = payload[
        position:position + length
    ].decode("utf-8", errors="replace")

    return text, position + length


def read_start_record(payload):
    # Bytes 1 through 4 contain the new NetworkTables entry ID
    entry_id = int.from_bytes(payload[1:5], "little")

    position = 5

    topic_name, position = read_string(payload, position)

    return entry_id, topic_name


def iter_records(file_path):
    """
    Reads each record from the WPILib log.

    Returns:
        entry ID
        timestamp in seconds
        raw payload
    """

    with file_path.open("rb") as file:
        with mmap.mmap(
            file.fileno(),
            0,
            access=mmap.ACCESS_READ
        ) as log:

            if len(log) < 12 or log[:6] != b"WPILOG":
                raise ValueError(
                    "This is not a valid WPILib .wpilog file."
                )

            extra_header_length = int.from_bytes(
                log[8:12],
                "little"
            )

            position = 12 + extra_header_length

            while position < len(log):
                header = log[position]

                entry_length = (header & 0x03) + 1
                size_length = ((header >> 2) & 0x03) + 1
                timestamp_length = ((header >> 4) & 0x07) + 1

                header_length = (
                    1
                    + entry_length
                    + size_length
                    + timestamp_length
                )

                if position + header_length > len(log):
                    break

                entry_start = position + 1
                size_start = entry_start + entry_length
                timestamp_start = size_start + size_length

                entry_id = int.from_bytes(
                    log[entry_start:size_start],
                    "little"
                )

                payload_size = int.from_bytes(
                    log[size_start:timestamp_start],
                    "little"
                )

                timestamp_microseconds = int.from_bytes(
                    log[
                        timestamp_start:
                        timestamp_start + timestamp_length
                    ],
                    "little"
                )

                payload_start = position + header_length
                payload_end = payload_start + payload_size

                if payload_end > len(log):
                    break

                payload = log[payload_start:payload_end]

                timestamp_seconds = (
                    timestamp_microseconds / 1_000_000
                )

                yield entry_id, timestamp_seconds, payload

                position = payload_end


def find_longest_enabled_interval(events, final_time):
    """
    Finds the longest time period where the robot was enabled.
    This removes most disabled time before and after the match.
    """

    intervals = []
    start_time = None

    for timestamp, enabled in sorted(events):
        if enabled and start_time is None:
            start_time = timestamp

        elif not enabled and start_time is not None:
            intervals.append((start_time, timestamp))
            start_time = None

    if start_time is not None:
        intervals.append((start_time, final_time))

    if not intervals:
        return None

    return max(
        intervals,
        key=lambda interval: interval[1] - interval[0]
    )


def add_time_gaps(times, values, maximum_gap=0.15):
    """
    Adds blank breaks when there is a large gap between samples.
    This prevents unrelated sections from being connected.
    """

    graph_times = []
    graph_values = []

    previous_time = None

    for timestamp, value in zip(times, values):
        if (
            previous_time is not None
            and timestamp - previous_time > maximum_gap
        ):
            graph_times.append(float("nan"))
            graph_values.append(float("nan"))

        graph_times.append(timestamp)
        graph_values.append(value)

        previous_time = timestamp

    return graph_times, graph_values


def add_path_gaps(
    times,
    x_values,
    y_values,
    maximum_time_gap=0.15,
    maximum_position_jump=1.0
):
    """
    Breaks the path line when the pose suddenly jumps.
    Pose jumps can happen because of odometry or vision resets.
    """

    graph_x = []
    graph_y = []

    previous_time = None
    previous_x = None
    previous_y = None

    for timestamp, x_value, y_value in zip(
        times,
        x_values,
        y_values
    ):
        break_line = False

        if previous_time is not None:
            time_gap = timestamp - previous_time

            position_jump = math.hypot(
                x_value - previous_x,
                y_value - previous_y
            )

            if time_gap > maximum_time_gap:
                break_line = True

            if position_jump > maximum_position_jump:
                break_line = True

        if break_line:
            graph_x.append(float("nan"))
            graph_y.append(float("nan"))

        graph_x.append(x_value)
        graph_y.append(y_value)

        previous_time = timestamp
        previous_x = x_value
        previous_y = y_value

    return graph_x, graph_y


def main():
    if not LOG_FILE.exists():
        print(f"Could not find {LOG_NAME}")
        print(
            "Put the .wpilog file in the same folder "
            "as this Python file."
        )
        return

    entry_names = {}

    enabled_events = []
    pose_samples = []
    speed_samples = []

    final_time = 0.0

    print(f"Reading {LOG_NAME}...")

    for entry_id, timestamp, payload in iter_records(LOG_FILE):
        final_time = max(final_time, timestamp)

        # Entry 0 contains control records and topic definitions
        if entry_id == 0:
            # Control type 0 means a topic is being created
            if payload and payload[0] == 0:
                try:
                    new_entry_id, topic_name = read_start_record(
                        payload
                    )

                    entry_names[new_entry_id] = topic_name

                except (IndexError, UnicodeDecodeError):
                    pass

            continue

        topic_name = entry_names.get(entry_id)

        # Pose2d contains three doubles:
        # x position, y position, heading
        if topic_name == POSE_TOPIC and len(payload) >= 24:
            x, y, heading = struct.unpack(
                "<ddd",
                payload[:24]
            )

            pose_samples.append(
                (timestamp, x, y, heading)
            )

        # ChassisSpeeds contains three doubles:
        # vx, vy, omega
        elif topic_name == SPEEDS_TOPIC and len(payload) >= 24:
            vx, vy, omega = struct.unpack(
                "<ddd",
                payload[:24]
            )

            speed_samples.append(
                (timestamp, vx, vy, omega)
            )

        elif topic_name == ENABLED_TOPIC and payload:
            enabled = payload[0] != 0

            enabled_events.append(
                (timestamp, enabled)
            )

    print(f"Pose samples found: {len(pose_samples):,}")
    print(f"Speed samples found: {len(speed_samples):,}")

    if not pose_samples:
        print("No DriveState pose data was found.")
        return

    if not speed_samples:
        print("No DriveState speed data was found.")
        return

    enabled_interval = find_longest_enabled_interval(
        enabled_events,
        final_time
    )

    if enabled_interval is not None:
        start_time, end_time = enabled_interval

        print(
            "Using longest enabled period: "
            f"{end_time - start_time:.1f} seconds"
        )

        pose_samples = [
            sample
            for sample in pose_samples
            if start_time <= sample[0] <= end_time
        ]

        speed_samples = [
            sample
            for sample in speed_samples
            if start_time <= sample[0] <= end_time
        ]

    else:
        start_time = min(
            pose_samples[0][0],
            speed_samples[0][0]
        )

        print(
            "No enabled-state data was found. "
            "Using the entire log."
        )

    if not pose_samples or not speed_samples:
        print("No samples remained after filtering.")
        return

    pose_times = [
        sample[0] - start_time
        for sample in pose_samples
    ]

    x_positions = [
        sample[1]
        for sample in pose_samples
    ]

    y_positions = [
        sample[2]
        for sample in pose_samples
    ]

    headings = [
        sample[3]
        for sample in pose_samples
    ]

    speed_times = [
        sample[0] - start_time
        for sample in speed_samples
    ]

    x_velocities = [
        sample[1]
        for sample in speed_samples
    ]

    y_velocities = [
        sample[2]
        for sample in speed_samples
    ]

    angular_velocities = [
        sample[3]
        for sample in speed_samples
    ]

    speeds = [
        math.hypot(vx, vy)
        for vx, vy in zip(
            x_velocities,
            y_velocities
        )
    ]

    path_x, path_y = add_path_gaps(
        pose_times,
        x_positions,
        y_positions
    )

    graph_speed_times, graph_speeds = add_time_gaps(
        speed_times,
        speeds
    )

    graph_heading_times, graph_headings = add_time_gaps(
        pose_times,
        headings
    )

    graph_omega_times, graph_omega = add_time_gaps(
        speed_times,
        angular_velocities
    )

    output_folder = Path(__file__).resolve().parent

    # Robot path graph
    plt.figure()
    plt.plot(path_x, path_y)
    plt.xlabel("X position (meters)")
    plt.ylabel("Y position (meters)")
    plt.title("FRC Robot Path")
    plt.axis("equal")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(
        output_folder / "robot_path.png",
        dpi=160
    )

    # Speed graph
    plt.figure()
    plt.plot(graph_speed_times, graph_speeds)
    plt.xlabel("Time (seconds)")
    plt.ylabel("Speed (meters per second)")
    plt.title("Robot Speed Over Time")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(
        output_folder / "robot_speed.png",
        dpi=160
    )

    # Heading graph
    plt.figure()
    plt.plot(graph_heading_times, graph_headings)
    plt.xlabel("Time (seconds)")
    plt.ylabel("Heading (radians)")
    plt.title("Robot Heading Over Time")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(
        output_folder / "robot_heading.png",
        dpi=160
    )

    # Angular velocity graph
    plt.figure()
    plt.plot(graph_omega_times, graph_omega)
    plt.xlabel("Time (seconds)")
    plt.ylabel("Angular velocity (radians per second)")
    plt.title("Robot Angular Velocity Over Time")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(
        output_folder / "robot_angular_velocity.png",
        dpi=160
    )

    print()
    print(
        f"Enabled pose samples graphed: "
        f"{len(pose_samples):,}"
    )

    print(
        f"Enabled speed samples graphed: "
        f"{len(speed_samples):,}"
    )

    print(f"Maximum speed: {max(speeds):.2f} m/s")

    print()
    print("Saved robot_path.png")
    print("Saved robot_speed.png")
    print("Saved robot_heading.png")
    print("Saved robot_angular_velocity.png")

    plt.show()


if __name__ == "__main__":
    main()