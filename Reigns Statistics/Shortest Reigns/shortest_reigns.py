import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta
import math
import numpy as np
import bar_chart_race as bcr


def parse_date(datestr: str) -> date:
    y, m, d = map(int, datestr[:10].split("-"))
    return date(y, m, d)


def format_tenure(start: str, end: str) -> str:
    start_dt = parse_date(start)
    end_dt = parse_date(end)
    diff = relativedelta(end_dt, start_dt)
    return f"{diff.years} years, {diff.months} months, {diff.days} days"


def format_date(datestr: str) -> str:
    dt = parse_date(datestr)
    return dt.strftime("%b %d, %Y")


def to_float_year(datestr: str) -> float:
    y, m, d = map(int, datestr[:10].split("-"))
    return y + (m - 1) / 12 + (d - 1) / 365.25


# ----------------------------
# Load and prepare data
# ----------------------------
df = pd.read_csv("popes.csv")

#############################################################
# PRINT ALL REIGNS LESS THAN A YEAR
#############################################################
# Calculate reign length in days
df["duration_days"] = df.apply(
    lambda row: (parse_date(row["end"]) - parse_date(row["start"])).days, axis=1
)

# Human-readable format for reign length
df["tenure_fmt"] = df.apply(lambda row: format_tenure(row["start"], row["end"]), axis=1)

# ----------------------------
# All popes with reign < 1 year
# ----------------------------
short_reigns = df[df["duration_days"] < 365].sort_values("duration_days")

for i, row in short_reigns.iterrows():
    print(
        f"{row['name_full']}: {row['tenure_fmt']} "
        f"({format_date(row['start'])} – {format_date(row['end'])}, {row['duration_days']} days)"
    )
#############################################################
# BUILD BCR
#############################################################

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
