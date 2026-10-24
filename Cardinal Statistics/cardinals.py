from collections import Counter
from datetime import date

import re

import matplotlib.pyplot as plt
import pandas as pd

OUTPUT_DIR = "Cardinal Statistics"
CONCLAVES = "Conclave Statistics/conclaves.csv"
TODAY = date.today()
# Ingravescentem aetatem (1970): cardinals who are 80 when the see falls vacant cannot vote
AGE_LIMIT_FROM = date(1971, 1, 1)
AGE_LIMIT = 80
# Death dates are missing for many medieval cardinals; without one, a cardinal is assumed dead
# this many years after creation (the longest recorded tenure is 60 years)
MAX_YEARS_WITHOUT_DEATH_DATE = 60
# Estimated electorates are trusted when they are within this share of Wikipedia's count
COVERAGE_TOLERANCE = 0.1


def parse_date(datestr):
    match = re.match(r"(\d{4})-(\d{2})-(\d{2})", datestr or "")
    return date(*map(int, match.groups())) if match else None


def ordinal(n):
    return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def years(earlier, later):
    return (later - earlier).days / 365.25


def living(frame, day):
    """Mask of cardinals created by `day` and still alive and in office on it."""
    created = frame["created_dt"].apply(lambda c: c is not None and c <= day)
    alive = [
        (d >= day) if d else (c is not None and years(c, day) < MAX_YEARS_WITHOUT_DEATH_DATE)
        for c, d in zip(frame["created_dt"], frame["death_dt"])
    ]
    in_office = frame["cardinal_until_dt"].apply(lambda u: u is None or u >= day)
    return created & pd.Series(alive, index=frame.index) & in_office


# --- Load ---
popes = pd.read_csv("popes.csv", keep_default_na=False)
pontificates = [
    (row.name_full, parse_date(row.start), parse_date(row.end) or TODAY) for row in popes.itertuples()
]

# Combined data from compare_cardinal_sources.py: Miranda's consistory lists for creation dates,
# creating popes and deaths; Wikidata for births, nationality and cardinals created after 2023
cardinals = pd.read_csv(f"{OUTPUT_DIR}/cardinals_combined.csv", keep_default_na=False)
for column in ("birth", "created", "cardinal_until", "death"):
    cardinals[f"{column}_dt"] = cardinals[column].apply(parse_date)
# Impossible dates: a birth after creation or death is discarded (the cardinal is kept);
# a creation after death drops the record
bad_birth = [bool(b and ((c and b > c) or (d and b > d))) for b, c, d in
             zip(cardinals["birth_dt"], cardinals["created_dt"], cardinals["death_dt"])]
cardinals.loc[bad_birth, "birth_dt"] = None
valid = [not (c and d and c > d) for c, d in zip(cardinals["created_dt"], cardinals["death_dt"])]
print(f"Cardinals: {len(cardinals)} ({dict(Counter(cardinals['source']))}); impossible birth dates discarded: "
      f"{sum(bad_birth)}; records dropped (created after death): {len(cardinals) - sum(valid)}")
cardinals = cardinals[valid].copy()


def creating_pope(created, precision):
    """The pope reigning on the creation date; for year-only dates, only if one pope reigned all year."""
    if not created:
        return ""
    if precision == "year":
        year_start, year_end = date(created.year, 1, 1), date(created.year, 12, 31)
        reigning = {name for name, start, end in pontificates if start <= year_end and end >= year_start}
        return reigning.pop() if len(reigning) == 1 else ""
    matches = [name for name, start, end in pontificates if start <= created <= end]
    return matches[-1] if matches else ""


pontificate_end = {}
for name, start, end in pontificates:
    pontificate_end[name] = max(end, pontificate_end.get(name, end))
# Cardinals only in Wikidata: the creating pope comes from Wikipedia's categories, or from the date.
# When Wikidata lacks the creation date, the earliest date it has is often a later promotion, so a date
# contradicting the category is replaced by the end of the creating pope's pontificate.
for index, row in cardinals[cardinals["source"] == "wikidata"].iterrows():
    category = row["created_by"].split(";")[0]
    by_date = creating_pope(row["created_dt"], row["created_precision"])
    if category and category != by_date:
        cardinals.at[index, "created_dt"] = pontificate_end[category]
        cardinals.at[index, "created_precision"] = "pontificate"
    cardinals.at[index, "created_by"] = category or by_date
# Cardinals created by antipopes did not vote in the conclaves of the recognised line
cardinals["antipope_creation"] = cardinals["created_by"].str.startswith("Antipope")
dated = cardinals[cardinals["created_dt"].notna()]
print(f"With a creation date: {len(dated)}; assigned to a pope: {(dated['created_by'] != '').sum()}")

