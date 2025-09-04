import pandas as pd
import matplotlib.pyplot as plt
from datetime import date


# --- helpers ---
def parse_date(datestr: str) -> date:
    y, m, d = map(int, datestr[:10].split("-"))
    return date(y, m, d)


# --- load data ---
df = pd.read_csv("../popes.csv")

# compute duration in days
df["duration_days"] = df.apply(
    lambda row: (parse_date(row["end"]) - parse_date(row["start"])).days,
    axis=1,
)

# compute start year
df["start_year"] = df["start"].str[:4].astype(int)

# regular century calculation
df["century"] = ((df["start_year"] - 1) // 100 + 1).astype(int)

# adjust first century to start from 33 AD
first_century_mask = df["century"] == 1
df.loc[first_century_mask, "century"] = (df.loc[first_century_mask, "start_year"] - 33) // 100 + 1

# remove any zero century just in case
df = df[df["century"] >= 1]

# group: average reign + count of popes
avg_reign = (
    df.groupby("century")
    .agg(
        avg_duration_days=("duration_days", "mean"),
        pope_count=("duration_days", "count"),
    )
    .reset_index()
)
avg_reign["avg_reign_years"] = avg_reign["avg_duration_days"] / 365.25

# sort descending by average reign
avg_reign_sorted = avg_reign.sort_values("avg_reign_years", ascending=False)

# --- print ---
print("Average papal reign by century (sorted by DESC):\n")
for _, row in avg_reign_sorted.iterrows():
    print(
        f"{int(row['century'])}th century: " f"{row['avg_reign_years']:.2f} years " f"({int(row['pope_count'])} popes)"
    )

# --- plot ---
plt.figure(figsize=(10, 6))
plt.bar(avg_reign["century"], avg_reign["avg_reign_years"], color="steelblue")
plt.xlabel("Century")
plt.ylabel("Average Reign Length (years)")
plt.title("Average Papal Reign Length by Century")
plt.xticks(avg_reign["century"])
plt.tight_layout()
plt.savefig("pontificate_lengths_distribution.png")
