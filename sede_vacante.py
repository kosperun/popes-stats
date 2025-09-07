from datetime import datetime

import matplotlib.pyplot as plt
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
prev_names = []
prev_ends = []
prev_end = None
prev_name = None

for idx, row in df.iterrows():
    if prev_end is None:
        gap_days.append(None)
        prev_names.append(None)
        prev_ends.append(None)
    else:
        gap_days.append((row["start_dt"] - prev_end).days)
        prev_names.append(prev_name)
        prev_ends.append(prev_end)
    prev_end = row["end_dt"]
    prev_name = row["name_full"]

df["gap_days"] = gap_days
df["prev_name"] = prev_names
df["prev_end_dt"] = prev_ends

# Remove first row (no previous pope)
gaps_sorted = df.dropna(subset=["gap_days"]).sort_values(
    by=["gap_days", "start_dt"], ascending=[False, True]
)

# Print
for _, row in gaps_sorted.iterrows():
    prev_end = row["prev_end_dt"]
    start = row["start_dt"]
    gap_days = int(row["gap_days"])

    if abs(gap_days) >= 365:
        years = gap_days // 365
        days = gap_days % 365
        gap_str = f"{years} years, {days} days"
    else:
        gap_str = f"{gap_days} days"
    print(
        f" {row['prev_name']} (ended {prev_end.year}-{prev_end.month}-{prev_end.day}) "
        f"-- {row['name_full']} (started {start.year}-{start.month}-{start.day}): "
        f"{gap_str}"
    )

# Compute century based on prev_end year
gaps_sorted["century"] = (gaps_sorted["prev_end_dt"].apply(lambda d: d.year)) // 100 + 1

# Aggregate: average gap per century
century_stats = (
    gaps_sorted.groupby("century")
    .agg(
        avg_gap_days=("gap_days", "mean"),
        total_gap_days=("gap_days", "sum"),
        num_gaps=("gap_days", "count"),
        pope_count=("gap_days", "count"),
    )
    .reset_index()
)

# Convert avg_gap_days to years for readability
century_stats["avg_gap_months"] = century_stats["avg_gap_days"] / 30.4375

# Sort by century
century_stats = century_stats.sort_values("century")

# Plot
plt.figure(figsize=(12, 6))
plt.bar(century_stats["century"], century_stats["avg_gap_months"], color="teal")
plt.xlabel("Century")
plt.ylabel("Average Sede Vacante (months)")
plt.title("Average Sede Vacante Duration by Century")
plt.xticks(century_stats["century"])
plt.savefig("average_sede_vacante_duration_by_century.png")


# Convert total days to months
century_stats["total_gap_months"] = (
    century_stats["total_gap_days"] / 365.25  # 30.4375
)  # average month length

# Sort by century
century_total = century_stats.sort_values("century")

# Plot
plt.figure(figsize=(12, 6))
plt.bar(century_total["century"], century_total["total_gap_months"], color="steelblue")
plt.xlabel("Century")
plt.ylabel("Total Sede Vacante (years)")
plt.title("Total Sede Vacante Duration by Century")
plt.xticks(century_total["century"])
plt.tight_layout()
plt.savefig("total_sede_vacante_duration_by_century.png")
