from datetime import date, timedelta

import matplotlib.pyplot as plt
import pandas as pd

OUTPUT_DIR = "General Statistics/Overlapping Lifespans"
# Birth years are documented from the end of the Western Schism (Martin V, elected 1417) on.
# Exact birth days are unknown for Martin V, Eugene IV and Innocent VIII (30 June placeholder).
FIRST_START = "1417-01-01"
TODAY = date.today()
# Popes who lived on after their pontificate ended
DEATHS_AFTER_PONTIFICATE = {"Benedict XVI": "2022-12-31"}


def parse_date(datestr: str) -> date:
    y, m, d = map(int, datestr[:10].split("-"))
    return date(y, m, d)


df = pd.read_csv("popes.csv", keep_default_na=False)
df = df[df["start"] >= FIRST_START].sort_values("number").reset_index(drop=True)
df["birth_dt"] = df["birth"].apply(parse_date)
df["start_dt"] = df["start"].apply(parse_date)
df["death_dt"] = [
    parse_date(DEATHS_AFTER_PONTIFICATE.get(r.name_full, r.end)) if r.end != "NA" else None
    for r in df.itertuples()
]
popes = df.to_dict("records")


def alive(pope, day: date) -> bool:
    return pope["birth_dt"] <= day and (pope["death_dt"] is None or day <= pope["death_dt"])


# --- At each election: future popes already alive, former popes still alive ---
print("## Future popes already alive at each election\n")
election_rows = []
for i, pope in enumerate(popes):
    day = pope["start_dt"]
    future = [p for p in popes[i + 1 :] if alive(p, day)]
    former = [p for p in popes[:i] if alive(p, day)]
    furthest = future[-1] if future else None
    election_rows.append(
        {
            "name": pope["name_full"],
            "year": day.year,
            "future_alive": len(future),
            "furthest": f"{furthest['name_full']} (+{popes.index(furthest) - i})" if furthest else "-",
            "former_alive": ", ".join(p["name_full"] for p in former),
        }
    )
elections = pd.DataFrame(election_rows)
print("| Pope | Elected | Future popes alive | Furthest future pope alive | Former popes alive |")
print("| --- | --- | --- | --- | --- |")
for r in elections.itertuples():
    print(f"| {r.name} | {r.year} | {r.future_alive} | {r.furthest} | {r.former_alive or '-'} |")

# --- Pontificates each pope lived through ---
print("\n## Pontificates lived through (including his own)\n")
lived = []
for pope in popes:
    end = pope["death_dt"] or TODAY
    reigns = [
        p["name_full"]
        for p in popes
        if p["start_dt"] <= end and (p["death_dt"] or TODAY) >= pope["birth_dt"]
    ]
    lived.append((pope["name_full"], len(reigns), reigns[0]))
lived.sort(key=lambda x: -x[1])
print("| Pope | Pontificates lived through | Born under |")
print("| --- | --- | --- |")
for name, count, first in lived[:15]:
    print(f"| {name} | {count} | {first} |")

# --- Popes (past, present or future) alive on each day ---
days = []
day = date(1450, 1, 1)
while day <= TODAY:
    days.append((day, sum(alive(p, day) for p in popes)))
    day += timedelta(days=30)
timeline = pd.DataFrame(days, columns=["day", "alive"])
peak = timeline["alive"].max()
peak_days = timeline[timeline["alive"] == peak]["day"]
print(f"\nMost popes alive at once: {peak} (first on ~{peak_days.iloc[0]}, last on ~{peak_days.iloc[-1]})")
peak_day = peak_days.iloc[0]
print("  " + ", ".join(p["name_full"] for p in popes if alive(p, peak_day)))
early = timeline[timeline["day"] <= date(1950, 1, 1)]
fewest = early["alive"].min()
fewest_days = early[early["alive"] == fewest]["day"]
print(f"Fewest popes alive at once (1450-1950): {fewest} (~{fewest_days.iloc[0]} to ~{fewest_days.iloc[-1]})")

# --- Plot ---
fig, ax = plt.subplots(figsize=(16, 6))
ax.step(timeline["day"], timeline["alive"], where="post", color="steelblue")
ax.fill_between(timeline["day"], timeline["alive"], step="post", color="steelblue", alpha=0.3)
ax.axvspan(date(1950, 1, 1), TODAY, color="grey", alpha=0.15)
ax.text(date(1952, 1, 1), peak, "incomplete:\nfuture popes\nnot yet known", fontsize=9, va="top")
ax.set_ylabel("Popes alive (past, reigning and future)")
ax.set_title("How Many Popes Were Alive at the Same Time (popes elected since 1417)")
ax.grid(True, axis="y", linestyle="--", alpha=0.7)
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/popes_alive_at_the_same_time.png")

fig, ax = plt.subplots(figsize=(16, 7))
ax.bar(range(len(elections)), elections["future_alive"], color="steelblue")
ax.set_xticks(range(len(elections)))
ax.set_xticklabels(elections["name"], rotation=90, fontsize=7)
ax.set_ylabel("Future popes already born")
ax.set_title("Future Popes Already Alive at Each Papal Election (since 1417)")
ax.grid(True, axis="y", linestyle="--", alpha=0.7)
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/future_popes_alive_at_each_election.png")
