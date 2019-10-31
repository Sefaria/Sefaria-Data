import requests
import json
import codecs
import time
import tqdm
import re
import unicodecsv
from collections import defaultdict
import django
django.setup()
from sefaria.model import *

API_URL = "https://www.wikidata.org/w/api.php"

labels = {
    "P569": "date of birth",
    "P570": "date of death",
    "P21": "sex or gender",
    "P20": "place of death",
    "P509": "cause of death",
    "P22": "father",
    "P25": "mother",
    "P26": "spouse",
    "P40": "child",
    "P106": "occupation",
    "P39": "position held",
    "P1441": "present in work",
}

tanakh = {
    "Q9184": "Genesis",
    "Q9190": "Exodus",
    "Q41490": "Leviticus",
    "Q43099": "Numbers",
    "Q42614": "Deuteronomy",
    "Q47680": "Joshua",
    "Q81240": "Judges",
    "Q1975029": "I Samuel",
    "Q209719": "II Samuel",
    "Q181620": "Samuels",
    "Q131066": "I Kings",
    "Q209746": "II Kings",
    "Q131458": "Isaiah",
    "Q131590": "Jeremiah",
    "Q178390": "Ezekiel",
    "Q184030": "Hoshea",
    "Q131643": "Joel",
    "Q174677": "Amos",
    "Q174753": "Obadiah",
    "Q178819": "Jonah",
    "Q178076": "Micah",
    "Q179755": "Nahum",
    "Q179760": "Habakkuk",
    "Q188563": "Zephaniah",
    "Q178338": "Haggai",
    "Q179769": "Zechariah",
    "Q51675": "Malachi",
    "Q41064": "Psalms",
    "Q4579": "Proverbs",
    "Q4577": "Job",
    "Q51670": "Song of Songs",
    "Q80038": "Ruth",
    "Q179058": "Lamentations",
    "Q131072": "Ecclesiastes",
    "Q131068": "Esther",
    "Q80115": "Daniel",
    "Q131635": "Ezra",
    "Q131640": "Nehemiah",
    "Q9813916": "I Chronicles",
    "Q209720": "II Chronicles",
    "Q161953": "Books of Chronicles"
}
query = "josiah"
e = 'wbsearchentities'
c = 'wbgetclaims'
params = {
    'action': e,
    'format': 'json',
    'language': 'en',
    'search': query
}
cparams = {
    'action': c,
    'entity': 'Q313228',
    'format': 'json'
}
# P373
def translate_claims(claims):
    translated = defaultdict(list)
    for k, v in claims.items():
        if k in labels:
            for subv in v:
                try:
                    datavalue = json.dumps(subv['mainsnak']['datavalue'])
                except KeyError:
                    continue
                datatype = subv['mainsnak']['datatype']
                r = requests.get(API_URL, params={"format": "json", "generate": "text/plain", "action": "wbformatvalue", "datatype": datatype, "datavalue": datavalue})
                translated[labels[k]] += [{
                    "string": r.json()["result"],
                    "id": subv['mainsnak']['datavalue']['value'].get('id', None) if isinstance(subv['mainsnak']['datavalue']['value'], dict) else None
                }]
        else:
            pass
    return translated


def filter_biblical_figures_csv():
    with open("biblical_figures.csv", "rb") as fin:
        mapping = defaultdict(list)
        cin = unicodecsv.DictReader(fin)
        for row in cin:
            mapping[row["item"].replace("http://www.wikidata.org/entity/", "")] += [{"name": row["itemLabel"], "bookName": row["present_in_workLabel"], "bookId": row["present_in_work"].replace("http://www.wikidata.org/entity/", "")}]
    good_guys = []
    bad_guys = []
    good_books = set(tanakh.keys())
    for k, v in mapping.items():
        filt = map(lambda x: tanakh[x["bookId"]] if x["bookId"] in good_books else Ref(x["bookName"]).normal(), filter(lambda x: x["bookId"] in good_books or (len(x["bookName"]) > 0 and Ref.is_ref(x["bookName"])), v))

        if len(filt) > 0:
            good_guys += [{"name": v[0]["name"], "id": k, "presentIn": filt}]
    return good_guys
#r = requests.get(API_URL, params=cparams)
#translate_wikicode(r.json())

def get_all_tanakh_peeps():
    good_guys = filter_biblical_figures_csv()
    for g in good_guys:
        print g["name"], g["id"]
    out = {"entities": {}}
    for i in xrange(0, len(good_guys), 50):
        time.sleep(1)
        print i
        good_ids = "|".join([x["id"] for x in good_guys[i:i+50]])
        r = requests.get(API_URL, params={"action": "wbgetentities", "ids": good_ids, "format": "json", "languages": "en|he"})
        j = r.json()
        out["entities"].update(j["entities"])
    with codecs.open("all_tanakh_wikidata.json", "wb", encoding="utf8") as fout:
        json.dump(out, fout, indent=2, ensure_ascii=False)


def project_tanakh_data():
    failed = ["Q30226372", "Q830183", "Q1676803", "Q794991", "Q192785", "Q229702", "Q937827", "Q200637", "Q214648",
              "Q221826", "Q30226376", "Q70899", "Q26835883", "Q665541", "Q37085", "Q184273"]

    with codecs.open("all_tanakh_wikidata.json", "rb", encoding="utf8") as fin:
        jin = json.load(fin)
    out = {}
    for id, v in tqdm.tqdm(jin["entities"].items()):
        if id not in failed:
            continue
        try:
            translated = translate_claims(v["claims"])
        except KeyError:
            print id, u"failed"
            continue
        translated["aliases"] = v.get("aliases", {})
        out[id] = translated
    good_guys = filter_biblical_figures_csv()
    gmap = {}
    for g in good_guys:
        gmap[g["id"]] = g
    with codecs.open("all_tanakh_projected.json", "rb", encoding="utf8") as fin:
        jin2 = json.load(fin)
        jin2.update(out)
    for id, v in jin2.items():
        jin2[id]["name"] = gmap[id]["name"]
        jin2[id]["presentIn"] = gmap[id]["presentIn"]
    with codecs.open("all_tanakh_projected.json", "wb", encoding="utf8") as fout:
        json.dump(jin2, fout, indent=2, ensure_ascii=False)


