from datetime import datetime

import pandas as pd


def parse_date(datestr: str):
    y, m, d = map(int, datestr[:10].split("-"))
    return datetime(y, m, d).date()


df = pd.read_csv("popes.csv")
df["start_dt"] = df["start"].apply(parse_date)
df["end_dt"] = df["end"].apply(parse_date)

# Sort by start date
df = df.sort_values("start_dt").reset_index(drop=True)

# Only start from Pontian (number >= 18)
df = df[df["number"] >= 18].reset_index(drop=True)

# Calculate gaps
gap_days = []
prev_end = None
prev_name = None
prev_names = []

for idx, row in df.iterrows():
    if prev_end is None:
        gap_days.append(None)
        prev_names.append(None)
    else:
        gap_days.append((row["start_dt"] - prev_end).days)
        prev_names.append(prev_name)
    prev_end = row["end_dt"]
    prev_name = row["name_full"]

df["gap_days"] = gap_days
df["prev_name"] = prev_names

# Remove first row (no previous pope)
gaps_sorted = df.dropna(subset=["gap_days"]).sort_values("gap_days", ascending=False)

# Print
for _, row in gaps_sorted.iterrows():
    print(
        f"Between {row['prev_name']} (ended {row['end_dt']}) "
        f"and {row['name_full']} (started {row['start_dt']}): "
        f"{int(row['gap_days'])} days"
    )
