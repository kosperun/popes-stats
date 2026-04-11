import csv
from datetime import date
from dateutil.relativedelta import relativedelta

# ----------------------------
# Load CSV
# ----------------------------
rows = []
with open("popes.csv") as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)

# ----------------------------
# Calculate age at cardinalate
# ----------------------------
data = []
for row in rows:
    start_year = int(row["start"][:4])
    if start_year < 1000:
        continue
    cardinalate = row["cardinalate_date"]
    birth = row["birth"]
    if not cardinalate or cardinalate == "NA" or not birth or birth == "NA":
        continue
    try:
        b = date.fromisoformat(birth[:10])
        c = date.fromisoformat(cardinalate[:10])
        delta = relativedelta(c, b)
        data.append({
            "name": row["name_full"],
            "pontificate": f"{row['start'][:4]}-{row['end'][:4]}",
            "years": delta.years,
            "months": delta.months,
            "days": delta.days,
        })
    except ValueError:
        continue

data.sort(key=lambda x: (x["years"], x["months"], x["days"]))

youngest = data[:10]
oldest = data[-10:][::-1]

# ----------------------------
# Print tables
# ----------------------------
def format_age(d):
    parts = [f"{d['years']}y"]
    if d["months"]:
        parts.append(f"{d['months']}m")
    if d["days"]:
        parts.append(f"{d['days']}d")
    return " ".join(parts)

print("YOUNGEST popes at cardinalate:")
print(f"{'#':<4} {'Name':<25} {'Pontificate':<15} {'Age at Cardinalate'}")
print("-" * 60)
for i, d in enumerate(youngest, 1):
    print(f"{i:<4} {d['name']:<25} {d['pontificate']:<15} {format_age(d)}")

print()
print("OLDEST popes at cardinalate:")
print(f"{'#':<4} {'Name':<25} {'Pontificate':<15} {'Age at Cardinalate'}")
print("-" * 60)
for i, d in enumerate(oldest, 1):
    print(f"{i:<4} {d['name']:<25} {d['pontificate']:<15} {format_age(d)}")
