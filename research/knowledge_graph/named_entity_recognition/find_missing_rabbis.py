import django, re, json, csv, srsly
django.setup()
from tqdm import tqdm
from collections import defaultdict
from sefaria.model import *

DATA_LOC = "/home/nss/sefaria/datasets/ner/michael-sperling"
stopwords = {'whence', 'here', 'show', 'were', 'why', 'n’t', 'the', 'whereupon', 'not', 'more', 'how', 'eight', 'indeed', 'i', 'only', 'via', 'nine', 're', 'themselves', 'almost', 'to', 'already', 'front', 'least', 'becomes', 'thereby', 'doing', 'her', 'together', 'be', 'often', 'then', 'quite', 'less', 'many', 'they', 'ourselves', 'take', 'its', 'yours', 'each', 'would', 'may', 'namely', 'do', 'whose', 'whether', 'side', 'both', 'what', 'between', 'toward', 'our', 'whereby', "'m", 'formerly', 'myself', 'had', 'really', 'call', 'keep', "'re", 'hereupon', 'can', 'their', 'eleven', '’m', 'even', 'around', 'twenty', 'mostly', 'did', 'at', 'an', 'seems', 'serious', 'against', "n't", 'except', 'has', 'five', 'he', 'last', '‘ve', 'because', 'we', 'himself', 'yet', 'something', 'somehow', '‘m', 'towards', 'his', 'six', 'anywhere', 'us', '‘d', 'thru', 'thus', 'which', 'everything', 'become', 'herein', 'one', 'in', 'although', 'sometime', 'give', 'cannot', 'besides', 'across', 'noone', 'ever', 'that', 'over', 'among', 'during', 'however', 'when', 'sometimes', 'still', 'seemed', 'get', "'ve", 'him', 'with', 'part', 'beyond', 'everyone', 'same', 'this', 'latterly', 'no', 'regarding', 'elsewhere', 'others', 'moreover', 'else', 'back', 'alone', 'somewhere', 'are', 'will', 'beforehand', 'ten', 'very', 'most', 'three', 'former', '’re', 'otherwise', 'several', 'also', 'whatever', 'am', 'becoming', 'beside', '’s', 'nothing', 'some', 'since', 'thence', 'anyway', 'out', 'up', 'well', 'it', 'various', 'four', 'top', '‘s', 'than', 'under', 'might', 'could', 'by', 'too', 'and', 'whom', '‘ll', 'say', 'therefore', "'s", 'other', 'throughout', 'became', 'your', 'put', 'per', "'ll", 'fifteen', 'must', 'before', 'whenever', 'anyone', 'without', 'does', 'was', 'where', 'thereafter', "'d", 'another', 'yourselves', 'n‘t', 'see', 'go', 'wherever', 'just', 'seeming', 'hence', 'full', 'whereafter', 'bottom', 'whole', 'own', 'empty', 'due', 'behind', 'while', 'onto', 'wherein', 'off', 'again', 'a', 'two', 'above', 'therein', 'sixty', 'those', 'whereas', 'using', 'latter', 'used', 'my', 'herself', 'hers', 'or', 'neither', 'forty', 'thereupon', 'now', 'after', 'yourself', 'whither', 'rather', 'once', 'from', 'until', 'anything', 'few', 'into', 'such', 'being', 'make', 'mine', 'please', 'along', 'hundred', 'should', 'below', 'third', 'unless', 'upon', 'perhaps', 'ours', 'but', 'never', 'whoever', 'fifty', 'any', 'all', 'nobody', 'there', 'have', 'anyhow', 'of', 'seem', 'down', 'is', 'every', '’ll', 'much', 'none', 'further', 'me', 'who', 'nevertheless', 'about', 'everywhere', 'name', 'enough', '’d', 'next', 'meanwhile', 'though', 'through', 'on', 'first', 'been', 'hereby', 'if', 'move', 'so', 'either', 'amongst', 'for', 'twelve', 'nor', 'she', 'always', 'these', 'as', '’ve', 'amount', '‘re', 'someone', 'afterwards', 'you', 'nowhere', 'itself', 'done', 'hereafter', 'within', 'made', 'ca', 'them'}
def myunidecode(text):
    # 'ăǎġḥḤḫḳḲŏṭżūŻāīēḗîìi̧'
    table = {
        "ḥ": "h",
        "Ḥ": "H",
        "ă": "a",
        "ǎ": "a",
        "ġ": "g",
        "ḫ": "h",
        "ḳ": "k",
        "Ḳ": "K",
        "ŏ": "o",
        "ṭ": "t",
        "ż": "z",
        "Ż": "Z",
        "’": "'"
    }
    for k, v in table.items():
        text = text.replace(k, v)
    return text

