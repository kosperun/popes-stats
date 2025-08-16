import pandas as pd
import bar_chart_race as bcr

df = pd.read_csv("popes.csv")

# Extract year manually from ISO-like string "0001-06-30T00:00:00Z"
df["start_year"] = df["start"].str[:4].astype(int)

# Count occurrences per year per name
counts = df.groupby(["start_year", "name"]).size().unstack(fill_value=0)

# Keep top 20 most used names overall
# top_names = counts.sum().sort_values(ascending=False).head(20).index
# counts = counts[top_names]

# Cumulative counts for bar growth
counts_cum = counts.cumsum()

# Make sure integers
counts_cum = counts_cum.astype(int)

# Create bar chart race
bcr.bar_chart_race(
    df=counts_cum,
    filename="popes_names.mp4",
    orientation="h",
    sort="desc",
    n_bars=20,
    fixed_order=False,
    fixed_max=True,
    steps_per_period=10,
    period_length=500,
    interpolate_period=False,
    label_bars=True,
    bar_size=0.95,
)
