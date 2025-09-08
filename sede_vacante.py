from datetime import datetime

import matplotlib.pyplot as plt
import pandas as pd


def parse_date(datestr: str):
    y, m, d = map(int, datestr[:10].split("-"))
    return datetime(y, m, d).date()


def format_days(days: float) -> str:
    days = int(round(days))
    if days >= 365:
        years = days // 365
        rem_days = days % 365
        return f"{years}y, {rem_days}d"
    else:
        return f"{days}d"


# --- Load data ---
df = pd.read_csv("popes.csv")
df["start_dt"] = df["start"].apply(parse_date)
df["end_dt"] = df["end"].apply(parse_date)

# Sort by start date and start from Pontian (number >= 18)
df = df[df["number"] >= 18].sort_values("start_dt").reset_index(drop=True)

# --- Compute gaps ---
gap_days, prev_names, prev_ends = [], [], []
prev_end, prev_name = None, None

for _, row in df.iterrows():
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

gaps_sorted = df.dropna(subset=["gap_days"]).sort_values(
    by=["gap_days", "start_dt"], ascending=[False, True]
)

# --- Print gaps ---
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

# --- Century aggregation ---
gaps_sorted["century"] = (gaps_sorted["prev_end_dt"].apply(lambda d: d.year)) // 100 + 1
century_stats = (
    gaps_sorted.groupby("century")
    .agg(
        avg_gap_days=("gap_days", "mean"),
        total_gap_days=("gap_days", "sum"),
        num_gaps=("gap_days", "count"),
    )
    .reset_index()
)
century_stats["avg_gap_str"] = century_stats["avg_gap_days"].apply(format_days)
century_stats["total_gap_str"] = century_stats["total_gap_days"].apply(format_days)

# --- Plots ---
# Average
plt.figure(figsize=(12, 6))
bars = plt.bar(
    century_stats["century"], century_stats["avg_gap_days"] / 30.4375, color="teal"
)
plt.xlabel("Century")
plt.ylabel("Average Sede Vacante (months)")
plt.title("Average Sede Vacante Duration by Century")
plt.xticks(century_stats["century"])
# Annotate bars
for bar, label in zip(bars, century_stats["avg_gap_str"]):
    plt.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height(),
        label,
        ha="center",
        va="bottom",
        fontsize=9,
    )
plt.tight_layout()
plt.savefig("average_sede_vacante_duration_by_century.png")

# Total
plt.figure(figsize=(12, 6))
bars = plt.bar(
    century_stats["century"],
    century_stats["total_gap_days"] / 365.25,
    color="steelblue",
)
plt.xlabel("Century")
plt.ylabel("Total Sede Vacante (years)")
plt.title("Total Sede Vacante Duration by Century")
plt.xticks(century_stats["century"])
# Annotate bars
for bar, label in zip(bars, century_stats["total_gap_str"]):
    plt.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height(),
        label,
        ha="center",
        va="bottom",
        fontsize=9,
    )
plt.tight_layout()
plt.savefig("total_sede_vacante_duration_by_century.png")

# Format strings for printing
century_stats["avg_gap_str"] = century_stats["avg_gap_days"].apply(format_days)
century_stats["total_gap_str"] = century_stats["total_gap_days"].apply(format_days)

# Sort by total gap for printing
century_stats_sorted = century_stats.sort_values("avg_gap_days", ascending=False)

# Print
print("\nSede Vacante per Century (sorted by average gap length):")
for _, row in century_stats_sorted.iterrows():
    print(
        f"{int(row['century'])}th century: "
        f"avg {row['avg_gap_str']}, total {row['total_gap_str']}, gaps: {row['num_gaps']}"
    )
    # Total and average for all time
total_days_all = gaps_sorted["gap_days"].sum()
avg_days_all = gaps_sorted["gap_days"].mean()

print("\nSede Vacante Overall (all centuries):")
print(f"Average gap: {format_days(avg_days_all)}")
print(f"Total gap: {format_days(total_days_all)}")
