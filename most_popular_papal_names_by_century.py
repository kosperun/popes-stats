import pandas as pd
import bar_chart_race as bcr

df = pd.read_csv("popes.csv")

# Extract year manually from ISO-like string "0001-06-30T00:00:00Z"
df["start_year"] = df["start"].str[:4].astype(int)

# Count occurrences per year per name
counts = df.groupby(["start_year", "name"]).size().unstack(fill_value=0)

# Cumulative counts for bar growth
counts_cum = counts.cumsum()

# Make sure integers
counts_cum = counts_cum.astype(float)

counts_cum_nudge = counts_cum.copy()

# Get first year each pope appears
first_year = df.groupby("name")["start_year"].min()

# Apply nudge dynamically: newer first appearances push later names higher
for name in counts_cum.columns:
    debut = first_year[name]
    counts_cum_nudge.loc[debut:, name] += debut * 1e-5
# # Add a very small increment proportional to year to break exact ties
# counts_cum += (counts_cum.index.to_series() / 1_000_000_000).values[:, None]
#
# recency = df.groupby("name")["start_year"].max()
# counts_cum_nudge = counts_cum + recency * 1e-6
# # Break ties: for names with same cumulative count, use most recent year to nudge
# last_year = df.groupby("name")["start_year"].max()
# print(f"11111111 {last_year=}")
# counts_cum_nudge = counts_cum.copy()
# for i, name in enumerate(counts_cum.columns):
#     counts_cum_nudge[name] += last_year[name] * 1e-5  # tiny fraction to break ties
#
# print(f"22222222 {counts_cum_nudge=}")

# Create bar chart race
bcr.bar_chart_race(
    df=counts_cum_nudge,
    filename="popes_names.mp4",
    orientation="h",
    sort="desc",
    n_bars=30,
    fixed_order=False,
    fixed_max=True,
    steps_per_period=10,
    period_length=500,
    interpolate_period=True,
    bar_size=0.95,
    filter_column_colors=True,
)
