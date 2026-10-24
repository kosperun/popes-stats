"""Download the consistory lists from Salvador Miranda, "The Cardinals of the Holy Roman Church"
(https://cardinals.fiu.edu/, ©1998-2023 Salvador Miranda) into miranda_cardinals.csv.

Only facts are extracted (pope, consistory date, cardinal's name, date of death, in pectore notes);
the biographies on the site are not copied. The site was last updated in 2023, so later consistories are missing.
"""

import csv
import html
import re
import time
import urllib.request
from datetime import date

OUTPUT_DIR = "Cardinal Statistics"
BASE_URL = "https://cardinals.fiu.edu"
USER_AGENT = "popes-stats/1.0 (https://github.com/kosperun/popes-stats)"
CENTURIES = ["v", "vi", "vii", "viii", "ix", "x", "xi", "xii", "xiii", "xiv", "xv", "xvi", "xvii", "xviii", "xix", "xx", "xxi"]
DELAY_SECONDS = 3
MONTHS = {m: i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"], 1)}
MONTH_NAMES = "|".join(MONTHS)

# "Pius VII (1800-1823)", "Gregory VIII (1187)", or open-ended "Francis (2013-)"
POPE_LINE = re.compile(r"^(\[Antipope\]\s*)?(.+?)\s*\((\d{3,4})(?:\s*-\s*(\d{3,4})?)?\)$")
CONSISTORY_LINE = re.compile(r"^(.*?\d{3,4}.*?)\s*\(([IVXL]+)\)$")
# "(4) 1. Name ..." (one entry on the site is written "(14). 3 Name")
ENTRY_LINE = re.compile(r"^\((\d+)\)\.?\s*(\d+)\.?\s+(.*)$")
FOOTNOTE_LINE = re.compile(r"^\((\d+)\)\s+(?!\d+\.)(.*)$")


def fetch(page):
    request = urllib.request.Request(f"{BASE_URL}/{page}", headers={"User-Agent": USER_AGENT})
    return urllib.request.urlopen(request, timeout=60).read().decode("utf-8", errors="replace")


def normalize_pope(name):
    """'LEO XIII' -> 'Leo XIII'; other headers are already in title case."""
    return " ".join(
        word.upper() if re.fullmatch(r"\(?[IVXL]+\)?", word, flags=re.I) else (word.capitalize() if word.isupper() else word)
        for word in name.strip().split()
    )


def to_lines(page_html):
    """Flatten the page to text lines, keeping cardinal names marked as «name»."""
    # Line breaks in the HTML source are not line breaks on the page; only <P> and <BR> are
    page_html = re.sub(r"\s+", " ", page_html)
    text = re.sub(r"<A HREF=\"bios[^\"]*\">\s*<STRONG>(.*?)</STRONG>\s*</A>", r"«\1»", page_html, flags=re.S | re.I)
    # Consistory and pope headings are not always in their own paragraph, so also break before
    # <CENTER> and anchors, and at the end of paragraphs
    text = re.sub(r"<(?:/?P|BR|TR|TD|DIV|CENTER|A NAME)[^>]*>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    return [re.sub(r"\s+", " ", line).strip() for line in text.split("\n") if line.strip()]


def parse_date(text):
    """Return (ISO date, precision) for 'August 11, 1800', 'June 1903', '1099', 'ca. 1105'."""
    text = text.replace("ca.", "").strip()
    match = re.search(rf"({MONTH_NAMES})\s+(\d{{1,2}})(?:\s*(?:-|or)\s*\d{{1,2}})?,\s*(\d{{3,4}})", text)
    if match:
        month, day, year = match.groups()
        return date(int(year), MONTHS[month], int(day)).isoformat(), "day"
    match = re.search(rf"({MONTH_NAMES})\s+(\d{{3,4}})", text)
    if match:
        return date(int(match.group(2)), MONTHS[match.group(1)], 1).isoformat(), "month"
    match = re.search(r"\b(\d{3,4})\b", text)
    if match:
        return date(int(match.group(1)), 1, 1).isoformat(), "year"
    return "", ""


def parse_page(page_html, century):
    rows, pope, antipope, consistory = [], None, False, None
    footnotes, pending = {}, []
    for line in to_lines(page_html):
        entry = ENTRY_LINE.match(line)
        if entry and pope and consistory:
            number, _, rest = entry.groups()
            marked = re.search(r"«([^«»]*)»", rest)
            # Some names on the site have unclosed tags; then the name is the text before the first comma
            name = (marked.group(1) if marked else re.split(r",\s|\s\(|\.?\s*\+", rest.replace("«", "").replace("»", ""))[0]).strip()
            rest = rest.replace("«", "").replace("»", "")
            death = re.search(r"\+\s*([^+]*?)\.?\s*((?:\(\d+\)\s*)*)$", rest)
            if not death:
                # A few entries give the date of death without the "+"
                death = re.search(rf"\.\s*((?:{MONTH_NAMES})\s+\d{{1,2}},\s*\d{{4}})\.?\s*((?:\(\d+\)\s*)*)$", rest)
            markers = re.findall(r"\((\d+)\)", death.group(2)) if death else re.findall(r"\((\d+)\)\s*$", rest)
            death_text = death.group(1).strip() if death else ""
            death_iso, death_precision = parse_date(death_text) if death_text else ("", "")
            row = {
                "century_page": century, "pope": pope, "antipope": antipope, "number": int(number),
                "consistory": consistory[0], "consistory_label": consistory[1],
                "created": consistory[2], "created_precision": consistory[3],
                "name": name, "description": "", "death_text": death_text,
                "death": death_iso, "death_precision": death_precision, "notes": "", "_markers": markers,
                "_consistory_key": consistory,
            }
            rows.append(row)
            pending.append(row)
            continue
        footnote = FOOTNOTE_LINE.match(line)
        if footnote and pending:
            footnotes[(pending[-1]["_consistory_key"], footnote.group(1))] = footnote.group(2)
            continue
        consistory_match = CONSISTORY_LINE.match(line)
        if consistory_match and pope and not line.startswith("("):
            created, precision = parse_date(consistory_match.group(1))
            consistory = (consistory_match.group(1), consistory_match.group(2), created, precision)
            continue
        pope_match = POPE_LINE.match(line)
        if pope_match and len(line) < 60:
            antipope = bool(pope_match.group(1))
            pope = (normalize_pope(pope_match.group(2)), int(pope_match.group(3)))
    for row in rows:
        notes = [footnotes.get((row["_consistory_key"], m), "") for m in row.pop("_markers")]
        row["notes"] = " ".join(n for n in notes if n)
        # Future popes have no "+ date"; a footnote may say "Elected Pope ... Died on January 28, 1621."
        died = re.search(r"Died on ([^.]*\d{3,4})", row["notes"])
        if not row["death"] and died:
            row["death_text"] = died.group(1)
            row["death"], row["death_precision"] = parse_date(died.group(1))
        row.pop("_consistory_key")
        row["pope_name"], row["pope_start_year"] = row.pop("pope")
    return rows


def main():
    rows = []
    for century in CENTURIES:
        page = fetch(f"consistories-{century}.htm")
        page_rows = parse_page(page, century)
        print(f"{century:>5}: {len(page_rows)} cardinals")
        rows.extend(page_rows)
        time.sleep(DELAY_SECONDS)
    fieldnames = ["century_page", "pope_name", "pope_start_year", "antipope", "number", "consistory", "consistory_label",
                  "created", "created_precision", "name", "death_text", "death", "death_precision", "notes"]
    with open(f"{OUTPUT_DIR}/miranda_cardinals.csv", "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} cardinals")


if __name__ == "__main__":
    main()
