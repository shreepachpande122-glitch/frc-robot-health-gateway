import glob
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


# Folder containing this Python file
PROJECT_FOLDER = Path(__file__).resolve().parent


def load_all_csv_files():
    csv_files = list(PROJECT_FOLDER.glob("*.csv"))

    if not csv_files:
        print("No CSV files found.")
        print("Put your robot CSV files in the same folder as this Python file.")
        return []

    datasets = []

    for file_path in csv_files:
        try:
            df = pd.read_csv(file_path)

            print()
            print(f"Loaded: {file_path.name}")
            print(f"Rows: {len(df)}")

            datasets.append((file_path.name, df))

        except Exception as e:
            print(f"Could not read {file_path.name}: {e}")

    return datasets


def clean_data(df):
    # Convert the time column into elapsed seconds
    if "Time" in df.columns:
        parsed_time = pd.to_datetime(
            df["Time"],
            format="%H:%M:%S.%f",
            errors="coerce"
        )

        if parsed_time.notna().any():
            start_time = parsed_time.iloc[0]

            df["Elapsed Time"] = (
                parsed_time - start_time
            ).dt.total_seconds()

        else:
            df["Elapsed Time"] = range(len(df))

    else:
        df["Elapsed Time"] = range(len(df))

    # Remove clearly impossible battery voltage values
    if "Voltage" in df.columns:
        df.loc[
            (df["Voltage"] < 0)
            | (df["Voltage"] > 20),
            "Voltage"
        ] = float("nan")

    return df


def graph_battery_voltage(df, name):
    if "Voltage" not in df.columns:
        return

    plt.figure()

    plt.plot(
        df["Elapsed Time"],
        df["Voltage"]
    )

    plt.xlabel("Time (seconds)")
    plt.ylabel("Battery Voltage (V)")
    plt.title(f"Battery Voltage - {name}")

    plt.grid(True)
    plt.tight_layout()


def graph_total_current(df, name):
    if "Total PDP" not in df.columns:
        return

    plt.figure()

    plt.plot(
        df["Elapsed Time"],
        df["Total PDP"]
    )

    plt.xlabel("Time (seconds)")
    plt.ylabel("Total Current (A)")
    plt.title(f"Total PDP Current - {name}")

    plt.grid(True)
    plt.tight_layout()


def graph_cpu(df, name):
    if "roboRIO CPU" not in df.columns:
        return

    plt.figure()

    plt.plot(
        df["Elapsed Time"],
        df["roboRIO CPU"]
    )

    plt.xlabel("Time (seconds)")
    plt.ylabel("CPU Usage (%)")
    plt.title(f"roboRIO CPU Usage - {name}")

    plt.grid(True)
    plt.tight_layout()


def graph_can(df, name):
    if "CAN" not in df.columns:
        return

    plt.figure()

    plt.plot(
        df["Elapsed Time"],
        df["CAN"]
    )

    plt.xlabel("Time (seconds)")
    plt.ylabel("CAN Utilization (%)")
    plt.title(f"CAN Utilization - {name}")

    plt.grid(True)
    plt.tight_layout()


def graph_pdp_channels(df, name):
    pdp_columns = [
        column
        for column in df.columns
        if column.startswith("PDP ")
    ]

    if not pdp_columns:
        return

    # Only graph channels that actually have current
    active_channels = []

    for column in pdp_columns:
        if df[column].abs().max() > 0.5:
            active_channels.append(column)

    if not active_channels:
        print(f"No active PDP channels found in {name}")
        return

    plt.figure(figsize=(12, 6))

    for column in active_channels:
        plt.plot(
            df["Elapsed Time"],
            df[column],
            label=column
        )

    plt.xlabel("Time (seconds)")
    plt.ylabel("Current (A)")
    plt.title(f"Active PDP Channels - {name}")

    plt.legend()
    plt.grid(True)
    plt.tight_layout()


def graph_brownout(df, name):
    if "Brownout" not in df.columns:
        return

    plt.figure()

    plt.step(
        df["Elapsed Time"],
        df["Brownout"].astype(int),
        where="post"
    )

    plt.xlabel("Time (seconds)")
    plt.ylabel("Brownout")
    plt.title(f"Brownout Status - {name}")

    plt.yticks(
        [0, 1],
        ["Normal", "Brownout"]
    )

    plt.grid(True)
    plt.tight_layout()


def graph_watchdog(df, name):
    if "Watchdog" not in df.columns:
        return

    plt.figure()

    plt.step(
        df["Elapsed Time"],
        df["Watchdog"].astype(int),
        where="post"
    )

    plt.xlabel("Time (seconds)")
    plt.ylabel("Watchdog")
    plt.title(f"Watchdog Status - {name}")

    plt.yticks(
        [0, 1],
        ["Normal", "Triggered"]
    )

    plt.grid(True)
    plt.tight_layout()


def print_summary(df, name):
    print()
    print(f"----- {name} -----")

    if "Voltage" in df.columns:
        valid_voltage = df["Voltage"].dropna()

        if not valid_voltage.empty:
            print(
                f"Battery voltage: "
                f"{valid_voltage.min():.2f} - "
                f"{valid_voltage.max():.2f} V"
            )

    if "Total PDP" in df.columns:
        print(
            f"Maximum total current: "
            f"{df['Total PDP'].max():.2f} A"
        )

    if "roboRIO CPU" in df.columns:
        print(
            f"Maximum roboRIO CPU: "
            f"{df['roboRIO CPU'].max():.1f}%"
        )

    if "CAN" in df.columns:
        print(
            f"Maximum CAN utilization: "
            f"{df['CAN'].max():.1f}%"
        )

    if "Brownout" in df.columns:
        brownouts = int(df["Brownout"].sum())

        print(
            f"Brownout samples: {brownouts}"
        )

    if "Watchdog" in df.columns:
        watchdogs = int(df["Watchdog"].sum())

        print(
            f"Watchdog samples: {watchdogs}"
        )


def main():
    datasets = load_all_csv_files()

    if not datasets:
        return

    for file_name, df in datasets:
        df = clean_data(df)

        print_summary(
            df,
            file_name
        )

        graph_battery_voltage(
            df,
            file_name
        )

        graph_total_current(
            df,
            file_name
        )

        graph_cpu(
            df,
            file_name
        )

        graph_can(
            df,
            file_name
        )

        graph_pdp_channels(
            df,
            file_name
        )

        graph_brownout(
            df,
            file_name
        )

        graph_watchdog(
            df,
            file_name
        )

    plt.show()


if __name__ == "__main__":
    main()