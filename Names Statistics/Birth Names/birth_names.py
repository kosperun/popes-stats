from collections import Counter, defaultdict

import matplotlib.pyplot as plt
import pandas as pd

OUTPUT_DIR = "Names Statistics/Birth Names"
# Gregory V (996) was the last pope of the first millennium recorded as changing his name;
# from him on, taking a new papal name became the rule.
FIRST_NAME_CHANGE_TRADITION = 138
TOP = 15

popes = pd.read_csv("popes.csv", keep_default_na=False).drop_duplicates(subset="name_full")
births = pd.read_csv(f"{OUTPUT_DIR}/birth_names.csv", keep_default_na=False)
births["given"] = births["given_names"].str.split(";")
births["english"] = births["given_names_english"].str.split(";")
births["first"] = births["english"].str[0]

first_counts = Counter(births["first"])
all_counts = Counter(name for names in births["english"] for name in names)
variants = defaultdict(Counter)
first_variants = defaultdict(Counter)
holders = defaultdict(list)
for row in births.itertuples():
    for original, english in zip(row.given, row.english):
        variants[english][original] += 1
    first_variants[row.first][row.given[0]] += 1
    holders[row.first].append(row.name_full)


def variant_str(name: str, forms=variants) -> str:
    return ", ".join(f"{v} ({c})" if c > 1 else v for v, c in forms[name].most_common())


print(f"Popes with a documented birth name: {len(births)}")
print(f"Distinct first names: {len(first_counts)}")

print(f"\n## Most common first given names\n")
print("| # | Name | Popes | Forms used | Popes |")
print("| --- | --- | --- | --- | --- |")
for i, (name, count) in enumerate(first_counts.most_common(TOP), 1):
    print(f"| {i} | {name} | {count} | {variant_str(name, first_variants)} | {', '.join(holders[name])} |")

print(f"\n## Most common given names, counting every given name\n")
print("| # | Name | Popes | Forms used |")
print("| --- | --- | --- | --- |")
for i, (name, count) in enumerate(all_counts.most_common(TOP), 1):
    print(f"| {i} | {name} | {count} | {variant_str(name)} |")

# --- Popes who kept their birth name ---
print("\n## Popes with a documented birth name who kept it as papal name\n")
for row in births.itertuples():
    regnal = popes.loc[popes["name_full"] == row.name_full, "name"].iloc[0]
    if row.first == regnal:
        print(f"- {row.name_full} ({row.given[0]})")


# --- Extended: assume early popes kept their names ---
documented = set(births["name_full"])
assumed = popes[(popes["number"] < FIRST_NAME_CHANGE_TRADITION) & ~popes["name_full"].isin(documented)]
extended_counts = first_counts + Counter(assumed["name"])
print(f"\n## Including {len(assumed)} earlier popes assumed to have kept their birth name\n")
print("| # | Name | Popes |")
print("| --- | --- | --- |")
for i, (name, count) in enumerate(extended_counts.most_common(TOP), 1):
    print(f"| {i} | {name} | {count} |")
print(f"\nPopes covered: {sum(extended_counts.values())}")

# --- Plots ---
for counts, forms, title, filename in [
    (first_counts, first_variants, "Most Common Birth Names of Popes (first given name)", "most_common_birth_names.png"),
    (all_counts, variants, "Most Common Given Names of Popes (all given names)", "most_common_given_names.png"),
]:
    top = counts.most_common(TOP)[::-1]
    fig, ax = plt.subplots(figsize=(12, 8))
    bars = ax.barh([n for n, _ in top], [c for _, c in top], color="steelblue")
    for bar, (name, _) in zip(bars, top):
        ax.text(
            bar.get_width() + 0.2,
            bar.get_y() + bar.get_height() / 2,
            variant_str(name, forms),
            va="center",
            fontsize=8,
        )
    ax.set_xlabel("Number of popes")
    ax.set_title(f"{title}\n{len(births)} popes with a documented birth name, mostly since the 10th century")
    ax.set_xlim(0, max(c for _, c in top) * 1.6)
    ax.grid(True, axis="x", linestyle="--", alpha=0.7)
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/{filename}")
