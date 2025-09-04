import pandas as pd
import re

# Load CSV
df = pd.read_csv("names_by_successive_gaps.csv")


# Function to get century from the date string
def get_century(date_str):
    match = re.match(r"^(\d{2})\d{2}-", date_str)
    if match:
        century_number = int(match.group(1)) + 1  # +1 because 1100s = 12th century
        return century_number
    return None


# Apply century extraction
df["century"] = df["start"].apply(get_century)

# --- Average gap per century ---
grouped = df.groupby("century")["gap_from_previous"].agg(["sum", "count"]).reset_index()
grouped["average_gap"] = grouped["sum"] / grouped["count"]

print("Average gap per century:")
for _, row in grouped.sort_values("century").iterrows():
    print(
        f"{int(row['century'])}th century: Average gap = {row['average_gap']:.2f} years"
    )

# --- Sum of gaps per century ---
result = df.groupby("century")["gap_from_previous"].sum().reset_index()

print("\nSum of gaps per century:")
for _, row in result.sort_values("century").iterrows():
    print(
        f"{int(row['century'])}th century: Total gap = {row['gap_from_previous']:.2f} years"
    )
