import pandas as pd


# Helper: convert YYYY-MM-DD... to float year
def to_float_year(datestr: str) -> float:
    y, m, d = map(int, datestr[:10].split("-"))
    return y + (m - 1) / 12 + (d - 1) / 365.25


# Load data
df = pd.read_csv("popes.csv")

# Convert start date to float year
df["start_f"] = df["start"].apply(to_float_year)

# Count occurrences per name
counts = df["name"].value_counts()

# Only names used at least twice
reused_names = counts[counts >= 2].index

# Current year as float
current = pd.Timestamp.now()
current_f = current.year + (current.month - 1) / 12 + (current.day - 1) / 365.25

# Compute remote usage index
remote_index = {}
for name in reused_names:
    last_year = df[df["name"] == name]["start_f"].max()
    usage_count = counts[name]
    remote_index[name] = (current_f - last_year) * usage_count

# Sort descending
remote_index = pd.Series(remote_index).sort_values(ascending=False)
print(remote_index)