# --- Coverage by century of creation ---
print("\n## Cardinals per century of creation\n")
print("| Century | Cardinals | Day-precise date | Known birth | Known nationality |")
print("| --- | --- | --- | --- | --- |")
dated = dated.assign(century=dated["created_dt"].apply(lambda d: d.year // 100 + 1))
for century, g in dated.groupby("century"):
    print(f"| {century} | {len(g)} | {(g['created_precision'] == 'day').mean():.0%} "
          f"| {g['birth_dt'].notna().mean():.0%} | {(g['country'] != '').mean():.0%} |")

# --- Cardinals created per pope ---
per_pope = dated[(dated["created_by"] != "") & ~dated["antipope_creation"]].groupby("created_by").size()
reign_years = {name: years(start, end) for name, start, end in pontificates}
print("\n## Popes who created the most cardinals\n")
print("| # | Pope | Cardinals created | Per year of pontificate |")
print("| --- | --- | --- | --- |")
for i, (pope, count) in enumerate(per_pope.sort_values(ascending=False).head(15).items(), 1):
    print(f"| {i} | {pope} | {count} | {count / max(reign_years[pope], 1):.1f} |")

# --- Ages and tenures ---
precise = cardinals[(cardinals["created_precision"] == "day") & cardinals["birth_dt"].notna()].copy()
# 1 January usually stands for an unknown day
precise = precise[(precise["birth"].str[5:] != "01-01") & (precise["created"].str[5:] != "01-01")]
precise["age_at_creation"] = [years(b, c) for b, c in zip(precise["birth_dt"], precise["created_dt"])]
# Younger than 7 is a data error (e.g. a birth date confused with a creation date)
precise = precise[precise["age_at_creation"] >= 7]
print("\n## Youngest cardinals at creation\n")
print("| # | Cardinal | Born | Created | Age | Created by |")
print("| --- | --- | --- | --- | --- | --- |")
for i, r in enumerate(precise.nsmallest(12, "age_at_creation").itertuples(), 1):
    print(f"| {i} | {r.name} | {r.birth} | {r.created} | {r.age_at_creation:.1f} | {r.created_by} |")
print("\n## Oldest cardinals at creation\n")
print("| # | Cardinal | Born | Created | Age | Created by |")
print("| --- | --- | --- | --- | --- | --- |")
for i, r in enumerate(precise.nlargest(10, "age_at_creation").itertuples(), 1):
    print(f"| {i} | {r.name} | {r.birth} | {r.created} | {r.age_at_creation:.1f} | {r.created_by} |")

# Exact dates at both ends, and not counting years as pope
tenure = cardinals[
    (cardinals["created_precision"] == "day") & cardinals["created_dt"].notna()
    & (cardinals["death_precision"] == "day") & (cardinals["became_pope"].astype(str) != "True")
].copy()
tenure["until"] = [u or d for u, d in zip(tenure["cardinal_until_dt"], tenure["death_dt"])]
tenure = tenure[tenure["until"].notna()]
tenure["years_as_cardinal"] = [years(c, u) for c, u in zip(tenure["created_dt"], tenure["until"])]
print("\n## Longest-serving cardinals\n")
print("| # | Cardinal | Created | Until | Years |")
print("| --- | --- | --- | --- | --- |")
for i, r in enumerate(tenure.nlargest(10, "years_as_cardinal").itertuples(), 1):
    print(f"| {i} | {r.name} | {r.created} | {r.until} | {r.years_as_cardinal:.1f} |")

# --- Italian share ---
print("\n## Italian share of new cardinals (where nationality is known)\n")
known = dated[dated["country"] != ""]
italian_share = known.groupby("century")["country"].apply(lambda s: (s == "Italy").mean())
for century, share in italian_share.items():
    print(f"- {ordinal(century)} century: {share:.0%} of {len(known[known['century'] == century])}")

# --- Electorate of each conclave ---
conclaves = pd.read_csv(CONCLAVES, keep_default_na=False)
conclaves = conclaves[~conclaves["antipope"].astype(str).eq("True")]
popes_by_name = popes.drop_duplicates(subset="name_full", keep="last").set_index("name_full")


def vacancy_start(elected):
    """The day the see fell vacant: the end of the previous pontificate."""
    number = popes_by_name.loc[elected, "number"]
    previous = popes[popes["number"] == number - 1].iloc[-1]
    return parse_date(previous["end"]), previous["name_full"]


rows = []
for c in conclaves.itertuples():
    vacant, predecessor = vacancy_start(c.elected)
    if not vacant:
        continue
    electorate = cardinals[living(cardinals, vacant) & ~cardinals["antipope_creation"]]
    if vacant >= AGE_LIMIT_FROM:
        electorate = electorate[electorate["birth_dt"].apply(lambda b: b is None or years(b, vacant) < AGE_LIMIT)]
    by_pope = Counter(electorate["created_by"])
    elected_creator = creating_pope(parse_date(popes_by_name.loc[c.elected, "cardinalate_date"]), "day")
    rows.append({
        "election": c.election, "year": vacant.year, "elected": c.elected, "predecessor": predecessor,
        "estimated": len(electorate), "wikipedia": pd.to_numeric(c.eligible_electors or c.electors, errors="coerce"),
        "by_predecessor": by_pope.get(predecessor, 0),
        "top_creators": ", ".join(f"{p or 'unknown'} {n}" for p, n in by_pope.most_common(3)),
        "elected_created_by": elected_creator,
    })
electorates = pd.DataFrame(rows)
electorates["coverage"] = electorates["estimated"] / electorates["wikipedia"]
trusted = electorates[(electorates["coverage"] - 1).abs() <= COVERAGE_TOLERANCE]

print(f"\n## Conclaves whose estimated electorate is within {COVERAGE_TOLERANCE:.0%} of Wikipedia's count\n")
print("| Conclave | Elected | Electors (Wikipedia) | Estimated | Created by predecessor | Main creators |")
print("| --- | --- | --- | --- | --- | --- |")
for r in trusted.itertuples():
    share = r.by_predecessor / r.estimated
    print(f"| {r.election} | {r.elected} | {int(r.wikipedia)} | {r.estimated} | {r.by_predecessor} ({share:.0%}) | {r.top_creators} |")
print(f"\nTrusted: {len(trusted)} of {electorates['wikipedia'].notna().sum()} conclaves with a Wikipedia count")

print("\n## Was the new pope a cardinal created by his predecessor?\n")
with_creator = electorates[electorates["elected_created_by"] != ""]
same = with_creator[with_creator["elected_created_by"] == with_creator["predecessor"]]
print(f"{len(same)} of {len(with_creator)} popes with a known cardinalate date were created by their immediate predecessor")
print("Not created by predecessor since 1800:", ", ".join(
    f"{r.elected} (by {r.elected_created_by})" for r in with_creator[with_creator["year"] >= 1800].itertuples()
    if r.elected_created_by != r.predecessor
))

# --- Plot: size of the College over time ---
checkpoints = [date(y, 1, 1) for y in range(1400, TODAY.year + 1)]
alive = [(living(cardinals, d) & ~cardinals["antipope_creation"]).sum() for d in checkpoints]
fig, ax = plt.subplots(figsize=(16, 7))
ax.plot(checkpoints, alive, color="steelblue", label="All living cardinals in Wikidata (1 January)")
ax.scatter(
    [date(int(y), 6, 30) for y in electorates.dropna(subset=["wikipedia"])["year"]],
    electorates.dropna(subset=["wikipedia"])["wikipedia"], color="indianred", s=14, zorder=3,
    label="Eligible electors at conclaves (Wikipedia); under 80 only since 1971",
)
ax.axhline(70, color="grey", linestyle=":", linewidth=1)
ax.text(date(1590, 1, 1), 72, "70: limit set by Sixtus V (1586)", fontsize=8, color="grey")
ax.set_ylabel("Cardinals")
ax.set_title("Size of the College of Cardinals, 1400–today")
ax.legend()
ax.grid(True, linestyle="--", alpha=0.7)
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/college_size.png")

# --- Plot: share of electors created by the predecessor ---
fig, ax = plt.subplots(figsize=(12, 11))
share = (trusted["by_predecessor"] / trusted["estimated"]).values[::-1]
labels = [f"{r.year} {r.elected} (after {r.predecessor})" for r in trusted.itertuples()][::-1]
bars = ax.barh(labels, share * 100, color="steelblue")
for bar, value in zip(bars, share):
    ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2, f"{value:.0%}", va="center", fontsize=8)
ax.set_xlabel("% of electors created by the previous pope")
ax.set_xlim(0, 105)
ax.tick_params(axis="y", labelsize=8)
ax.set_title("Share of Conclave Electors Created by the Previous Pope\n(conclaves where the reconstructed electorate matches Wikipedia within 10%)")
ax.grid(True, axis="x", linestyle="--", alpha=0.7)
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/electors_created_by_predecessor.png")
