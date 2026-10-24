from datetime import date

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import pandas as pd

OUTPUT_DIR = "Sainthood Statistics"
# Popes who lived on after their pontificate ended
DEATHS_AFTER_PONTIFICATE = {"Celestine V": "1296-05-19", "Benedict XVI": "2022-12-31"}
CATEGORIES = [
    ("Saint (venerated since antiquity)", "goldenrod"),
    ("Saint (canonised by a later pope)", "darkorange"),
    ("Blessed", "steelblue"),
    ("Venerable / Servant of God", "lightsteelblue"),
    ("Not beatified", "lightgrey"),
]


def parse_date(datestr: str) -> date:
    y, m, d = map(int, datestr[:10].split("-"))
    return date(y, m, d)


def years_between(earlier: date, later: date) -> float:
    return (later - earlier).days / 365.25


def category(row) -> str:
    if row["sainthood_status"] == "Saint":
        return CATEGORIES[1][0] if row["canonization"] else CATEGORIES[0][0]
    if row["sainthood_status"] == "Blessed":
        return CATEGORIES[2][0]
    if row["sainthood_status"] in ("Venerable", "Servant of God"):
        return CATEGORIES[3][0]
    return CATEGORIES[4][0]


df = pd.read_csv("popes.csv", keep_default_na=False)
# Benedict IX reigned three times; count each pope once
df = df.drop_duplicates(subset="name_full").reset_index(drop=True)
df["century"] = df["start"].str[:4].astype(int) // 100 + 1
df["category"] = df.apply(category, axis=1)
df["death"] = [DEATHS_AFTER_PONTIFICATE.get(r.name_full, r.end) for r in df.itertuples()]

# --- Status overview ---
print("## Status overview\n")
for name, _ in CATEGORIES:
    print(f"- {name}: {(df['category'] == name).sum()}")

first_non_saint = df[df["sainthood_status"] != "Saint"].iloc[0]
print(f"\nUnbroken run of saints from Peter: {first_non_saint['number'] - 1} popes, until {first_non_saint['name_full']}")
last_ancient = df[df["category"] == CATEGORIES[0][0]].iloc[-1]
print(f"Last pope venerated as a saint without formal canonisation: {last_ancient['name_full']} ({last_ancient['start'][:4]})")

by_century = pd.crosstab(df["century"], df["category"]).reindex(columns=[c for c, _ in CATEGORIES], fill_value=0)
print("\n## By century of pontificate\n")
print("| Century | " + " | ".join(c for c, _ in CATEGORIES) + " |")
print("| --- " * (len(CATEGORIES) + 1) + "|")
for century, counts in by_century.iterrows():
    print(f"| {century} | " + " | ".join(str(v) for v in counts.values) + " |")

# --- Time from death to beatification and canonisation ---
formal = df[(df["beatification"] != "") | (df["canonization"] != "")].copy()
formal["death_dt"] = formal["death"].apply(parse_date)
formal["to_beatification"] = [
    years_between(r.death_dt, parse_date(r.beatification)) if r.beatification else None for r in formal.itertuples()
]
formal["to_canonization"] = [
    years_between(r.death_dt, parse_date(r.canonization)) if r.canonization else None for r in formal.itertuples()
]
formal["first_recognition"] = formal[["to_beatification", "to_canonization"]].min(axis=1)
formal = formal.sort_values("first_recognition")

print("\n## Time from death to beatification and canonisation\n")
print("| # | Pope | Died | Beatified | Canonised | Death → beatification | Death → canonisation |")
print("| --- | --- | --- | --- | --- | --- | --- |")
for i, r in enumerate(formal.itertuples(), 1):
    beat = f"{r.beatification[:4]} by {r.beatified_by}" if r.beatification else "-"
    canon = f"{r.canonization[:4]} by {r.canonized_by}" if r.canonization else "-"
    to_beat = f"{r.to_beatification:.1f} years" if pd.notna(r.to_beatification) else "-"
    to_canon = f"{r.to_canonization:.1f} years" if pd.notna(r.to_canonization) else "-"
    print(f"| {i} | {r.name_full} | {r.death[:4]} | {beat} | {canon} | {to_beat} | {to_canon} |")

both = formal.dropna(subset=["to_beatification", "to_canonization"])
print("\nBeatification → canonisation:")
for r in both.itertuples():
    print(f"- {r.name_full}: {r.to_canonization - r.to_beatification:.1f} years")

# --- Recognitions per century (by date of the decree) ---
events = pd.concat(
    [
        pd.DataFrame({"year": formal.loc[formal["beatification"] != "", "beatification"].str[:4].astype(int), "type": "Beatification"}),
        pd.DataFrame({"year": formal.loc[formal["canonization"] != "", "canonization"].str[:4].astype(int), "type": "Canonisation"}),
    ]
)
events["century"] = events["year"] // 100 + 1
per_century = pd.crosstab(events["century"], events["type"]).reindex(range(11, 22), fill_value=0)
print("\n## Beatifications and canonisations of popes per century (by date of decree)\n")
print("| Century | Beatifications | Canonisations |")
print("| --- | --- | --- |")
for century, r in per_century.iterrows():
    print(f"| {century} | {r.get('Beatification', 0)} | {r.get('Canonisation', 0)} |")

# --- Popes who raised predecessors to the altars ---
raisers = pd.concat(
    [
        formal.loc[formal["beatified_by"] != "", ["beatified_by", "name_full"]].rename(columns={"beatified_by": "by"}).assign(act="beatified"),
        formal.loc[formal["canonized_by"] != "", ["canonized_by", "name_full"]].rename(columns={"canonized_by": "by"}).assign(act="canonised"),
    ]
)
print("\n## Popes who beatified or canonised other popes\n")
print("| Pope | Beatified | Canonised |")
print("| --- | --- | --- |")
for by, group in sorted(raisers.groupby("by"), key=lambda g: -len(g[1])):
    beat = ", ".join(group.loc[group["act"] == "beatified", "name_full"]) or "-"
    canon = ", ".join(group.loc[group["act"] == "canonised", "name_full"]) or "-"
    print(f"| {by} | {beat} | {canon} |")

# --- Plot: status by century ---
fig, ax = plt.subplots(figsize=(14, 7))
bottom = [0] * len(by_century)
for name, color in CATEGORIES:
    values = by_century[name].values
    ax.bar(by_century.index, values, bottom=bottom, color=color, label=name)
    bottom = [b + v for b, v in zip(bottom, values)]
ax.set_xlabel("Century of pontificate")
ax.set_ylabel("Number of popes")
ax.set_title("Sainthood Status of Popes by Century")
ax.set_xticks(by_century.index)
ax.legend()
ax.grid(True, axis="y", linestyle="--", alpha=0.7)
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/sainthood_status_by_century.png")

# --- Plot: time from death to recognition ---
fig, ax = plt.subplots(figsize=(12, 9))
y = range(len(formal))
ax.barh([i + 0.2 for i in y], formal["to_beatification"].fillna(0), height=0.4, color="steelblue", label="Death → beatification")
ax.barh([i - 0.2 for i in y], formal["to_canonization"].fillna(0), height=0.4, color="darkorange", label="Death → canonisation")
ax.set_yticks(list(y))
ax.set_yticklabels(formal["name_full"])
ax.invert_yaxis()
ax.set_xscale("log")
ax.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:g}"))
ax.set_xlabel("Years after death (log scale)")
ax.set_title("Time from Death to Beatification and Canonisation")
ax.legend(loc="lower right")
ax.grid(True, axis="x", linestyle="--", alpha=0.7)
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/time_from_death_to_recognition.png")
