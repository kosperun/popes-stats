import pandas as pd
import matplotlib.pyplot as plt

# Load dataset
df = pd.read_csv("popes.csv")

# Extract year manually from start string
df["start_year"] = df["start"].str[:4].astype(int)

# Compute century
df["century"] = (df["start_year"] - 1) // 100 + 1

# Count occurrences per name
name_total_counts = df["name"].value_counts()

# Keep only names with >= 5 occurrences
popular_names = name_total_counts[name_total_counts >= 9].index
df_filtered = df[df["name"].isin(popular_names)]

# Count occurrences per century
name_counts = df_filtered.groupby(["century", "name"]).size().reset_index(name="count")

# Pivot for stacked bar chart
pivot = name_counts.pivot(index="century", columns="name", values="count").fillna(0)

# Optional: sort columns by total occurrences for consistent stacking order
pivot = pivot[sorted(pivot.columns, key=lambda x: name_total_counts[x], reverse=True)]

# Plot
pivot.plot(kind="bar", stacked=True, figsize=(12, 6))
plt.title("Distribution of Most Common Papal Names by Century")
plt.xlabel("Century")
plt.ylabel("Number of Popes")
plt.legend(title="Papal Name", bbox_to_anchor=(1.05, 1), loc="upper left")
plt.tight_layout()
plt.show()
