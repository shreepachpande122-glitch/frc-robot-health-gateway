import pandas as pd

columns = [
    "Timestamp",
    "NT:/DriveState/Pose/translation/x",
    "NT:/DriveState/Pose/translation/y",
    "NT:/DriveState/Pose/rotation/value",
    "NT:/DriveState/Speeds/vx",
    "NT:/DriveState/Speeds/vy",
    "NT:/DriveState/Speeds/omega",
]

df = pd.read_csv(
    "robot_log_data.csv",
    usecols=columns,
    low_memory=False
)

# Carry the most recent value forward
data = df.ffill()

# Remove rows before all six telemetry values have appeared
data = data.dropna(subset=[
    "NT:/DriveState/Pose/translation/x",
    "NT:/DriveState/Pose/translation/y",
    "NT:/DriveState/Pose/rotation/value",
    "NT:/DriveState/Speeds/vx",
    "NT:/DriveState/Speeds/vy",
    "NT:/DriveState/Speeds/omega",
])

print(f"Complete telemetry rows: {len(data)}")
print(data.head(20).to_string(index=False))