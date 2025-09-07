import math
import pandas as pd
import numpy as np
import bar_chart_race as bcr


# ----------------------------
# Helpers
# ----------------------------
def to_float_year(datestr: str) -> float:
    """Convert YYYY-MM-DD string into float year (year + fraction)."""
    y, m, d = map(int, datestr[:10].split("-"))
    return y + (m - 1) / 12 + (d - 1) / 365.25


# ----------------------------
# Load data
# ----------------------------
df = pd.read_csv("../../popes.csv")

# Convert start dates to float years
df["end_f"] = df["end"].apply(to_float_year)

# ----------------------------
# Compute "most remote usage" metric
# ----------------------------
# Only consider names used at least twice
counts = df["name"].value_counts()
reused_names = counts[counts >= 2].index
df_reused = df[df["name"].isin(reused_names)]

current_year = 2025.0
last_usage = df_reused.groupby("name")["end_f"].max()
usage_count = df_reused.groupby("name").size().apply(int)

# Metric: (years since last use) * number of usages
metric = (current_year - last_usage) * usage_count
# Combine into one DataFrame
result = pd.DataFrame({"count": usage_count.astype(int), "score": metric}).sort_values("score", ascending=False)

print("Top forgotten/popular names by this metric:")
for name, row in result.iterrows():
    print(f"{name} ({int(row['count'])}): {row['score']:.2f}")

# ----------------------------
# Optional: animate growth of metric over time
# ----------------------------
# For each year, compute metric up to that point
timeline = np.arange(int(df["end_f"].min()), int(current_year) + 1)
records = []

for t in timeline:
    df_active = df_reused[df_reused["end_f"] <= t]
    last_use = df_active.groupby("name")["end_f"].max()
    counts = df_active.groupby("name").size()
    val = (t - last_use) * counts
    records.append(val)

race_df = pd.DataFrame(records, index=timeline).fillna(0)

# Keep top 15 names per frame for readability
race_df = race_df.apply(lambda row: row.nlargest(15), axis=1).fillna(0)

# ----------------------------
# Extend final frame by ~5s
# ----------------------------
period_length = 100
extra_periods = math.ceil(5000 / period_length)  # number of extra periods to add
last_row = race_df.iloc[[-1]]
last_rows = pd.concat([last_row] * extra_periods, ignore_index=False)
race_df = pd.concat([race_df, last_rows])

# ----------------------------
# Bar chart race
# ----------------------------
bcr.bar_chart_race(
    df=race_df,
    filename="forgotten_names.mp4",
    orientation="h",
    sort="desc",
    n_bars=15,
    fixed_order=False,
    fixed_max=True,
    steps_per_period=10,
    period_length=70,
    interpolate_period=False,
    bar_size=0.95,
    title="The rise and neglect of papal names across history (top 15)",
    filter_column_colors=True,
    period_template="{x:.0f}",
)
