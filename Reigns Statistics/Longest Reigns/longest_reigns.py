import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta
import bar_chart_race as bcr


def parse_date(datestr: str) -> date:
    """Parse YYYY-MM-DD from CSV (ignores time/zone)."""
    y, m, d = map(int, datestr[:10].split("-"))
    return date(y, m, d)


def format_tenure(start: str, end: str) -> str:
    """Return exact tenure in 'X years, Y months, Z days'."""
    start_dt = parse_date(start)
    end_dt = parse_date(end)
    diff = relativedelta(end_dt, start_dt)
    return f"{diff.years} years, {diff.months} months, {diff.days} days"


def format_date(datestr: str) -> str:
    """Format YYYY-MM-DD into 'Mon DD, YYYY' (e.g., Jan 1, 899)."""
    dt = parse_date(datestr)
    return dt.strftime("%b %d, %Y")


def to_float_year(datestr: str) -> float:
    y, m, d = map(int, datestr[:10].split("-"))
    return y + (m - 1) / 12 + (d - 1) / 365.25


df = pd.read_csv("popes.csv")
df["start_f"] = df["start"].apply(to_float_year)
df["end_f"] = df["end"].apply(to_float_year)

# Exact tenure for printing
df["tenure_fmt"] = df.apply(lambda row: format_tenure(row["start"], row["end"]), axis=1)

# Compute duration in days (for ranking)
df["duration_days"] = df.apply(
    lambda row: (parse_date(row["end"]) - parse_date(row["start"])).days, axis=1
)

# ----------------------------
# Print 20 longest reigns
# ----------------------------
top20 = df.sort_values("duration_days", ascending=False).head(20)
print("20 Longest Papal Reigns:")
for _, row in top20.iterrows():
    start_str = format_date(row["start"])
    end_str = format_date(row["end"])
    print(f"{row['name_full']} ({start_str} – {end_str}): {row['tenure_fmt']}")
# Assume top20 is your DataFrame of top 20 longest reigns
top20["start_year"] = top20["start"].apply(lambda s: int(s[:4]))
top20["century"] = top20["start_year"] // 100 + 1  # 1st century = years 1–100

century_counts = top20["century"].value_counts().sort_index()
print(century_counts)

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
