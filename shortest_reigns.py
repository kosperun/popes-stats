import math
import numpy as np
import pandas as pd
from datetime import date
import bar_chart_race as bcr


# ---------- helpers (same as yours) ----------
def parse_date(datestr: str) -> date:
    y, m, d = map(int, datestr[:10].split("-"))
    return date(y, m, d)


def to_float_year(datestr: str) -> float:
    y, m, d = map(int, datestr[:10].split("-"))
    return y + (m - 1) / 12 + (d - 1) / 365.25


# ---------- load data ----------
df = pd.read_csv("popes.csv")
df["start_f"] = df["start"].apply(to_float_year)
df["end_f"] = df["end"].apply(to_float_year)
df["name_full"] = df["name_full"].astype(str)  # ensure strings

# ---------- constants ----------
DAYS_PER_YEAR = 365.2425
period_length = 70  # ms per frame (adjust to taste)
n_bars = 20

# ---------- timeline (years, coarse step for speed) ----------
timeline = np.arange(int(df["start_f"].min()), int(df["end_f"].max()) + 1, 2)

# ---------- build frames: tenure in DAYS, only positive tenures ----------
records = []
for t in timeline:
    # tenure in YEARS at time t (0 for not-yet-started)
    tenure_years = np.clip(t - df["start_f"], 0, df["end_f"] - df["start_f"])
    # convert to DAYS
    tenure_days = tenure_years * DAYS_PER_YEAR

    # Series indexed by name_full
    s = pd.Series(tenure_days.values, index=df["name_full"])

    # Keep only popes that have actually started (tenure > 0)
    s = s[s > 0.0]

    # Sort ascending (shortest at top) and keep up to n_bars
    snapshot = s.sort_values(ascending=True).head(n_bars)

    records.append(snapshot)

# ---------- DataFrame with aligned columns; absent names -> NaN -> fill 0 ----------
race_df = pd.DataFrame(records, index=timeline).fillna(0)

# Round to integers (days) for cleaner display
race_df = race_df.round().astype(int)

# ---------- extend final frame so video doesn't cut off immediately ----------
extra_periods = math.ceil(5000 / period_length)
last_row = race_df.iloc[[-1]]
last_rows = pd.concat([last_row] * extra_periods, ignore_index=False)
race_df = pd.concat([race_df, last_rows])

# ---------- run animation (shortest at top) ----------
bcr.bar_chart_race(
    df=race_df,
    filename="papal_reigns_shortest_days.mp4",
    orientation="h",
    sort="asc",  # shortest tenures appear at top
    n_bars=n_bars,
    fixed_order=False,
    fixed_max=False,  # global max across race_df (display df) -> stable axis
    steps_per_period=10,
    interpolate_period=False,
    period_length=period_length,
    title="20 Shortest Papal Reigns (by days)",
    bar_size=0.95,
    filter_column_colors=True,
    period_template="{x:.0f}",  # integer year counter bottom-right
)
