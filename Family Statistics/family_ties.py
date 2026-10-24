import pandas as pd

OUTPUT_DIR = "Family Statistics"
RELIABLE = ("documented", "probable")

popes = pd.read_csv("popes.csv", keep_default_na=False)
# Benedict IX reigned three times; use his first pontificate
popes = popes.drop_duplicates(subset="name_full").set_index("name_full")
ties = pd.read_csv(f"{OUTPUT_DIR}/papal_family_ties.csv", keep_default_na=False)

unknown = (set(ties["earlier_pope"]) | set(ties["later_pope"])) - set(popes.index)
assert not unknown, f"Unknown popes: {unknown}"


def start_year(name: str) -> int:
    return int(popes.loc[name, "start"][:4])


def end_year(name: str) -> int:
    end = popes.loc[name, "end"]
    return int(end[:4]) if end != "NA" else None


ties["years_apart"] = [start_year(b) - start_year(a) for a, b in zip(ties["earlier_pope"], ties["later_pope"])]
reliable = ties[ties["certainty"].isin(RELIABLE)]

# --- Overview ---
print("## Overview\n")
print(ties["certainty"].value_counts().to_string())
reliable_popes = sorted(set(reliable["earlier_pope"]) | set(reliable["later_pope"]), key=lambda n: popes.loc[n, "number"])
print(f"\nPopes with a documented or probable papal relative: {len(reliable_popes)}")
print(", ".join(reliable_popes))

# --- Popes related to their immediate predecessor ---
print("\n## Popes related to their immediate predecessor\n")
for t in reliable.itertuples():
    if popes.loc[t.later_pope, "number"] - popes.loc[t.earlier_pope, "number"] == 1:
        print(f"- {t.earlier_pope} → {t.later_pope} ({t.relationship})")

# --- Cardinal-nephews who became pope ---
print("\n## Popes made cardinal by a papal relative\n")
print("| Pope | Made cardinal by | Relationship | Cardinal | Age at cardinalate | Elected pope | Years after relative's death |")
print("| --- | --- | --- | --- | --- | --- | --- |")
nephews = ties[ties["made_cardinal_by_relative"].isin(["yes", "disputed"])].copy()
nephews["order"] = nephews["later_pope"].map(lambda n: popes.loc[n, "number"])
for t in nephews.sort_values("order").itertuples():
    p = popes.loc[t.later_pope]
    cardinal = p["cardinalate_date"][:4] if p["cardinalate_date"][:1].isdigit() else "?"
    age = p["age_at_cardinalate"].split("y")[0] if p["age_at_cardinalate"][:1].isdigit() else "?"
    gap = start_year(t.later_pope) - end_year(t.earlier_pope)
    flag = " (disputed)" if t.certainty == "disputed" or t.made_cardinal_by_relative == "disputed" else ""
    print(
        f"| {t.later_pope} | {t.earlier_pope} | {t.relationship}{flag} | {cardinal} | {age} "
        f"| {start_year(t.later_pope)} | {gap} |"
    )
print(f"\nTotal: {len(nephews)} ({(nephews['certainty'].isin(RELIABLE) & (nephews['made_cardinal_by_relative'] == 'yes')).sum()} documented or probable)")

# --- Longest-range ties ---
print("\n## Longest-range ties (documented or probable)\n")
print("| Earlier pope | Later pope | Relationship | Years between elections |")
print("| --- | --- | --- | --- |")
for t in reliable.sort_values("years_apart", ascending=False).head(10).itertuples():
    print(f"| {t.earlier_pope} ({start_year(t.earlier_pope)}) | {t.later_pope} ({start_year(t.later_pope)}) | {t.relationship} | {t.years_apart} |")

# --- Mermaid family graph ---
print("\n## Mermaid graph\n")
print("```mermaid\ngraph LR")
for t in reliable.itertuples():
    a, b = t.earlier_pope.replace(" ", "_"), t.later_pope.replace(" ", "_")
    print(f'    {a}["{t.earlier_pope}"] -->|"{t.relationship}"| {b}["{t.later_pope}"]')
print("```")
