import calendar
from datetime import date

import matplotlib.pyplot as plt
import pandas as pd

OUTPUT_DIR = "General Statistics/Calendar Patterns"
# Rome switched to the Gregorian calendar in October 1582. Earlier dates are Julian,
# so weekdays are only computed from 1583 onward.
GREGORIAN_START = "1583-01-01"
# Popes whose pontificate ended by resignation or deposition, not death
NOT_DEATH = {"Pontian", "Silverius", "Benedict IX", "Gregory VI", "Celestine V", "Gregory XII", "Benedict XVI"}
BIRTHDAY_WINDOW_DAYS = 7
ANNIVERSARY_WINDOW_DAYS = 2


def parse_date(datestr: str) -> date:
    y, m, d = map(int, datestr[:10].split("-"))
    return date(y, m, d)


def is_known(datestr: str) -> bool:
    # Unknown days are stored as a 30 June placeholder: for every estimated birth date,
    # and for election/end dates of the earliest popes (before AD 300)
    return datestr != "NA" and not datestr.endswith("-06-30")


def is_known_event(datestr: str) -> bool:
    return datestr != "NA" and not (datestr.endswith("-06-30") and datestr < "0300")


def days_from_anniversary(anchor: date, other: date) -> int:
    """Signed distance in days from the anniversary of `anchor` in `other`'s year."""
    day = 28 if (anchor.month, anchor.day) == (2, 29) else anchor.day
    anniversary = date(other.year, anchor.month, day)
    diff = (other - anniversary).days
    if diff > 182:
        diff -= 365
    elif diff < -182:
        diff += 365
    return diff


df = pd.read_csv("popes.csv", keep_default_na=False)

starts = df[df["start"].apply(is_known_event)]
deaths = df[df["end"].apply(is_known_event) & ~df["name_full"].isin(NOT_DEATH)]
births = df[df["birth"].apply(is_known)]

start_months = starts["start"].str[5:7].astype(int).value_counts().reindex(range(1, 13), fill_value=0)
death_months = deaths["end"].str[5:7].astype(int).value_counts().reindex(range(1, 13), fill_value=0)
birth_months = births["birth"].str[5:7].astype(int).value_counts().reindex(range(1, 13), fill_value=0)

print(f"Known election dates: {len(starts)}, known death dates: {len(deaths)}, known birth dates: {len(births)}")
print("\n| Month | Elections | Deaths | Births |")
print("| --- | --- | --- | --- |")
for m in range(1, 13):
    print(f"| {calendar.month_name[m]} | {start_months[m]} | {death_months[m]} | {birth_months[m]} |")

# --- Weekdays (Gregorian era only) ---
modern_starts = starts[starts["start"] >= GREGORIAN_START]
start_weekdays = (
    modern_starts["start"].apply(lambda s: parse_date(s).weekday()).value_counts().reindex(range(7), fill_value=0)
)
modern_deaths = deaths[deaths["end"] >= GREGORIAN_START]
death_weekdays = (
    modern_deaths["end"].apply(lambda s: parse_date(s).weekday()).value_counts().reindex(range(7), fill_value=0)
)
print(f"\nWeekdays since 1583 ({len(modern_starts)} elections, {len(modern_deaths)} deaths)")
print("\n| Weekday | Elections | Deaths |")
print("| --- | --- | --- |")
for d in range(7):
    print(f"| {calendar.day_name[d]} | {start_weekdays[d]} | {death_weekdays[d]} |")
print("\nSunday elections:", ", ".join(
    f"{r.name_full} ({r.start})" for r in modern_starts.itertuples() if parse_date(r.start).weekday() == 6
))

# --- Coincidences ---
print(f"\n## Coincidences (birthday within {BIRTHDAY_WINDOW_DAYS} days, election anniversary within {ANNIVERSARY_WINDOW_DAYS} days)\n")
for r in df.itertuples():
    events = []
    birth = parse_date(r.birth) if is_known(r.birth) else None
    start = parse_date(r.start) if is_known_event(r.start) else None
    end = parse_date(r.end) if is_known_event(r.end) else None
    ended_by = "resigned" if r.name_full in NOT_DEATH else "died"

    if birth and start:
        diff = days_from_anniversary(birth, start)
        if abs(diff) <= BIRTHDAY_WINDOW_DAYS:
            events.append(f"elected {abs(diff)} days {'after' if diff > 0 else 'before'} his birthday" if diff else "elected on his birthday")
    if birth and end:
        diff = days_from_anniversary(birth, end)
        if abs(diff) <= BIRTHDAY_WINDOW_DAYS:
            events.append(f"{ended_by} {abs(diff)} days {'after' if diff > 0 else 'before'} his birthday" if diff else f"{ended_by} on his birthday")
    if start and end and end.year > start.year:
        diff = days_from_anniversary(start, end)
        if abs(diff) <= ANNIVERSARY_WINDOW_DAYS:
            events.append(
                f"{ended_by} {abs(diff)} days {'after' if diff > 0 else 'before'} the anniversary of his election"
                if diff
                else f"{ended_by} on the anniversary of his election"
            )
    for event in events:
        print(f"- {r.name_full} ({r.birth} / {r.start} / {r.end}): {event}")

# --- Plots ---
months = [calendar.month_abbr[m] for m in range(1, 13)]
fig, ax = plt.subplots(figsize=(12, 6))
width = 0.4
x = range(12)
ax.bar([i - width / 2 for i in x], start_months.values, width, label="Elections", color="steelblue")
ax.bar([i + width / 2 for i in x], death_months.values, width, label="Deaths in office", color="indianred")
ax.set_xticks(list(x))
ax.set_xticklabels(months)
ax.set_ylabel("Number of popes")
ax.set_title("Papal Elections and Deaths by Month (all popes with known dates)")
ax.legend()
ax.grid(True, axis="y", linestyle="--", alpha=0.7)
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/elections_and_deaths_by_month.png")

weekdays = [calendar.day_abbr[d] for d in range(7)]
fig, ax = plt.subplots(figsize=(10, 6))
x = range(7)
ax.bar([i - width / 2 for i in x], start_weekdays.values, width, label="Elections", color="steelblue")
ax.bar([i + width / 2 for i in x], death_weekdays.values, width, label="Deaths in office", color="indianred")
ax.set_xticks(list(x))
ax.set_xticklabels(weekdays)
ax.set_ylabel("Number of popes")
ax.set_title("Papal Elections and Deaths by Weekday (since 1583)")
ax.legend()
ax.grid(True, axis="y", linestyle="--", alpha=0.7)
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/elections_and_deaths_by_weekday.png")
