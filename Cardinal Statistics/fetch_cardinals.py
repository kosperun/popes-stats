"""Download all cardinals from Wikidata into cardinals.csv.

A cardinal is anyone holding the position "cardinal" (Q45722) or one of its subclasses
(cardinal-bishop, cardinal-priest, cardinal-deacon, ...), excluding pseudocardinals.
Dates before 1582 are returned by Wikidata converted to the Gregorian calendar.
The creating pope comes from English Wikipedia's "Cardinals created by Pope X" categories.
"""

import csv
from collections import defaultdict
import json
import re
import time
import urllib.parse
import urllib.request

OUTPUT_DIR = "Cardinal Statistics"
SPARQL_URL = "https://query.wikidata.org/sparql"
USER_AGENT = "popes-stats/1.0 (https://github.com/kosperun/popes-stats)"
CARDINAL = "wd:Q45722"
PSEUDOCARDINAL = "wd:Q956561"
# Offices held by cardinals (also subclasses of "cardinal" in Wikidata). Their start dates mark
# the appointment to the office, not the creation as cardinal, so they are ignored for "created".
OFFICES = {
    "Q1813197",  # Camerlengo of the Sacred College of Cardinals
    "Q449676",  # Dean of the College of Cardinals
    "Q1054345",  # Cardinal Secretary of State
    "Q1729117",  # Cardinal Vicar
    "Q7175168",  # cardinal protodeacon
    "Q1793097",  # cardinal of the Roman Curia
}
# Wikidata date precision: 9 = year, 10 = month, 11 = day
PRECISION = {"9": "year", "10": "month", "11": "day"}

# Historical states mapped to the modern country, as in popes.csv.
# States without a single modern successor are left out and reported as ambiguous.
MODERN_COUNTRY = {
    "Kingdom of Italy": "Italy", "Papal States": "Italy", "Republic of Venice": "Italy", "Republic of Genoa": "Italy",
    "Kingdom of Naples": "Italy", "Grand Duchy of Tuscany": "Italy", "Duchy of Milan": "Italy", "Kingdom of Sardinia": "Italy",
    "Republic of Siena": "Italy", "Lordship of Bologna": "Italy", "March of Tuscany": "Italy", "Duchy of Modena and Reggio": "Italy",
    "Kingdom of Sicily": "Italy", "Kingdom of the Two Sicilies": "Italy", "Signoria of Milan": "Italy", "Republic of Florence": "Italy",
    "Vatican City": "Italy", "Duchy of Savoy": "Italy",
    "Kingdom of France": "France", "Duchy of Burgundy": "France",
    "Crown of Aragon": "Spain", "Crown of Castile": "Spain", "Kingdom of Aragon": "Spain", "Kingdom of Navarre": "Spain",
    "Principality of Catalonia": "Spain", "Kingdom of Leon": "Spain",
    "Kingdom of Portugal": "Portugal",
    "United Kingdom of Great Britain and Ireland": "United Kingdom", "Kingdom of England": "United Kingdom",
    "England": "United Kingdom", "Scotland": "United Kingdom", "Wales": "United Kingdom",
    "Irish Free State": "Ireland",
    "Polish–Lithuanian Commonwealth": "Poland", "Kingdom of Poland": "Poland", "Second Polish Republic": "Poland",
    "Royal Prussia": "Poland",
    "Kingdom of Prussia": "Germany", "Kingdom of Bavaria": "Germany", "Electorate of Bavaria": "Germany", "German Reich": "Germany",
    "Duchy of Saxony": "Germany", "Electorate of Hesse": "Germany", "Margraviate of Brandenburg": "Germany", "Prussia": "Germany",
    "West Germany": "Germany",
    "Archduchy of Austria": "Austria",
    "Kingdom of Hungary": "Hungary", "Kingdom of Bohemia": "Czech Republic", "Moravia": "Czech Republic",
    "Kingdom of the Netherlands": "Netherlands", "Kingdom of Denmark": "Denmark",
    "Kingdom of Romania": "Romania", "Socialist Republic of Romania": "Romania", "Romanian People's Republic": "Romania",
    "Principality of Transylvania": "Romania", "Grand Duchy of Lithuania": "Lithuania",
    "Independent State of Croatia": "Croatia",
    "British Raj": "India", "Dominion of India": "India", "Empire of Japan": "Japan",
    "People's Republic of China": "China", "Republic of China": "China",
    "Kingdom of Egypt": "Egypt", "Republic of Egypt": "Egypt", "United Arab Republic": "Egypt",
    "British Hong Kong": "China", "Kingdom of Cyprus": "Cyprus",
}
AMBIGUOUS = {
    "Habsburg monarchy", "Austrian Empire", "Austria–Hungary", "Cisleithania", "Holy Roman Empire", "Byzantine Empire",
    "Ottoman Empire", "Russian Empire", "Soviet Union", "Czechoslovakia", "Kingdom of Yugoslavia",
    "Federal People's Republic of Yugoslavia", "Socialist Federal Republic of Yugoslavia",
    "Kingdom of Serbs, Croats and Slovenes", "Habsburg Netherlands",
}

POSITIONS_QUERY = f"""
SELECT ?p ?pos ?start ?startPrecision ?end WHERE {{
  ?p p:P39 ?statement . ?statement ps:P39 ?pos . ?pos wdt:P279* {CARDINAL} . FILTER(?pos != {PSEUDOCARDINAL})
  OPTIONAL {{ ?statement pqv:P580 ?startValue . ?startValue wikibase:timeValue ?start ; wikibase:timePrecision ?startPrecision }}
  OPTIONAL {{ ?statement pq:P582 ?end }}
}}"""

