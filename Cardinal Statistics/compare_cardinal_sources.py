"""Match Miranda's consistory lists against the Wikidata cardinals, report disagreements,
and write cardinals_combined.csv.

In the combined data, Miranda's site is the source for the creation date, the creating pope and
the death date; Wikidata supplies birth dates, nationality and the end of the cardinalate.
Cardinals found in only one source are kept, so consistories after Miranda's last update (2023)
come from Wikidata alone.
"""

import csv
import json
import re
import time
import urllib.parse
import urllib.request
import unicodedata
from collections import Counter, defaultdict
from datetime import date
from difflib import SequenceMatcher

OUTPUT_DIR = "Cardinal Statistics"
# Miranda's spelling of papal names where it differs from popes.csv
POPE_ALIASES = {
    "Callistus": "Callixtus", "Eugenius": "Eugene", "Zacharias": "Zachary", "Agapitus": "Agapetus",
    "Constantinus": "Constantine", "Deusdedit": "Adeodatus",
}
# Words that are not part of a person's name in either source
NOISE = {"seniore", "iuniore", "juniore", "the", "elder", "younger", "cardinal", "osb", "op", "ofm", "sj"}
MIN_SIMILARITY_WITH_YEARS = 0.6
MIN_SIMILARITY_NAME_ONLY = 0.85
MIN_SIMILARITY_SAME_CONSISTORY = 0.45
DATE_TOLERANCE_DAYS = 31
# Cardinals created since then may still matter for the age limit in conclaves (from 1971)
LOOKUP_BIRTHS_FROM = "1900-01-01"
USER_AGENT = "popes-stats/1.0 (https://github.com/kosperun/popes-stats)"


def parse_date(text):
    match = re.match(r"(\d{4})-(\d{2})-(\d{2})", text or "")
    return date(*map(int, match.groups())) if match else None


def normalize(name):
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    words = re.findall(r"[a-z]+", name.replace("-", " "))
    return " ".join(w for w in words if w not in NOISE)


def similarity(a, b):
    ratio = SequenceMatcher(None, a, b).ratio()
    tokens_a, tokens_b = set(a.split()), set(b.split())
    # A single shared word ("Pietro") says little: compare one-word names as whole strings only
    if min(len(tokens_a), len(tokens_b)) < 2:
        return ratio
    overlap = len(tokens_a & tokens_b) / min(len(tokens_a), len(tokens_b))
    return max(ratio, overlap)


# --- Popes: Miranda header (name, first year) -> popes.csv name ---
with open("popes.csv") as file:
    popes = list(csv.DictReader(file))
popes_by_year = defaultdict(list)
for pope in popes:
    popes_by_year[int(pope["start"][:4])].append(pope["name_full"])


def map_pope(name, start_year, antipope):
    if antipope:
        return f"Antipope {name}"
    name = re.sub(r"\s*\([IVXL]+\)", "", name).replace(" The Great", "")
    for miranda, ours in POPE_ALIASES.items():
        name = name.replace(miranda, ours)
    candidates = popes_by_year.get(start_year, []) + popes_by_year.get(start_year - 1, []) + popes_by_year.get(start_year + 1, [])
    if name in candidates:
        return name
    same_first_word = [c for c in candidates if c.split()[0] == name.split()[0]]
    return same_first_word[0] if same_first_word else name


# --- Load both sources ---
with open(f"{OUTPUT_DIR}/miranda_cardinals.csv") as file:
    miranda = list(csv.DictReader(file))
for row in miranda:
    row["created_by"] = map_pope(row["pope_name"], int(row["pope_start_year"]), row["antipope"] == "True")
    row["norm"] = normalize(row["name"])
    row["created_dt"], row["death_dt"] = parse_date(row["created"]), parse_date(row["death"])

with open(f"{OUTPUT_DIR}/cardinals.csv") as file:
    wikidata = list(csv.DictReader(file))
