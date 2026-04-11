import matplotlib.pyplot as plt
import csv

# ----------------------------
# Load CSV
# ----------------------------
rows = []
with open("popes.csv") as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)

# ----------------------------
# Filter and aggregate
# ----------------------------
# Only popes starting from 1400 with valid cardinalate data
century_data = {}

for row in rows:
    start_year = int(row["start"][:4])
    if start_year < 1400:
        continue
    years_str = row["years_as_cardinal"]
    if not years_str or years_str == "NA":
        continue
    try:
        years = float(years_str)
    except ValueError:
        continue

    century = start_year // 100 + 1
    if century not in century_data:
        century_data[century] = []
    century_data[century].append(years)

centuries = sorted(century_data.keys())
mean_years = [sum(century_data[c]) / len(century_data[c]) for c in centuries]
pope_counts = [len(century_data[c]) for c in centuries]

# Print summary
print("Average years served as cardinal before becoming pope per century:")
for c, mean, count in zip(centuries, mean_years, pope_counts):
    print(f"  {c}th century: {mean:.2f} years ({count} popes)")

# ----------------------------
# Plot
# ----------------------------
fig, ax = plt.subplots(figsize=(12, 6))

bar_width = 0.6

bars = ax.bar(
    centuries,
    mean_years,
    width=bar_width,
    color="steelblue",
)

# Annotate mean values above bars
for rect, mean in zip(bars, mean_years):
    ax.text(
        rect.get_x() + rect.get_width() / 2,
        rect.get_height() + 0.3,
        f"{mean:.1f}",
        ha="center",
        va="bottom",
        fontsize=9,
        fontweight="bold",
        color="steelblue",
    )

ax.set_xlabel("Century")
ax.set_ylabel("Average Years as Cardinal")
ax.set_title("Average Years Popes Served as Cardinals Before Election by Century (from 1400)")
ax.set_xticks(centuries)
ax.grid(True, axis="y", linestyle="--", alpha=0.7)


plt.tight_layout()
plt.savefig("Age Statistics/Cardinalate/average_years_as_cardinal_by_century.png")