PEOPLE_QUERY = f"""
SELECT ?p ?pLabel ?birth ?birthPrecision ?death ?countryLabel WHERE {{
  {{ SELECT DISTINCT ?p WHERE {{ ?p p:P39/ps:P39 ?pos . ?pos wdt:P279* {CARDINAL} . FILTER(?pos != {PSEUDOCARDINAL}) }} }}
  OPTIONAL {{ ?p p:P569/psv:P569 ?birthValue . ?birthValue wikibase:timeValue ?birth ; wikibase:timePrecision ?birthPrecision }}
  OPTIONAL {{ ?p wdt:P570 ?death }}
  OPTIONAL {{ ?p wdt:P27 ?country }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,it,fr,es,de,la". }}
}}"""


WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"


def wikipedia(**params):
    params.update(format="json")
    request = urllib.request.Request(f"{WIKIPEDIA_API}?{urllib.parse.urlencode(params)}", headers={"User-Agent": USER_AGENT})
    return json.load(urllib.request.urlopen(request, timeout=120))


def creators_from_wikipedia(pope_names):
    """{Wikidata QID: [popes]} from English Wikipedia's "Cardinals created by Pope X" categories."""
    titles = defaultdict(list)
    for pope in pope_names:
        params = {"action": "query", "list": "categorymembers", "cmtitle": f"Category:Cardinals created by Pope {pope}",
                  "cmlimit": 500, "cmnamespace": 0}
        while True:
            data = wikipedia(**params)
            for member in data["query"]["categorymembers"]:
                titles[member["title"]].append(pope)
            if "continue" not in data:
                break
            params.update(data["continue"])
        time.sleep(0.5)
    creators = {}
    names = list(titles)
    for i in range(0, len(names), 50):
        data = wikipedia(action="query", prop="pageprops", ppprop="wikibase_item", redirects=1, titles="|".join(names[i:i + 50]))
        renamed = {r["to"]: r["from"] for r in data["query"].get("normalized", []) + data["query"].get("redirects", [])}
        for page in data["query"]["pages"].values():
            item = page.get("pageprops", {}).get("wikibase_item")
            title = renamed.get(page["title"], page["title"])
            if item and title in titles:
                creators.setdefault(item, []).extend(titles[title])
        time.sleep(0.5)
    return creators


def run(query):
    request = urllib.request.Request(
        f"{SPARQL_URL}?{urllib.parse.urlencode({'query': query, 'format': 'json'})}",
        headers={"User-Agent": USER_AGENT},
    )
    rows = json.load(urllib.request.urlopen(request, timeout=300))["results"]["bindings"]
    return [{key: value["value"] for key, value in row.items()} for row in rows]


def qid(uri):
    return uri.rsplit("/", 1)[-1]


def day(timestamp):
    # "+1590-12-05T00:00:00Z" or "1590-12-05T00:00:00Z" -> "1590-12-05"; "unknown value" is a URI
    match = re.match(r"\+?(\d{4}-\d{2}-\d{2})", timestamp or "")
    return match.group(1) if match else ""


def main():
    people = {}
    for row in run(PEOPLE_QUERY):
        person = people.setdefault(qid(row["p"]), {
            "qid": qid(row["p"]), "name": row.get("pLabel", ""), "birth": "", "birth_precision": "",
            "death": "", "countries": set(),
        })
        if row.get("birth") and not person["birth"]:
            person["birth"] = day(row["birth"])
            person["birth_precision"] = PRECISION.get(row.get("birthPrecision"), "")
        if row.get("death") and not person["death"]:
            person["death"] = day(row["death"])
        if row.get("countryLabel") and not row["countryLabel"].startswith("http"):
            person["countries"].add(row["countryLabel"])

    for row in run(POSITIONS_QUERY):
        person = people[qid(row["p"])]
        start = day(row.get("start", "")) if qid(row["pos"]) not in OFFICES else ""
        if start and (not person.get("created") or start < person["created"]):
            person["created"] = start
            person["created_precision"] = PRECISION.get(row.get("startPrecision"), "")
        # The end of the plain "cardinal" position marks deposition, resignation or election as pope
        if row["pos"].endswith("/Q45722") and row.get("end"):
            person["cardinal_until"] = day(row["end"])

    with open("popes.csv") as file:
        pope_names = list(dict.fromkeys(row["name_full"] for row in csv.DictReader(file)))
    creators = creators_from_wikipedia(pope_names)

    for person in people.values():
        # A few cardinals are in more than one category; keep them all, separated by ";"
        person["created_by_wikipedia"] = ";".join(creators.get(person["qid"], []))
        modern = sorted({MODERN_COUNTRY.get(c, c) for c in person["countries"] if c not in AMBIGUOUS})
        person["country"] = modern[0] if len(modern) == 1 else (" / ".join(modern) if modern else "")
        person["country_ambiguous"] = ";".join(sorted(c for c in person["countries"] if c in AMBIGUOUS))
        person["countries"] = ";".join(sorted(person["countries"]))

    fieldnames = ["qid", "name", "birth", "birth_precision", "created", "created_precision", "created_by_wikipedia",
                  "cardinal_until", "death", "country", "countries", "country_ambiguous"]
    with open(f"{OUTPUT_DIR}/cardinals.csv", "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for person in sorted(people.values(), key=lambda p: (p.get("created") or "9999", p["name"])):
            writer.writerow(person)
    print(f"Wrote {len(people)} cardinals, {sum(1 for p in people.values() if p.get('created'))} with a creation date, "
          f"{sum(1 for p in people.values() if p['created_by_wikipedia'])} with a creating pope from Wikipedia")


if __name__ == "__main__":
    main()
