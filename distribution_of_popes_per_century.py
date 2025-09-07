from datetime import date

import matplotlib.pyplot as plt
import pandas as pd


# --- helpers ---
def parse_date(datestr: str) -> date:
    y, m, d = map(int, datestr[:10].split("-"))
    return date(y, m, d)


# --- load data ---
df = pd.read_csv("popes.csv")

# compute start year
df["start_year"] = df["start"].str[:4].astype(int)

# map to centuries
df["century"] = ((df["start_year"] - 1) // 100 + 1).astype(int)

# adjust first century to start from 33 AD
first_century_mask = df["century"] == 1
df.loc[first_century_mask, "century"] = (
    df.loc[first_century_mask, "start_year"] - 33
) // 100 + 1

# remove any zero centuries just in case
df = df[df["century"] >= 1]

# count popes per century
pope_counts = df.groupby("century").size().reset_index(name="pope_count")

# --- print ASC sort by pope count ---
pope_counts_sorted = pope_counts.sort_values("pope_count", ascending=True)
print("Number of popes per century (ascending by count):")
for _, row in pope_counts_sorted.iterrows():
    print(f"{int(row['century'])}th century: {row['pope_count']} popes")

# --- matplotlib plot in chronological order ---
plt.figure(figsize=(10, 6))
plt.bar(
    pope_counts["century"].astype(str), pope_counts["pope_count"], color="steelblue"
)
plt.xlabel("Century")
plt.ylabel("Number of Popes")
plt.title("Distribution of Popes per Century")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("distribution_of_popes_over_centuries.png")