def guess_english():
    sef_id_map = {}
    with open("/home/nss/sefaria/data/research/knowledge_graph/named_entity_recognition/sefaria_bonayich_reconciliation - Sheet2.csv", "r") as fin:
        c = csv.DictReader(fin)
        for row in c:
            try:
                sef_id_map[int(row["bonayich"])] = row["Slug"]
            except ValueError:
                continue

    out = []
    aggregated_mentions = defaultdict(lambda: {"he": "", "ens": defaultdict(int), "refs": [], "text": ""})
    combined = srsly.read_jsonl(f"{DATA_LOC}/combined_mentions.jsonl")

    token_counts = defaultdict(set)
    unique_ids = set()
    for row in tqdm(combined):
        temp_missed = {}
        for mention in row["He Mentions"]:
            if mention["Bonayich ID"] not in sef_id_map:
                temp_missed[mention["Bonayich ID"]] = mention["Mention"]
        temp_guesses = []
        if len(temp_missed) > 0:
            en = Ref(row["Ref"]).text("en").text
            already_found = {m["Mention"] for m in filter(lambda x: x["Bonayich ID"] is not None, row["En Mentions"])}
            en = " ".join(re.sub("<[^>]+>", " ", myunidecode(en)).split())
            potential_rabbis = re.finditer(r'(?:(?:(?:Rabbi|Rav|Rabban|ben) )?(?:[A-Z][a-z\']+)(?:(?: ben| bar|, son of|, from|, from the) )?)+(?=\s|$|[.,\"?!()\[\]:;<>\-]|\'s)', en)
            for pot_rabbi in potential_rabbis:
                guess = re.sub(r"'s$", "", pot_rabbi.group())
                if guess.lower() in stopwords:  # guess in already_found or 
                    continue
                for mention in row["He Mentions"]:
                    token_counts[guess].add(mention["Bonayich ID"])
                    unique_ids.add(mention["Bonayich ID"])
                temp_guesses += [guess]
            out += [{
                "Ref": row["Ref"],
                "Book": row["Book"],
                "He Missed": [{"Bonayich ID": k, "Mention": v} for k, v in temp_missed.items()],
                "En Guesses": temp_guesses
            }]
            for he in out[-1]["He Missed"]:
                aggregated_mentions[he["Bonayich ID"]]["he"] = he["Mention"]
                aggregated_mentions[he["Bonayich ID"]]["refs"] += [row["Ref"]]
                aggregated_mentions[he["Bonayich ID"]]["text"] = en
                for en in out[-1]["En Guesses"]:
                    aggregated_mentions[he["Bonayich ID"]]["ens"][en] += 1

    custom_stopwords = set()
    for token, doc_set in token_counts.items():
        if len(doc_set) > (0.08*len(unique_ids)) and token not in {"Rabbi Zeira", "Ravina"}:
            custom_stopwords.add(token)
    print("CUSTOM STOPWORDS", custom_stopwords)
    best_aggregates = []
    for k, v in aggregated_mentions.items():
        item = {
            "Bonayich ID": k,
            "He": v["he"],
            "Ens": list(filter(lambda x: x not in custom_stopwords, [x[0] for x in list(sorted(v["ens"].items(), key=lambda x: x[1], reverse=True))]))[:3],
            "Example": v["text"],
            "Refs": v["refs"][:5]
        }
        item["Final En"] = ""
        if len(item["Ens"]) > 0:
            item["Final En"] = item["Ens"][0]
        best_aggregates += [item]
    print(len(best_aggregates))
    with open(f"{DATA_LOC}/en_guesses.json", "w") as fout:
        json.dump(out, fout, ensure_ascii=False, indent=True)
    with open(f"{DATA_LOC}/best_en_guesses.json", "w") as fout:
        json.dump(best_aggregates, fout, ensure_ascii=False, indent=True)

