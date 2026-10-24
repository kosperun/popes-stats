from datetime import date

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter

OUTPUT_DIR = "Conclave Statistics"


def parse_date(datestr: str):
    if not datestr:
        return None
    y, m, d = map(int, datestr[:10].split("-"))
    return date(y, m, d)


popes = pd.read_csv("popes.csv", keep_default_na=False).drop_duplicates(subset="name_full").set_index("name_full")
df = pd.read_csv(f"{OUTPUT_DIR}/conclaves.csv", keep_default_na=False)
# Elections of antipopes are listed for completeness; they are left out of the statistics
df = df[~df["antipope"].astype(str).eq("True")].copy()
unknown = set(df["elected"]) - set(popes.index)
assert not unknown, f"Unknown popes: {unknown}"

df["start_dt"] = df["start_date"].apply(parse_date)
# When the infobox gives only a month, fall back to the pope's election date from popes.csv
df["end_dt"] = [
    parse_date(end) or parse_date(popes.loc[pope, "start"]) for end, pope in zip(df["end_date"], df["elected"])
]
df["start_dt"] = [start or end for start, end in zip(df["start_dt"], df["end_dt"])]
# The list counts both the first and the last day, so a conclave from 12 to 13 March lasts 2 days
df["duration"] = [
    int(days) if days != "" else (end - start).days + 1
    for days, start, end in zip(df["duration_days"], df["start_dt"], df["end_dt"])
]
df["year"] = df["end_dt"].apply(lambda d: d.year)
df["century"] = df["year"] // 100 + 1
df["electors"] = pd.to_numeric(df["electors"], errors="coerce")
df["eligible_electors"] = pd.to_numeric(df["eligible_electors"], errors="coerce")
df["ballots"] = pd.to_numeric(df["ballots"], errors="coerce")
# Locations are given as "Building (City)" or just a building; reduce them to the city
CITY_KEYWORDS = {
    "Rome": "Rome", "Vatican": "Rome", "Viterbo": "Viterbo", "Arezzo": "Arezzo", "Lyon": "Lyon",
    "Konstanz": "Constance", "Cluny": "Cluny", "Avignon": "Avignon", "Perugia": "Perugia", "Naples": "Naples",
    "Pisa": "Pisa", "Ferrara": "Ferrara", "Anagni": "Anagni", "Terracina": "Terracina", "Verona": "Verona",
    "Venice": "Venice",
}
df["city"] = [next((city for key, city in CITY_KEYWORDS.items() if key in location), location) for location in df["location"]]


def fmt_days(days: int) -> str:
    if days < 365:
        return f"{days} days" if days != 1 else "1 day"
    years, rest = divmod(days, 365)
    return f"{years} y {rest} d"


print(f"Elections analysed: {len(df)} ({df['year'].min()}–{df['year'].max()})")
print(f"Total time spent electing popes: {fmt_days(df['duration'].sum())}")
print(f"Elections decided in a single day: {(df['duration'] == 1).sum()}")

print("\n## Longest elections\n")
print("| # | Election | Elected | Duration | Electors | Ballots |")
print("| --- | --- | --- | --- | --- | --- |")
for i, r in enumerate(df.sort_values("duration", ascending=False).head(12).itertuples(), 1):
    electors = int(r.electors) if pd.notna(r.electors) else "?"
    ballots = int(r.ballots) if pd.notna(r.ballots) else "?"
    print(f"| {i} | {r.election} | {r.elected} | {fmt_days(r.duration)} | {electors} | {ballots} |")

print("\n## Most ballots\n")
print("| # | Election | Elected | Ballots | Duration |")
print("| --- | --- | --- | --- | --- |")
for i, r in enumerate(df.dropna(subset=["ballots"]).sort_values("ballots", ascending=False).head(10).itertuples(), 1):
    print(f"| {i} | {r.election} | {r.elected} | {int(r.ballots)} | {fmt_days(r.duration)} |")

print("\n## By century\n")
print("| Century | Elections | Median duration | Longest | Avg. electors |")
print("| --- | --- | --- | --- | --- |")
for century, g in df.groupby("century"):
    longest = g.loc[g["duration"].idxmax()]
    electors = f"{g['electors'].mean():.0f}" if g["electors"].notna().any() else "?"
    print(f"| {century} | {len(g)} | {fmt_days(int(g['duration'].median()))} | {fmt_days(longest['duration'])} ({longest['elected']}) | {electors} |")

modern = df[df["year"] >= 1831]
print(f"\nSince 1831: {len(modern)} conclaves, longest {fmt_days(modern['duration'].max())}, "
      f"median {modern['duration'].median():.0f} days")

print("\n## Locations\n")
for city, count in df["city"].value_counts().items():
    years = ", ".join(str(y) for y in df.loc[df["city"] == city, "year"])
    print(f"- {city}: {count}" + (f" ({years})" if count <= 6 else ""))
outside = df[df["city"] != "Rome"]
print(f"\nOutside Rome: {len(outside)}; last: {outside.iloc[-1]['election']} ({outside.iloc[-1]['city']})")

print("\n## Absent electors (eligible but not present)\n")
absent = df.dropna(subset=["electors", "eligible_electors"]).copy()
absent["absent"] = absent["eligible_electors"] - absent["electors"]
for r in absent.sort_values("absent", ascending=False).head(8).itertuples():
    print(f"- {r.election}: {int(r.absent)} of {int(r.eligible_electors)} absent")

# --- Plot: duration of every election ---
fig, ax = plt.subplots(figsize=(16, 7))
ax.scatter(df["end_dt"], df["duration"], color="steelblue", s=25)
# Elections of similar length sit side by side, so label one of each pair on the left
LABEL_ON_LEFT = {"Nicholas IV", "Celestine V"}
for r in df[df["duration"] >= 300].itertuples():
    left = r.elected in LABEL_ON_LEFT
    ax.annotate(
        f"{r.elected} ({fmt_days(r.duration)})", (r.end_dt, r.duration), textcoords="offset points",
        xytext=(-8 if left else 8, -3), ha="right" if left else "left", fontsize=8,
    )
ax.set_yscale("log")
ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:g}"))
ax.set_ylabel("Duration in days (log scale)")
ax.set_title("Length of Papal Elections, 1061–2025")
ax.grid(True, linestyle="--", alpha=0.7)
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/conclave_durations.png")

# --- Plot: number of electors ---
electors = df.dropna(subset=["electors"])
fig, ax = plt.subplots(figsize=(16, 7))
# Points only: many 17th- and 18th-century counts are missing, and a line would bridge the gap
ax.scatter(electors["end_dt"], electors["electors"], color="steelblue", s=20, label="Electors present")
eligible = df.dropna(subset=["eligible_electors"])
ax.scatter(eligible["end_dt"], eligible["eligible_electors"], color="indianred", s=12, label="Eligible electors", zorder=3)
ax.set_ylabel("Cardinals")
ax.set_title("Number of Cardinal Electors at Papal Elections, 1061–2025")
ax.legend()
ax.grid(True, linestyle="--", alpha=0.7)
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/conclave_electors.png")
