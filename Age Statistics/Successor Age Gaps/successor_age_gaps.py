from datetime import date

import matplotlib.pyplot as plt
import pandas as pd

# Birth dates are documented (not estimated) from roughly the mid-15th century on,
# so the analysis starts with the transition into Nicholas V (elected 1447).
FIRST_SUCCESSOR_START = "1447-01-01"
OUTPUT_DIR = "Age Statistics/Successor Age Gaps"


def parse_date(datestr: str) -> date:
    y, m, d = map(int, datestr[:10].split("-"))
    return date(y, m, d)


def years_between(earlier: date, later: date) -> float:
    return (later - earlier).days / 365.25


def pontificate(row) -> str:
    end = row["end"][:4] if row["end"] != "NA" else "current"
    return f"{row['start'][:4]}-{end}"


# --- Load data ---
df = pd.read_csv("popes.csv", keep_default_na=False)
df = df.sort_values("number").reset_index(drop=True)

# --- Build predecessor/successor pairs ---
pairs = []
for prev, curr in zip(df.iloc[:-1].to_dict("records"), df.iloc[1:].to_dict("records")):
    if curr["start"] < FIRST_SUCCESSOR_START or prev["name_full"] == curr["name_full"]:
        continue
    prev_birth, curr_birth = parse_date(prev["birth"]), parse_date(curr["birth"])
    pairs.append(
        {
            "predecessor": prev["name_full"],
            "successor": curr["name_full"],
            "predecessor_pontificate": pontificate(prev),
            "successor_pontificate": pontificate(curr),
            "predecessor_birth": prev["birth"],
            "successor_birth": curr["birth"],
            # Positive: successor is younger than predecessor
            "birth_gap": years_between(prev_birth, curr_birth),
            "predecessor_age_at_election": float(prev["start_age"]),
            "successor_age_at_election": float(curr["start_age"]),
            "start_year": int(curr["start"][:4]),
        }
    )

gaps = pd.DataFrame(pairs)
gaps["century"] = gaps["start_year"] // 100 + 1
gaps["election_age_diff"] = (
    gaps["successor_age_at_election"] - gaps["predecessor_age_at_election"]
)


def format_birth(datestr: str) -> str:
    # Unknown birth days are stored as a 30 June placeholder
    return datestr[:4] if datestr.endswith("-06-30") else datestr


def print_table(title, frame):
    print(f"\n## {title}\n")
    print("| # | Predecessor | Born | Successor | Born | Birth gap | Ages at election |")
    print("| --- | --- | --- | --- | --- | --- | --- |")
    for i, row in enumerate(frame.itertuples(), 1):
        direction = "later" if row.birth_gap > 0 else "earlier"
        print(
            f"| {i} | {row.predecessor} ({row.predecessor_pontificate}) "
            f"| {format_birth(row.predecessor_birth)} "
            f"| {row.successor} ({row.successor_pontificate}) "
            f"| {format_birth(row.successor_birth)} "
            f"| {abs(row.birth_gap):.1f} years {direction} "
            f"| {row.predecessor_age_at_election:.0f} → {row.successor_age_at_election:.0f} |"
        )


print_table("Successors much younger than their predecessors", gaps.nlargest(10, "birth_gap"))
print_table("Successors older than their predecessors", gaps[gaps["birth_gap"] < 0].nsmallest(10, "birth_gap"))
print_table("Closest in age", gaps.reindex(gaps["birth_gap"].abs().sort_values().index).head(10))

younger = (gaps["birth_gap"] > 0).sum()
older = (gaps["birth_gap"] < 0).sum()
print(f"\nTransitions analysed: {len(gaps)}")
print(f"Successor younger than predecessor: {younger}")
print(f"Successor older than predecessor: {older}")
print(f"Mean birth gap: {gaps['birth_gap'].mean():.1f} years")
print(f"Mean absolute birth gap: {gaps['birth_gap'].abs().mean():.1f} years")

century_stats = (
    gaps.groupby("century")
    .agg(
        mean_abs_gap=("birth_gap", lambda s: s.abs().mean()),
        mean_gap=("birth_gap", "mean"),
        older_successors=("birth_gap", lambda s: (s < 0).sum()),
        transitions=("birth_gap", "count"),
    )
    .reset_index()
)
print("\n## By century\n")
print("| Century | Transitions | Avg. absolute gap | Avg. gap | Successor older |")
print("| --- | --- | --- | --- | --- |")
for row in century_stats.itertuples():
    print(
        f"| {row.century}th | {row.transitions} | {row.mean_abs_gap:.1f} years "
        f"| {row.mean_gap:+.1f} years | {row.older_successors} |"
    )

# --- Plot: every transition over time ---
fig, ax = plt.subplots(figsize=(16, 7))
colors = ["steelblue" if g > 0 else "indianred" for g in gaps["birth_gap"]]
ax.bar(range(len(gaps)), gaps["birth_gap"], color=colors)
ax.axhline(0, color="black", linewidth=0.8)
ax.set_xticks(range(len(gaps)))
ax.set_xticklabels(gaps["successor"], rotation=90, fontsize=7)
ax.set_ylabel("Years (positive = successor born later)")
ax.set_title(
    "Birth Gap Between Each Pope and His Predecessor (since 1447)\n"
    "blue: successor younger, red: successor older"
)
ax.grid(True, axis="y", linestyle="--", alpha=0.7)
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/successor_birth_gaps.png")

# --- Plot: average absolute gap by century ---
fig, ax = plt.subplots(figsize=(12, 6))
bars = ax.bar(century_stats["century"], century_stats["mean_abs_gap"], color="steelblue", width=0.6)
for rect, value, older_count, total in zip(
    bars,
    century_stats["mean_abs_gap"],
    century_stats["older_successors"],
    century_stats["transitions"],
):
    ax.text(
        rect.get_x() + rect.get_width() / 2,
        rect.get_height() + 0.2,
        f"{value:.1f} y\n({older_count}/{total} older)",
        ha="center",
        va="bottom",
        fontsize=9,
    )
ax.set_xlabel("Century")
ax.set_ylabel("Average absolute birth gap (years)")
ax.set_title("Average Age Difference Between Successive Popes by Century (since 1447)")
ax.set_xticks(century_stats["century"])
ax.grid(True, axis="y", linestyle="--", alpha=0.7)
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/average_successor_age_gap_by_century.png")