# Wikidata names popes by their papal name; Miranda lists them under their birth name
birth_names = {p["name_full"]: p["Personal Name"] for p in popes if p["Personal Name"] not in ("", "NA")}
for row in wikidata:
    row["norm"] = normalize(row["name"])
    papal_name = row["name"].removeprefix("Pope ")
    row["names"] = [row["norm"]] + ([normalize(birth_names[papal_name])] if papal_name in birth_names else [])
    row["created_dt"], row["death_dt"] = parse_date(row["created"]), parse_date(row["death"])

unmapped = sorted({r["created_by"] for r in miranda} - {p["name_full"] for p in popes} - {r["created_by"] for r in miranda if r["created_by"].startswith("Antipope")})
print(f"Miranda: {len(miranda)} creations; Wikidata: {len(wikidata)} cardinals")
print(f"Miranda popes not matched to popes.csv: {unmapped or 'none'}")

# --- Candidate pairs: same death year (±1) or same creation year (±2), then by name ---
by_death, by_created = defaultdict(list), defaultdict(list)
for i, w in enumerate(wikidata):
    if w["death_dt"]:
        by_death[w["death_dt"].year].append(i)
    if w["created_dt"]:
        by_created[w["created_dt"].year].append(i)

# Future popes often have no death date on Miranda's site; compare them with every pope in Wikidata
pope_records = [i for i, w in enumerate(wikidata) if len(w["names"]) > 1]

pairs = []
for m_index, m in enumerate(miranda):
    candidates = set(i for i in pope_records if not m["death_dt"] and m["created_dt"] and wikidata[i]["created_dt"]
                     and abs(m["created_dt"].year - wikidata[i]["created_dt"].year) <= 2)
    if m["death_dt"]:
        for year in range(m["death_dt"].year - 1, m["death_dt"].year + 2):
            candidates.update(by_death[year])
    if m["created_dt"]:
        for year in range(m["created_dt"].year - 2, m["created_dt"].year + 3):
            candidates.update(by_created[year])
    for w_index in candidates:
        w = wikidata[w_index]
        death_ok = bool(m["death_dt"] and w["death_dt"] and abs(m["death_dt"].year - w["death_dt"].year) <= 1)
        created_ok = bool(m["created_dt"] and w["created_dt"] and abs(m["created_dt"].year - w["created_dt"].year) <= 2)
        # Different people often share a name: a creator contradicting Wikipedia's categories, together with
        # creation years far apart, rules a pair out (the categories alone have occasional errors)
        creators = set(filter(None, w["created_by_wikipedia"].split(";")))
        if creators and m["created_by"] not in creators and not m["created_by"].startswith("Antipope"):
            if not death_ok or (m["created_dt"] and w["created_dt"] and abs(m["created_dt"].year - w["created_dt"].year) > 5):
                continue
        score = max(similarity(m["norm"], name) for name in w["names"])
        # Future popes have no death date on Miranda's site ("elected pope"), so the years cannot all be compared
        deaths_comparable = bool(m["death_dt"] and w["death_dt"])
        both_years_agree = created_ok and (death_ok or not deaths_comparable)
        threshold = MIN_SIMILARITY_WITH_YEARS if both_years_agree else MIN_SIMILARITY_NAME_ONLY
        # Created in the same consistory: allow different spellings (Lewicki / Levytsky, Willem / Wim)
        if m["created_dt"] and m["created_dt"] == w["created_dt"] and m["created_precision"] == w["created_precision"] == "day":
            threshold = MIN_SIMILARITY_SAME_CONSISTORY
        if score >= threshold:
            pairs.append((score + 0.2 * death_ok + 0.1 * created_ok, m_index, w_index))

# One-to-one matching, best pairs first
matched_m, matched_w, matches = set(), set(), {}
for score, m_index, w_index in sorted(pairs, reverse=True):
    if m_index not in matched_m and w_index not in matched_w:
        matched_m.add(m_index)
        matched_w.add(w_index)
        matches[m_index] = w_index
print(f"Matched: {len(matches)}; only in Miranda: {len(miranda) - len(matches)}; only in Wikidata: {len(wikidata) - len(matched_w)}")


def century(d):
    return d.year // 100 + 1 if d else None


