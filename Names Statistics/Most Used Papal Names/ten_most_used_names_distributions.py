import pandas as pd
import matplotlib.pyplot as plt
import os

# ----------------------------
# Load data
# ----------------------------
df = pd.read_csv("popes.csv")

# Compute century
df["century"] = df["start"].str[:4].astype(int) // 100 + 1

# ----------------------------
# Top 10 most used names
# ----------------------------
top_names = df["name"].value_counts().head(10).index
df_top = df[df["name"].isin(top_names)]

# ----------------------------
# Pivot table: century x name
# ----------------------------
pivot = df_top.groupby(["century", "name"]).size().unstack(fill_value=0)

# ----------------------------
# Output directory
# ----------------------------
out_dir = "papal_name_charts"
os.makedirs(out_dir, exist_ok=True)

# ----------------------------
# Plot per name
# ----------------------------
for name in top_names:
    plt.figure(figsize=(10, 4))
    plt.plot(pivot.index, pivot[name], marker="o", linestyle="-")
    plt.title(f"Usage of Pope Name '{name}' by Century")
    plt.xlabel("Century")
    plt.ylabel("Number of Popes")
    plt.xticks(pivot.index)  # show all centuries
    plt.yticks(range(int(pivot[name].max()) + 1))  # integers only
    plt.grid(True, axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()

    # Save PNG
    filename = os.path.join(out_dir, f"{name}_by_century_line.png")
    plt.savefig(filename, dpi=300)
    plt.close()
