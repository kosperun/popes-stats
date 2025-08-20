import pandas as pd
import numpy as np
import bar_chart_race as bcr
import math


def to_float_year(datestr: str) -> float:
    y, m, d = map(int, datestr[:10].split("-"))
    return y + (m - 1) / 12 + (d - 1) / 365.25


df = pd.read_csv("popes.csv")
df["start_f"] = df["start"].apply(to_float_year)
df["end_f"] = df["end"].apply(to_float_year)

# ----------------------------
# Build timeline with fewer points
# ----------------------------
timeline = np.arange(int(df["start_f"].min()), int(df["end_f"].max()) + 1, 2)

records = []
for t in timeline:
    df["tenure_at_t"] = np.clip(t - df["start_f"], 0, df["end_f"] - df["start_f"])
    snapshot = (
        df.set_index("name_full")["tenure_at_t"].sort_values(ascending=False).head(20)
    )
    records.append(snapshot)

race_df = pd.DataFrame(records, index=timeline).fillna(0)

# ----------------------------
# Extend final frame by ~5s
# ----------------------------
period_length = 100

extra_periods = math.ceil(5000 / period_length)  # number of extra periods to add
last_row = race_df.iloc[[-1]]
last_rows = pd.concat([last_row] * extra_periods, ignore_index=False)

race_df = pd.concat([race_df, last_rows])

# ----------------------------
# Animation
# ----------------------------
bcr.bar_chart_race(
    df=race_df,
    filename="papal_reigns.mp4",
    orientation="h",
    sort="desc",
    n_bars=20,
    fixed_order=False,
    fixed_max=True,
    steps_per_period=10,
    interpolate_period=False,
    period_length=period_length,
    title="20 Longest Papal Reigns in History",
    bar_size=0.95,
    filter_column_colors=True,
    period_template="{x:.0f}",
)
