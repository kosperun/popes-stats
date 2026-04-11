import csv
from datetime import date

from dateutil.relativedelta import relativedelta  # pip install python-dateutil


def parse_date(datestr):
    """Parse YYYY-MM-DD or YYYY-MM-DDT00:00:00Z into datetime.date."""
    if not datestr or datestr in ("NA", "Unknown", ""):
        return None
    datestr = datestr.split("T")[0]
    try:
        y, m, d = map(int, datestr.split("-"))
        return date(y, m, d)
    except Exception:
        return None


def diff_ymd(d1, d2):
    """Return difference between two dates as 'Xy Ym Zd'."""
    if not d1 or not d2:
        return ""
    delta = relativedelta(d2, d1)
    return f"{delta.years}y {delta.months}m {delta.days}d"


def load_popes(path):
    """Load popes and filter out invalid 'years_as_cardinal' values."""
    valid_rows = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            start = parse_date(row.get("start"))
            cardinalate = parse_date(row.get("cardinalate_date"))
            end = parse_date(row.get("end"))
            if not start or not cardinalate or not end:
                continue
            row["years_as_cardinal_ymd"] = diff_ymd(cardinalate, start)
            row["start_year"] = start.year
            row["end_year"] = end.year
            valid_rows.append(row)
    return valid_rows


def sort_by_years_as_cardinal(rows):
    """Return ascending and descending lists by years_as_cardinal (by total days)."""

    # sort by total days for proper ordering
    def total_days(r):
        start = parse_date(r.get("start"))
        cardinalate = parse_date(r.get("cardinalate_date"))
        if not start or not cardinalate:
            return float("inf")
        return (start - cardinalate).days  # negative if cardinalate after start

    asc = sorted(rows, key=total_days)
    desc = list(reversed(asc))
    return asc, desc


def print_top_bottom(asc, desc, n=267):
    """Print top and bottom N popes by years_as_cardinal (Y M D)."""
    print("\n🕊️ Shortest-serving cardinals before becoming pope:")
    for r in asc[:n]:
        print(
            f"{r['name_full']} ({r['start_year']}-{r['end_year']}): {r['years_as_cardinal_ymd']}"
        )

    print("\n👑 Longest-serving cardinals before becoming pope:")
    for r in desc[:n]:
        print(
            f"{r['name_full']} ({r['start_year']}-{r['end_year']}): {r['years_as_cardinal_ymd']}"
        )


def main():
    popes = load_popes("popes.csv")
    asc, desc = sort_by_years_as_cardinal(popes)
    print_top_bottom(asc, desc)


if __name__ == "__main__":
    main()
