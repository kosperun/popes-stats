"""
AGES
1. By age and end
2. By age at start
3. By tenure
4. Distribution of popes ages - total and by centuries

NAMES
5. By biggest gap between two popes of the same name
6. By last used name in time
7. By most young name at start
8. By youngest name at end
9. By oldest name at start
10. By oldest name at end
11. By longest tenure name
12. By shortest tenure name
13. Distribution of popes names - total and by centuries

13. Add anitpopes to the list
"""

import csv
import datetime
import matplotlib.pyplot as plt

multiple_popes = {}


def calculate_age(start, end) -> float:
    start_date = datetime.datetime.fromisoformat(start.replace("Z", "+00:00"))
    end_date = datetime.datetime.fromisoformat(end.replace("Z", "+00:00"))
    return (end_date - start_date).days / 365.25


############## Replace age_start and age_end with exact ages ######################
with open("popes.csv", "r") as input_file:
    reader = csv.DictReader(input_file)
    rows = list(reader)

fieldnames = reader.fieldnames

for row in rows:
    birth = row["birth"]
    if birth == "NA":
        row["age_start"] = "NA"
        row["age_end"] = "NA"
    start = row["start"]
    end = row["end"]

    row["age_start"] = calculate_age(birth, start)
    row["age_end"] = calculate_age(birth, end)

