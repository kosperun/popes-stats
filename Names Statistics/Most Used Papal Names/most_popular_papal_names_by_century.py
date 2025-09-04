import pandas as pd
import bar_chart_race as bcr

# Load CSV
df = pd.read_csv("popes.csv")

# Extract year
df["start_year"] = df["start"].str[:4].astype(int)

# Count occurrences per year per name
counts = df.groupby(["start_year", "name"]).size().unstack(fill_value=0)

# Compute cumulative counts
counts_cum = counts.cumsum()

# Compute first year each cumulative count appears for each name
# This will be used as a tie-breaker: newer names with same count rise above older ones
first_count_year = pd.DataFrame(
    index=counts_cum.index, columns=counts_cum.columns, dtype=float
)
for name in counts_cum.columns:
    seen_counts = {}
    for year, value in counts_cum[name].items():
        if value not in seen_counts:
            seen_counts[value] = year
        first_count_year.at[year, name] = seen_counts[value]

# Invert the tie-breaker: higher first_count_year → higher bar
tie_nudge = first_count_year / 10_000_000  # very small fraction

# Add tie-breaking nudge to cumulative counts
counts_cum_nudge = counts_cum + tie_nudge

# Convert to float
counts_cum_nudge = counts_cum_nudge.astype(float)

# Repeat the last row to extend the final frame
extra_frames = 10  # number of extra periods to hold the last frame
last_row = counts_cum_nudge.iloc[[-1]]  # keep it as DataFrame
hold_frames = pd.concat([last_row] * extra_frames, ignore_index=False)
counts_cum_nudge_extended = pd.concat([counts_cum_nudge, hold_frames])

# Create the bar chart race
bcr.bar_chart_race(
    df=counts_cum_nudge_extended,
    filename="popes_names.mp4",
    orientation="h",
    sort="desc",
    n_bars=20,
    fixed_order=False,
    fixed_max=True,
    steps_per_period=10,
    period_length=500,
    interpolate_period=True,
    bar_size=0.95,
    filter_column_colors=True,
    period_template="{x:.0f}",
)