print("\n## Coverage by century of creation\n")
print("| Century | Miranda | Matched in Wikidata | Only in Miranda |")
print("| --- | --- | --- | --- |")
counts = Counter(century(m["created_dt"]) for m in miranda)
found = Counter(century(miranda[i]["created_dt"]) for i in matches)
for c in sorted(k for k in counts if k):
    print(f"| {c} | {counts[c]} | {found[c]} ({found[c] / counts[c]:.0%}) | {counts[c] - found[c]} |")

# --- Disagreements ---
diffs = []
for m_index, w_index in matches.items():
    m, w = miranda[m_index], wikidata[w_index]
    created_gap = (abs((m["created_dt"] - w["created_dt"]).days)
                   if m["created_dt"] and w["created_dt"] and m["created_precision"] == "day" and w["created_precision"] == "day" else None)
    death_gap = (abs((m["death_dt"] - w["death_dt"]).days)
                 if m["death_dt"] and w["death_dt"] and m["death_precision"] == "day" else None)
    creator_disagrees = bool(w["created_by_wikipedia"] and not m["created_by"].startswith("Antipope")
                             and m["created_by"] not in w["created_by_wikipedia"].split(";"))
    diffs.append({
        "miranda_name": m["name"], "wikidata_name": w["name"], "qid": w["qid"],
        "miranda_pope": m["created_by"], "wikipedia_pope": w["created_by_wikipedia"],
        "miranda_created": m["created"], "wikidata_created": w["created"],
        "miranda_death": m["death"], "wikidata_death": w["death"],
        "created_differs": created_gap is not None and created_gap > DATE_TOLERANCE_DAYS,
        "in_pectore": "pectore" in m["notes"],
        "death_differs": death_gap is not None and death_gap > DATE_TOLERANCE_DAYS,
        "creator_differs": creator_disagrees,
    })
with open(f"{OUTPUT_DIR}/cardinal_source_comparison.csv", "w", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=list(diffs[0]))
    writer.writeheader()
    writer.writerows(diffs)

both_created = sum(1 for d in diffs if d["miranda_created"] and d["wikidata_created"])
print(f"\nCreation date differs by more than {DATE_TOLERANCE_DAYS} days: {sum(d['created_differs'] for d in diffs)} "
      f"({sum(d['created_differs'] and d['in_pectore'] for d in diffs)} of them created in pectore, "
      f"where Wikidata usually has the date of publication)")
print(f"Death date differs by more than {DATE_TOLERANCE_DAYS} days: {sum(d['death_differs'] for d in diffs)}")
print(f"Creating pope differs from Wikipedia's category: {sum(d['creator_differs'] for d in diffs)}")
print("\nExamples of differing creation dates (not in pectore):")
for d in [d for d in diffs if d["created_differs"] and not d["in_pectore"]][:12]:
    print(f"- {d['miranda_name']}: Miranda {d['miranda_created']} ({d['miranda_pope']}), Wikidata {d['wikidata_created']}")
print("\nExamples of differing death dates:")
for d in [d for d in diffs if d["death_differs"]][:12]:
    print(f"- {d['miranda_name']}: Miranda {d['miranda_death']}, Wikidata {d['wikidata_death']}")
print("\nExamples of differing creating popes:")
for d in [d for d in diffs if d["creator_differs"]][:12]:
    print(f"- {d['miranda_name']}: Miranda {d['miranda_pope']}, Wikipedia {d['wikipedia_pope']}")

# --- Birth dates for modern cardinals missing from the Wikidata query ---
# A few modern cardinals' Wikidata items do not record the position of cardinal; the age limit for
# voting needs their birth dates, so they are looked up by name.
def wikidata_birth(name):
    def api(**params):
        params.update(format="json")
        request = urllib.request.Request(f"https://www.wikidata.org/w/api.php?{urllib.parse.urlencode(params)}",
                                         headers={"User-Agent": USER_AGENT})
        return json.load(urllib.request.urlopen(request, timeout=60))
    for result in api(action="wbsearchentities", search=name, language="en", limit=5)["search"]:
        if re.search(r"cardinal|bishop|priest|prelate", result.get("description", ""), flags=re.I):
            entity = api(action="wbgetentities", ids=result["id"], props="claims")["entities"][result["id"]]
            for claim in entity["claims"].get("P569", []):
                value = claim["mainsnak"].get("datavalue", {}).get("value", {})
                if value.get("precision") == 11:
                    return value["time"].lstrip("+")[:10], result["id"]
    return "", ""


