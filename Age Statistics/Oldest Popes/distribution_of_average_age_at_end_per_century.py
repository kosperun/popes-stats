import matplotlib.pyplot as plt
import pandas as pd

# ----------------------------
# Load CSV
# ----------------------------
df = pd.read_csv("popes.csv")

# Ensure age_end is numeric
df["age_end"] = pd.to_numeric(df["age_end"], errors="coerce")

# Compute start year and map to centuries
df["start_year"] = df["start"].str[:4].astype(int)
df["century"] = df["start_year"] // 100 + 1

# ----------------------------
# Distribution by century
# ----------------------------
# Aggregate mean age per century
century_stats = (
    df.groupby("century")
    .agg(mean_age_end=("age_end", "mean"), pope_count=("age_end", "count"))
    .reset_index()
)

# Sort for printing: descending by mean age
century_stats_desc = century_stats.sort_values("mean_age_end", ascending=False)

print("Average age at pontificate end per century (DESC by mean age):")
for _, row in century_stats_desc.iterrows():
    print(
        f"{int(row['century']):>2}th century: {row['mean_age_end']:.2f} years ({int(row['pope_count'])} popes)"
    )

# --- Plot ---
fig, ax = plt.subplots(figsize=(12, 6))

bar_width = 0.6

# Outer bar: average age
ax.bar(
    century_stats["century"],
    century_stats["mean_age_end"],
    width=bar_width,
    color="steelblue",
    label="Average Age",
)

# Inner bar: pope count (thinner)
scale = century_stats["mean_age_end"].max() / century_stats["pope_count"].max()
pope_bars = ax.bar(
    century_stats["century"],
    century_stats["pope_count"] * scale,
    width=bar_width * 0.3,  # thinner
    color="lightcoral",
    label="Number of Popes",
)

# Annotate pope counts above the red bars
for rect, count in zip(pope_bars, century_stats["pope_count"]):
    height = rect.get_height()
    ax.text(
        rect.get_x() + rect.get_width() / 2,
        height + 0.5,  # slight offset
        str(count),
        ha="center",
        va="bottom",
        fontsize=9,
        fontweight="bold",
        color="darkred",
    )

# Labels and axes
ax.set_xlabel("Century")
ax.set_ylabel("Average Age / Scaled Pope Count")
ax.set_title("Average Age of Popes at Pontificate End by Century")
ax.set_xticks(century_stats["century"])
ax.legend()

plt.tight_layout()
plt.savefig("average_age_of_popes_at_end_by_century.png")
