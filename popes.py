"""
1. By age and end
2. By age at start
3. By tenure
4. By biggest gap between two popes of the same name
5. By last used name in time
6. By most young name at start
7. By youngest name at end
8. By oldest name at start
9. By oldest name at end
10. By longest tenure name
"""

import csv
import datetime

multiple_popes = {}

with open("Downloads/popes.csv") as file:
    reader = csv.DictReader(file)
    all_names = set()
    reccurrent_pope_names = set()

    # Get stats on all popes
    reader = list(reader)
    sorted_by_age_end = sorted(
        reader, key=lambda row: int(row["age_end"]) if row["age_end"] != "NA" else 0, reverse=True
    )
    sorted_by_age_start = sorted(
        reader, key=lambda row: int(row["age_start"]) if row["age_start"] != "NA" else 0, reverse=True
    )
    sorted_by_tenure = sorted(
        reader,
        key=lambda row: (
            float(row["tenure"])
            if row["tenure"] != "NA"
            else (
                datetime.datetime.today() - datetime.datetime.strptime(row["start"][:-1], "%Y-%m-%dT%H:%M:%S")
            ).total_seconds()
            / (365.25 * 24 * 3600)
        ),
        reverse=True,
    )

    # Get stats on reccurrent popes names
    for row in reader:
        all_names.add(row["name"])
        if len(row["name_full"].split(" ")) > 1:
            reccurrent_pope_names.add(row["name"])
            if (name := row.pop("name")) in multiple_popes:
                multiple_popes[name].append(row)
            else:
                multiple_popes[name] = [row]

with open("popes_by_age_end.csv", "w") as file:
    writer = csv.DictWriter(file, fieldnames=sorted_by_age_end[0].keys())
    writer.writeheader()
    writer.writerows(sorted_by_age_end)

with open("popes_by_age_start.csv", "w") as file:
    writer = csv.DictWriter(file, fieldnames=sorted_by_age_start[0].keys())
    writer.writeheader()
    writer.writerows(sorted_by_age_start)

with open("popes_by_tenure.csv", "w") as file:
    writer = csv.DictWriter(file, fieldnames=sorted_by_tenure[0].keys())
    writer.writeheader()
    writer.writerows(sorted_by_tenure)

# Gaps between popes with the same names
for name, data in multiple_popes.items():
    for i in range(len(data)):
        if i == 0:
            gap = None
        else:
            gap = float(
                (
                    datetime.datetime.strptime(data[i]["start"][:-1], "%Y-%m-%dT%H:%M:%S")
                    - datetime.datetime.strptime(data[i - 1]["end"][:-1], "%Y-%m-%dT%H:%M:%S")
                ).total_seconds()
            ) / (365.25 * 24 * 3600)
        data[i]["gap_from_previous"] = gap

# Filter out popes with new names that didn't have predecessors
popes_with_gaps = [
    value for data in multiple_popes.values() for value in data if value["gap_from_previous"] is not None
]

sorted_by_gap = sorted(popes_with_gaps, key=lambda x: x["gap_from_previous"], reverse=True)

with open("popes_sorted_by_gaps.csv", "w") as file:
    writer = csv.DictWriter(file, fieldnames=sorted_by_gap[0].keys())
    writer.writeheader()
    writer.writerows(sorted_by_gap)

# Sorted by the most remote last used name
