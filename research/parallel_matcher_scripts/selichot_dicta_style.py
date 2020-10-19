import django, re, csv, requests, json
from collections import defaultdict
django.setup()
from sefaria.model import *
from sefaria.system.exceptions import InputError
from tqdm import tqdm
from time import sleep

find_url = "https://talmudfinder-1-1.loadbalancer.dicta.org.il/TalmudFinder/api/markpsukim"
parse_url = "https://talmudfinder-1-1.loadbalancer.dicta.org.il/TalmudFinder/api/parsetogroups?smin=22&smax=10000"

"""
yo = ""
find_params = {
    "data": yo,
    "mode": "tanakh",  # or "mishna" or "talmud"
    "thresh": 0,
    "fdirectonly": False
}

find_response = {
    "downloadId",
    "allText",
    "results"
}


parse_params = {
    "allText": "str",
    "downloadId": "id",
    "keepredundant": True,
    "results": "results"
}

parse_response = [{
    "startIChar", "endIChar", "text", "matches": [
        {
            "matchedText",
            "mode",
            "score",
            "verseId"
        }
    ]
}]
"""

def find_matches():
    oref = Ref("Selichot Edot HaMizrach")
    segs = oref.text("he").text
    refs = oref.all_segment_refs()
    dicta_results = defaultdict(dict)
    dicta_parsed = defaultdict(list)

    count = 0
    for ref, seg in tqdm(zip(refs, segs), total=len(segs)):
        count += 1
        # if count > 3:
        #     break
        results = []
        downloadId = None
        allText = None
        for i, mode in enumerate(("tanakh", "mishna", "talmud")):
            data = {
                "data": seg,
                "mode": mode,
                "thresh": 0,
                "fdirectonly": False
            }
            response = requests.post(find_url, data=json.dumps(data))
            response_json = response.json()
            dicta_results[ref.normal()][mode] = response_json
            try:
                results += response_json["results"]
            except TypeError:
                print("ERROR", response_json)
                continue
            if i == 0:
                downloadId = response_json["downloadId"]
                allText = response_json["allText"]
            sleep(1)
        if downloadId is None:
            continue
        data = {
            "allText": allText,
            "downloadId": downloadId,
            "keepredundant": True,
            "results": results            
        }
        response = requests.post(parse_url, data=json.dumps(data))
        response_json = response.json()
        dicta_parsed[ref.normal()] = response_json
        sleep(1)
    with open("research/parallel_matcher_scripts/dicta_selichot_matches.json", "w") as fout:
        json.dump(dicta_results, fout, ensure_ascii=False)
    with open("research/parallel_matcher_scripts/dicta_selichot_parsed_matches.json", "w") as fout:
        json.dump(dicta_parsed, fout, ensure_ascii=False, indent=2)

def parse_matches():
    test = "Selichot Edot HaMizrach 2"
    with open("research/parallel_matcher_scripts/dicta_selichot_matches.json", "r") as fin:
        j = json.load(fin)
    dicta_parsed = defaultdict(list)
    for ref, mode_dict in tqdm(j.items()):
        results = []
        for mode, temp_response in mode_dict.items():
            try:
                results += temp_response["results"]
            except TypeError:
                print(temp_response)
        try:
            downloadId = mode_dict["tanakh"]["downloadId"]
            allText = mode_dict["tanakh"]["allText"]
        except TypeError:
            continue
        data = {
            "allText": allText,
            "downloadId": downloadId,
            "keepredundant": True,
            "results": results            
        }
        response = requests.post(parse_url, data=json.dumps(data))
        response_json = response.json()
        dicta_parsed[ref] = response_json
        sleep(1)
    with open("research/parallel_matcher_scripts/dicta_selichot_parsed_matches.json", "w") as fout:
        json.dump(dicta_parsed, fout, ensure_ascii=False, indent=2)

def convert_to_csv():
    with open("research/parallel_matcher_scripts/dicta_selichot_parsed_matches.json", "r") as fin:
        j = json.load(fin)
    rows = []
    for ref, results in j.items():
        for result in results:
            for match in result['matches']:
                other_ref_parts = match["verseId"].split('.')[-3:]
                book = other_ref_parts[0].replace('_', ' ')
                if other_ref_parts[-1] in {'a', 'b'}:
                    other_ref = f"{book} {''.join(other_ref_parts[1:])}"
                else:
                    other_ref = f"{book} {':'.join(other_ref_parts[1:])}"
                try:
                    other_ref = Ref(other_ref).normal()
                except InputError:
                    print("INPUTERROR", other_ref)
                    continue
                rows += [{
                    "Selichot Ref": ref,
                    "Selichot Text": re.sub('<[^>]+>', '', result["text"]),
                    "Type": match['mode'],
                    "Other Ref": other_ref,
                    "Other Text": re.sub('<[^>]+>', '', match["matchedText"]),
                }]
    with open('research/parallel_matcher_scripts/dicta_selichot_matches.csv', 'w') as fout:
        c = csv.DictWriter(fout, ['Selichot Text', 'Other Text','Type', 'Selichot Ref','Other Ref'])
        c.writeheader()
        c.writerows(rows)

def post_links():
    from sources.functions import post_link
    from sefaria.system.exceptions import DuplicateRecordError
    with open("research/parallel_matcher_scripts/final_selichot_links.csv", "r") as fin:
        c = csv.DictReader(fin)
        links = []
        for row in c:
            if row["Keep?"] == "Yes":
                links += [{
                    "refs": [
                        row["Tanakh Ref"],
                        row["Selichot Ref"]
                    ],
                    "auto": True,
                    "generated_by": "selichot_edot_hamizrach_parallel_matcher"
                }]
        for l in links:
            link = Link(l)
            try:
                link.save()
            except DuplicateRecordError:
                print("DUP", l)
        post_link(links)
if __name__ == "__main__":
    # find_matches()
    # convert_to_csv()
    post_links()
