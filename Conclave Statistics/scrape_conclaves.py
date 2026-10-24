"""Scrape papal elections (1061 onward) from Wikipedia's "List of papal conclaves"
and each election's infobox into conclaves.csv."""

import csv
import json
import re
import time
import urllib.parse
import urllib.request
from datetime import date

OUTPUT_DIR = "Conclave Statistics"
API_URL = "https://en.wikipedia.org/w/api.php"
USER_AGENT = "popes-stats/1.0 (https://github.com/kosperun/popes-stats)"
LIST_PAGE = "List of papal conclaves"
INFOBOX_FIELDS = ["dates", "location", "electors", "ballots", "vetoed", "dean", "camerlengo", "pope_elected", "nametaken"]
MONTHS = {m: i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"], 1)}


def fetch_pages(titles):
    """Return {requested title: wikitext} for up to 20 titles per request."""
    pages = {}
    for i in range(0, len(titles), 20):
        batch = titles[i:i + 20]
        query = urllib.parse.urlencode({
            "action": "query", "prop": "revisions", "rvprop": "content", "rvslots": "main",
            "format": "json", "redirects": 1, "titles": "|".join(batch),
        })
        request = urllib.request.Request(f"{API_URL}?{query}", headers={"User-Agent": USER_AGENT})
        data = json.load(urllib.request.urlopen(request))["query"]
        renamed = {}
        for step in data.get("normalized", []) + data.get("redirects", []):
            renamed[step["to"]] = renamed.get(step["from"], step["from"])
        for page in data["pages"].values():
            if "revisions" in page:
                pages[renamed.get(page["title"], page["title"])] = page["revisions"][0]["slots"]["main"]["*"]
        time.sleep(1)
    return pages


def split_top_level(text, sep="|"):
    """Split on `sep` outside of {{ }} and [[ ]]."""
    parts, depth, current, i = [], 0, "", 0
    while i < len(text):
        pair = text[i:i + 2]
        if pair in ("{{", "[["):
            depth += 1
            current += pair
            i += 2
        elif pair in ("}}", "]]"):
            depth -= 1
            current += pair
            i += 2
        elif text[i] == sep and depth == 0:
            parts.append(current)
            current = ""
            i += 1
        else:
            current += text[i]
            i += 1
    parts.append(current)
    return parts


def expand_templates(text):
    """Replace {{sort|key|shown}} and similar with their visible text, drop the rest."""
    while True:
        match = re.search(r"\{\{((?:(?!\{\{|\}\}).)*)\}\}", text, flags=re.S)
        if not match:
            return text
        params = split_top_level(match.group(1))
        name = params[0].strip().lower()
        if name in ("sort", "sortname") and len(params) >= 3:
            shown = params[-1]
        elif name in ("nowrap", "small", "nobr") and len(params) >= 2:
            shown = params[1]
        else:
            shown = ""
        text = text[:match.start()] + shown + text[match.end():]


def clean(text):
    text = re.sub(r"<ref[^>]*/>|<ref[^>]*>.*?</ref>", "", text, flags=re.S)
    text = expand_templates(text)
    text = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", text)
    text = re.sub(r"<br\s*/?>", ", ", text)
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", text.replace("&nbsp;", " ").replace("''", "")).strip(" ,")


def first_int(text):
    match = re.search(r"\d+", text.replace(",", ""))
    return int(match.group()) if match else ""


def parse_list(wikitext):
    """Parse the main wikitable (one cell per line), expanding rowspans."""
    table = wikitext[wikitext.index("{|"):wikitext.index("\n|}", wikitext.index("{|"))]
    rows, pending = [], {}
    for raw_row in table.split("\n|-")[1:]:
        cells = [line[1:] for line in re.split(r"\n(?=[|!])", "\n" + raw_row.strip())[1:]]
        row, column = [], 0
        for cell in cells + [None]:
            while column in pending:
                value, remaining = pending[column]
                row.append(value)
                if remaining == 1:
                    del pending[column]
                else:
                    pending[column] = (value, remaining - 1)
                column += 1
            if cell is None:
                break
            attributes = re.match(r'\s*((?:(?:scope|rowspan|colspan)="?\w+"?\s*)+)\|(?!\|)', cell)
            value = cell[attributes.end():] if attributes else cell
            span = re.search(r'rowspan="?(\d+)', attributes.group(1)) if attributes else None
            if span and int(span.group(1)) > 1:
                pending[column] = (value, int(span.group(1)) - 1)
            row.append(value)
            column += 1
        rows.append(row)
    return rows


def parse_infobox(wikitext):
    match = re.search(r"\{\{\s*Infobox papal conclave(.*?)\n\}\}", wikitext, flags=re.S | re.I)
    if not match:
        return {}
    fields = {}
    for part in split_top_level(match.group(1)):
        if "=" in part:
            key, value = part.split("=", 1)
            key = key.strip().lower()
            if key in INFOBOX_FIELDS:
                fields[key] = clean(re.sub(r"<!--.*?-->", "", value, flags=re.S))
    return fields


def parse_dates(text):
    """Parse '31 July – 4 August 1903', '8–9 February 1621', '18 April 2005 to 19 April 2005' and similar."""
    text = text.replace("–", "-").replace("—", "-").replace(" to ", " - ")
    months = "|".join(MONTHS)
    full = re.findall(rf"(\d{{1,2}})\s+({months})\s+(\d{{3,4}})", text)
    if len(full) >= 2:
        (d1, m1, y1), (d2, m2, y2) = full[0], full[-1]
        return date(int(y1), MONTHS[m1], int(d1)), date(int(y2), MONTHS[m2], int(d2))
    match = re.search(rf"(\d{{1,2}})\s+({months})\s*-\s*(\d{{1,2}})\s+({months})\s+(\d{{3,4}})", text)
    if match:
        d1, m1, d2, m2, y = match.groups()
        return date(int(y), MONTHS[m1], int(d1)), date(int(y), MONTHS[m2], int(d2))
    match = re.search(rf"(\d{{1,2}})\s*-\s*(\d{{1,2}})\s+({months})\s+(\d{{3,4}})", text)
    if match:
        d1, d2, m, y = match.groups()
        return date(int(y), MONTHS[m], int(d1)), date(int(y), MONTHS[m], int(d2))
    if len(full) == 1:
        d, m, y = full[0]
        return date(int(y), MONTHS[m], int(d)), date(int(y), MONTHS[m], int(d))
    return None, None


def main():
    list_text = fetch_pages([LIST_PAGE])[LIST_PAGE]
    records = []
    for cells in parse_list(list_text):
        if len(cells) < 6:
            continue
        election_cell, pope_cell, location_cell, eligible_cell, electors_cell, duration_cell = cells[:6]
        link = re.search(r"\[\[([^|\]]+)", election_cell)
        sort_key = re.search(r"\{\{sort\|([\d.]+)", election_cell)
        duration_text = re.sub(r"\{\{Efn.*", "", duration_cell, flags=re.S | re.I)
        ballots = re.search(r"(\d+)\s+ballots?", duration_cell)
        records.append({
            "election": link.group(1).strip() if link else clean(election_cell),
            "sort_key": sort_key.group(1) if sort_key else "",
            "elected": clean(pope_cell).replace("Pope ", "").replace("Antipope ", ""),
            "antipope": "Antipope" in pope_cell,
            "location": clean(location_cell),
            "eligible_electors": first_int(clean(eligible_cell)),
            "electors": first_int(clean(electors_cell)),
            "duration_days": first_int(clean(duration_text)) if "day" in duration_text else "",
            "ballots": int(ballots.group(1)) if ballots else "",
            "dates_note": clean(" ".join(re.findall(r"\{\{Efn\|(\d{1,2} [A-Z][a-z]+ \d{3,4}[^|}]*)", duration_cell))),
        })

    infoboxes = {title: parse_infobox(text) for title, text in fetch_pages(sorted({r["election"] for r in records})).items()}
    for record in records:
        box = infoboxes.get(record["election"], {})
        record["infobox_dates"] = box.get("dates", "")
        start, end = parse_dates(record["infobox_dates"] or record["dates_note"])
        record["start_date"], record["end_date"] = start or "", end or ""
        if record["ballots"] == "" and box.get("ballots"):
            record["ballots"] = first_int(box["ballots"])
        if record["electors"] == "" and box.get("electors"):
            record["electors"] = first_int(box["electors"])
        for field in ("dean", "camerlengo", "vetoed"):
            record[field] = box.get(field, "")
        record["has_infobox"] = bool(box)

    fieldnames = ["election", "sort_key", "elected", "antipope", "location", "eligible_electors", "electors",
                  "duration_days", "ballots", "start_date", "end_date", "infobox_dates", "dates_note",
                  "dean", "camerlengo", "vetoed", "has_infobox"]
    with open(f"{OUTPUT_DIR}/conclaves.csv", "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    print(f"Wrote {len(records)} elections, {sum(r['has_infobox'] for r in records)} with an infobox")


if __name__ == "__main__":
    main()