# Write the new CSV file with updated exact ages
with open("popes_with_exact_ages.csv", "w", newline="") as output_file:
    writer = csv.DictWriter(output_file, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
######################################################################################


def sort_dict_by_average(name_ages_mapping):
    names_average_ages = {
        name: sum(ages) / len(ages) for name, ages in name_ages_mapping.items()
    }
    names_sorted_by_average_ages_ASC = sorted(
        names_average_ages.items(), key=lambda x: x[1]
    )
    names_sorted_by_average_ages_DESC = sorted(
        names_average_ages.items(), key=lambda x: x[1], reverse=True
    )
    return names_sorted_by_average_ages_ASC, names_sorted_by_average_ages_DESC


# def sort_by_average_end_age(popes_names_by_end_ages):
#     popes_names_by_average_end_age = {
#         name: sum(ages) / len(ages) for name, ages in popes_names_by_end_ages.items()
#     }
#     popes_names_by_average_end_age_ASC = sorted(
#         popes_names_by_average_end_age.items(), key=lambda x: x[1]
#     )
#     popes_names_by_average_end_age_DESC = sorted(
#         popes_names_by_average_start_age.items(), key=lambda x: x[1], reverse=True
#     )
#     with open("popes_names_sorted_by_age_at_death_DESC.csv", "w") as file:
#         writer = csv.writer(file)
#         writer.writerow(["name", "age"])
#         writer.writerows(popes_names_by_average_end_age_DESC)
#
#     with open("popes_names_sorted_by_age_at_death_ASC.csv", "w") as file:
#         writer = csv.writer(file)
#         writer.writerow(["name", "age"])
#         writer.writerows(popes_names_by_average_end_age_ASC)


def get_names_by_start_age(popes_names_by_start_ages):
    if row["name"] in popes_names_by_start_ages:
        popes_names_by_start_ages[row["name"]].append(
            float(calculate_age(row["birth"], row["start"]))
        )
    else:
        popes_names_by_start_ages[row["name"]] = [
            float(calculate_age(row["birth"], row["start"]))
        ]
    return popes_names_by_start_ages


def get_names_by_end_age(row, popes_names_by_end_ages):
    if row["age_end"] == "NA":
        return
    if row["name"] in popes_names_by_end_ages:
        popes_names_by_end_ages[row["name"]].append(
            float(calculate_age(row["birth"], row["end"]))
        )
    else:
        popes_names_by_end_ages[row["name"]] = [
            float(calculate_age(row["birth"], row["end"]))
        ]
    return popes_names_by_end_ages


with open("popes.csv") as file:
    reader = csv.DictReader(file)
    popes_data = []
    popes_data_by_century = {i: [] for i in range(21)}
    all_names = set()
    reccurrent_pope_names = set()

    # Get stats on all popes
    reader = list(reader)
    sorted_by_age_end = sorted(
        reader,
        key=lambda row: int(row["age_end"]) if row["age_end"] != "NA" else 0,
        reverse=True,
    )
    sorted_by_age_start = sorted(
        reader,
        key=lambda row: int(row["age_start"]) if row["age_start"] != "NA" else 0,
        reverse=True,
    )
    sorted_by_tenure = sorted(
        reader,
        key=lambda row: (
            float(row["tenure"])
            if row["tenure"] != "NA"
            else (
                datetime.datetime.today()
                - datetime.datetime.strptime(row["start"][:-1], "%Y-%m-%dT%H:%M:%S")
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
                        datetime.datetime.strptime(
                            data[i]["start"][:-1], "%Y-%m-%dT%H:%M:%S"
                        )
                        - datetime.datetime.strptime(
                            data[i - 1]["end"][:-1], "%Y-%m-%dT%H:%M:%S"
                        )
                    ).total_seconds()
                ) / (365.25 * 24 * 3600)
            data[i]["gap_from_previous"] = gap

    # Filter out popes with new names that didn't have predecessors
    popes_with_gaps = [
        value
        for data in multiple_popes.values()
        for value in data
        if value["gap_from_previous"] is not None
    ]

    sorted_by_gap = sorted(
        popes_with_gaps, key=lambda x: x["gap_from_previous"], reverse=True
    )

    with open("popes_sorted_by_gaps.csv", "w") as file:
        writer = csv.DictWriter(file, fieldnames=sorted_by_gap[0].keys())
        writer.writeheader()
        writer.writerows(sorted_by_gap)

    popes_names_by_start_ages = {}
    popes_names_by_average_start_age = {}
    popes_names_by_average_end_age = {}
    popes_names_by_end_ages = {}
    for row in reader:
        # Names by age at election and death
        if row["age_start"] != "NA":
            popes_names_by_start_ages = get_names_by_start_age(
                popes_names_by_start_ages
            )
        if row["age_end"] != "NA":
            popes_names_by_end_ages = get_names_by_end_age(row, popes_names_by_end_ages)

        # Distribution of popes ages at election and death
        if row["birth"] != "NA":
            data = {
                "number": row["number"],
                "name_full": row["name_full"],
                "name": row["name"],
                "suffix": row["suffix"],
                "canonization": row["canonization"],
                "birth_date": row["birth"],
                "start_date": row["start"],
                "end_date": row["end"],
                "start_age": row["age_start"],
                "end_age": row["age_end"],
            }
            popes_data.append(data)

            century = (
                datetime.datetime.fromisoformat(
                    row["start"].replace("Z", "+00:00")
                ).year
                // 100
            )
            popes_data_by_century[century].append(data)

names_sorted_by_average_ages_ASC = sort_dict_by_average()

    with open("popes_names_sorted_by_age_at_election_ASC.csv", "w") as file:
        writer = csv.writer(file)
        writer.writerow(["name", "age"])
        writer.writerows(names_sorted_by_average_ages_ASC)
    with open("popes_names_sorted_by_age_at_election_DESC.csv", "w") as file:
        writer = csv.writer(file)
        writer.writerow(["name", "age"])
        writer.writerows(names_sorted_by_average_ages_DESC)
# # Plotting the distribution of ages at election for all times
start_ages = [pope["start_age"] for pope in popes_data]

age_bins = range(18, 105)
plt.figure(figsize=(10, 6))
plt.hist(start_ages, bins=age_bins, color="skyblue", edgecolor="black", align="left")
plt.title("Distribution of Popes' Ages at Election")
plt.xlabel("Age at election")
plt.ylabel("Frequency")
plt.xticks(range(20, 110, 5))
plt.grid(axis="y")
plt.savefig("age_at_election_histogram.png")

# Plotting the distribution of ages at death for all times
end_ages = [pope["end_age"] for pope in popes_data]

age_bins = range(18, 105)
plt.figure(figsize=(10, 6))
plt.hist(end_ages, bins=age_bins, color="skyblue", edgecolor="black", align="left")
plt.title("Distribution of Popes' Ages at Death")
plt.xlabel("Age at death")
plt.ylabel("Frequency")
plt.xticks(range(20, 110, 5))
plt.grid(axis="y")
plt.savefig("age_at_death_histogram.png")


for century, data in popes_data_by_century.items():
    start_ages = [pope["start_age"] for pope in data]
    age_bins = range(18, 105)
    plt.figure(figsize=(10, 6))
    plt.hist(
        start_ages, bins=age_bins, color="skyblue", edgecolor="black", align="left"
    )
    plt.title(f"Distribution of Popes' Ages at Election in {century+1} century")
    plt.xlabel("Age at election")
    plt.ylabel("Frequency")
    plt.xticks(range(20, 110, 5))
    plt.grid(axis="y")
    plt.savefig(f"age_at_election_in_{century+1}_century_histogram.png")

    end_ages = [pope["end_age"] for pope in data]
    age_bins = range(18, 105)
    plt.figure(figsize=(10, 6))
    plt.hist(end_ages, bins=age_bins, color="skyblue", edgecolor="black", align="left")
    plt.title(f"Distribution of Popes' Ages at Death in {century+1} century")
    plt.xlabel("Age at death")
    plt.ylabel("Frequency")
    plt.xticks(range(20, 110, 5))
    plt.grid(axis="y")
    plt.savefig(f"age_at_death_{century+1}_histogram.png")