def convert_final_en_names_to_csv():
    bid_to_he = {}
    with open(f"{DATA_LOC}/AllNameReferences.csv", "r") as fin:
        c = csv.DictReader(fin)
        for r in c:
            bid_to_he[int(r[" Rabbi ID after Link"])] = r[" Rabbi Name after Link"]
    json_data = srsly.read_json(f"{DATA_LOC}/best_en_guesses_final.json")
    rows = []
    for guy in json_data:
        row = {
            "Bonayich ID": guy["Bonayich ID"],
            "He": bid_to_he[guy["Bonayich ID"]],
            "He Mention": guy["He"],
        }
        en_list = guy["Final En"] if isinstance(guy["Final En"], list) else [guy["Final En"]]
        for i, en in enumerate(en_list):
            en = en[0].capitalize() + en[1:]
            row[f"En {i+1}"] = en
        for i, r in enumerate(guy["Refs"]):
            row[f"Ref {i+1}"] = r
        rows += [row]
    with open(f"{DATA_LOC}/sperling_en_and_he.csv", "w") as fout:
        c = csv.DictWriter(fout, ["Bonayich ID", "He", "En 1", "En 2", "En 3", "He Mention", "Ref 1", "Ref 2", "Ref 3", "Ref 4", "Ref 5"])
        c.writeheader()
        c.writerows(rows)

def find_ambiguous_rabbis():
    ambiguous_topics = {t.slug for t in TopicSet({"titles.disambiguation": {"$exists": True}})}
    rabbis = Topic.init('talmudic-people').topics_by_link_type_recursively(only_leaves=True) + Topic.init('mishnaic-people').topics_by_link_type_recursively(only_leaves=True)
    ambiguous_rabbis = list(filter(lambda x: x.slug in ambiguous_topics, rabbis))
    for r in ambiguous_rabbis:
        print(r.slug)

def check_rabbi_yehuda_hanasi():
    bad = 0
    with open(f"{DATA_LOC}/rabbi_yehuda_hanasi.csv", "r") as fin:
        rows = list(csv.DictReader(fin))
    with open(f"{DATA_LOC}/rabbi_yehuda_hanasi_bad.txt", "w") as fout:
        for row in rows:
            ref = row["Segment"]
            try:
                seg_text = " ".join(re.sub(r"<[^>]+>", " ", Ref(ref).text("en").text).split())
            except:
                print("BAD REF", ref)
            if not re.search(r"Rabbi Yehuda HaNasi", seg_text):
                bad+=1
                fout.write(f"{ref}\n{seg_text}\n")
    print(bad)

def convert_final_en_names_to_ner_tagger_input():
    with open(f"{DATA_LOC}/sperling_en_and_he.csv", "r") as fin:
        sperling_entities = []
        c = csv.DictReader(fin)
        for row in c:
            en1 = row["En 1"].strip()
            if len(en1) == 0 or en1 == "N/A" or en1 == "MM":
                continue
            bid = row['Bonayich ID']
            en_titles = []
            for i in range(3):
                temp_en = row[f'En {i+1}']
                if len(temp_en) == 0:
                    continue
                en_titles += [temp_en]
            tag = "NORP" if len(row["Is Group"]) > 0 else "PERSON"
            sperling_entities += [{
                "tag": tag,
                "id": f"BONAYICH:{bid}",
                "idIsSlug": False,
                "manualTitles": [{"text": title, "lang": "en"} for title in en_titles] + [{"text": row["He"], "lang": "he"}]
            }]
        with open(f"{DATA_LOC}/sperling_ner_tagger_input.json", "w") as fout:
            json.dump(sperling_entities, fout, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    # convert_final_en_names_to_csv()
    # find_ambiguous_rabbis()
    # check_rabbi_yehuda_hanasi()
    convert_final_en_names_to_ner_tagger_input()