def add_he_labels():
    with codecs.open("all_tanakh_wikidata.json", "rb", encoding="utf8") as fin:
        jin = json.load(fin)
    with codecs.open("all_tanakh_projected.json", "rb", encoding="utf8") as fin:
        jin2 = json.load(fin)
    for k, v in jin2.items():
        helab = jin["entities"].get(k, {}).get("labels", {}).get("he", {}).get("value", None)
        enlab = jin["entities"].get(k, {}).get("labels", {}).get("en", {}).get("value", None)
        if helab is not None and len(helab) > 0 and not re.match(r"^Q\d+$", helab):
            jin2[k]["heName"] = helab
            print u"heb name!", helab
        if enlab is not None and len(enlab) > 0 and not re.match(r"^Q\d+$", enlab) and re.match(r"^Q\d+$", jin2[k]["name"]):
            jin2[k]["name"] = enlab  # prev name was just an ID
            print "Better name", enlab
    with codecs.open("all_tanakh_projected.json", "wb", encoding="utf8") as fout:
        json.dump(jin2, fout, indent=2, ensure_ascii=False)

# TODO
# filter out people referenced that don't appear as keys
# filter out people not in tanakh
# get Hebrew names

add_he_labels()
characters = [
    "Adam",
    "Seth",
    "Enos",
    "Kenan",
    "Mehalalel",
    "Jared",
    "Enoch",
    "Methuselah",
    "Lamech",
    "Noah",
    "Shem",
    "Cain",
    "Irad",
    "Mehujael",
    "Methusael",
    "Tubal-cain",
    "Arpachshad",
    "Cainan",
    "Shelah",
    "Eber",
    "Peleg",
    "Reu",
    "Serug",
    "Nahor",
    "Terah",
    "Abraham",
    "Isaac",
    "Jacob",
    "Judah",
    "Perez",
    "Hezron",
    "Ram",
    "Amminadab",
    "Nahshon",
    "Salmon",
    "Boaz",
    "Obed",
    "Jesse",
    "David",
]

prophets = [
   "Abel",
    "Kenan",
    "Enoch",
    "Noah",
    "Abraham",
    "Isaac",
    "Jacob",
    "Levi",
    "Joseph",
    "Sarah",
    "Rebecca",
    "Rachel",
    "Leah",
    "Moses",
    "Aaron",
    "Miriam",
    "Eldad and Meidad",
    "Phinehas",
    "Joshua",
    "Deborah",
    "Gideon",
    "Eli",
    "Elkanah",
    "Hannah",
    "Abigail",
    "Samuel",
    "Gad",
    "Nathan",
    "David",
    "Solomon",
    "Jeduthun",
    "Ahijah",
    "Shemaiah",
    "Elijah",
    "Elisha",
    "Iddo",
    "Hanani",
    "Jehu",
    "Micaiah",
    "Jahaziel",
    "Eliezer",
    "Zechariah ben Jehoiada",
    "Huldah",
    "Isaiah",
    "Jeremiah",
    "Ezekiel",
    "Daniel",
    "Hosea",
    "Joel",
    "Amos",
    "Obadiah",
    "Jonah",
    "Micah",
    "Nahum",
    "Habakkuk",
    "Zephaniah",
    "Haggai",
    "Zechariah",
    "Malachi"
]

OtherProphets = [
    "Beor",
    "Balaam",
    "Job",
    "Amoz",
    "Beeri",
    "Baruch",
    "Agur",
    "Uriah",
    "Buzi",
    "Mordecai",
    "Esther",
    "Oded",
    "Azariah"
]

UnitedKings = [
    "Saul",
    "Ish-bosheth",
    "David",
    "Solomon"
]
IsraelKings = [
    "Jeroboam I",
    "Nadab",
    "Baasha",
    "Elah",
    "Zimri",
    "Tibni",
    "Omri",
    "Ahab",
    "Ahaziah",
    "Jehoram",
    "Jehu",
    "Jehoahaz",
    "Jehoash",
    "Jeroboam II",
    "Zechariah",
    "Shallum",
    "Menahem",
    "Pekahiah",
    "Pekah",
    "Hoshea"
]
JudahKings = [
    "Rehoboam",
    "Abijam",
    "Asa",
    "Jehoshaphat",
    "Jehoram",
    "Ahaziah",
    "Athaliah",
    "Jehoash",
    "Amaziah",
    "Uzziah",
    "Jotham",
    "Ahaz",
    "Hezekiah",
    "Manasseh",
    "Amon",
    "Josiah",
    "Jehoahaz",
    "Jehoiakim",
    "Jeconiah",
    "Zedekiah"
]
OtherRulers = [
    "Abimelech",
    "Simon Thassi",
    "John Hyrcanus"
]

HighPriests = [
    "Aaron",
    "Eleazar",
    "Eli",
    "Phinehas"
]

Tribes = [
    "Judah",
    "Asher",
    "Benjamin",
    "Dan",
    "Gad",
    "Issachar",
    "Joseph",
    "Menasheh",
    "Ephraim",
    "Levi",
    "Naphtali",
    "Reuben",
    "Simeon",
    "Zebulun"
]