looked_up = {}
for m_index, m in enumerate(miranda):
    if m_index not in matches and m["created"] >= LOOKUP_BIRTHS_FROM:
        looked_up[m_index] = wikidata_birth(m["name"])
        time.sleep(1)
print(f"\nBirth dates looked up for {sum(1 for b, _ in looked_up.values() if b)} of {len(looked_up)} "
      f"cardinals created since {LOOKUP_BIRTHS_FROM[:4]} and missing from the Wikidata query")

pope_names = {p["name_full"] for p in popes}

# --- Combined dataset ---
combined = []
for m_index, m in enumerate(miranda):
    w = wikidata[matches[m_index]] if m_index in matches else {}
    combined.append({
        "name": m["name"], "qid": w.get("qid", "") or looked_up.get(m_index, ("", ""))[1], "source": "both" if w else "miranda",
        "created": m["created"], "created_precision": m["created_precision"], "created_by": m["created_by"],
        "in_pectore_note": m["notes"],
        "death": m["death"] or w.get("death", ""),
        "death_precision": m["death_precision"] if m["death"] else ("day" if w.get("death") else ""),
        "became_pope": bool(re.search(r"Elected Pope", m["notes"])) or w.get("name", "").removeprefix("Pope ") in pope_names,
        "birth": w.get("birth", "") or looked_up.get(m_index, ("", ""))[0],
        "birth_precision": w.get("birth_precision", "") or ("day" if looked_up.get(m_index, ("", ""))[0] else ""),
        "cardinal_until": w.get("cardinal_until", ""), "country": w.get("country", ""),
    })
for w_index, w in enumerate(wikidata):
    if w_index not in matched_w:
        combined.append({
            "name": w["name"], "qid": w["qid"], "source": "wikidata",
            "created": w["created"], "created_precision": w["created_precision"],
            "created_by": w["created_by_wikipedia"], "in_pectore_note": "",
            "death": w["death"], "death_precision": "day" if w["death"] else "",
            "became_pope": w["name"].removeprefix("Pope ") in pope_names,
            "birth": w["birth"], "birth_precision": w["birth_precision"],
            "cardinal_until": w["cardinal_until"], "country": w["country"],
        })
# --- Link popes to their cardinal records ---
# A cardinal elected pope stops being a cardinal; Miranda's lists often give no death date for them.
linked = 0
for pope in popes:
    birth_name = normalize(pope["Personal Name"]) if pope["Personal Name"] not in ("", "NA") else ""
    cardinalate = parse_date(pope["cardinalate_date"])
    best, best_score = None, 0
    for record in combined:
        if record["created_by"].startswith("Antipope"):
            continue
        created = parse_date(record["created"])
        if cardinalate and (not created or abs(created.year - cardinalate.year) > 1):
            continue
        if not cardinalate and (not created or created > parse_date(pope["start"])):
            continue
        score = 1.0 if record["name"].removeprefix("Pope ") == pope["name_full"] else (
            similarity(birth_name, normalize(record["name"])) if birth_name else 0)
        if score > best_score:
            best, best_score = record, score
    if best and best_score >= MIN_SIMILARITY_WITH_YEARS:
        best["became_pope"] = True
        best["cardinal_until"] = pope["start"]
        best["death"] = best["death"] or (pope["end"] if pope["end"] != "NA" else "")
        best["death_precision"] = best["death_precision"] or ("day" if best["death"] else "")
        linked += 1
print(f"Popes linked to their cardinal records: {linked} "
      f"(of {sum(1 for p in popes if p['cardinalate_date'] not in ('', 'NA'))} with a cardinalate date in popes.csv)")

with open(f"{OUTPUT_DIR}/cardinals_combined.csv", "w", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=list(combined[0]))
    writer.writeheader()
    writer.writerows(combined)
print(f"\nWrote {len(combined)} cardinals to cardinals_combined.csv "
      f"({Counter(c['source'] for c in combined)})")
