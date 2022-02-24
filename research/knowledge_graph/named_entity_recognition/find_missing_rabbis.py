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
    from sefaria.utils.hebrew import is_hebrew
    matched_bon_id_set = set()
    with open(f"{DATA_LOC}/Match Bonayich Rabbis with Sefaria Rabbis - Sefaria Rabbis Matched.csv", "r") as fin:
        c = csv.DictReader(fin)
        for row in c:
            try:
                matched_bon_id_set.add(int(row["Bonayich ID"]))
            except ValueError:
                continue
    bonayich_metadata = {}
    with open(f"{DATA_LOC}/AllRabbisWithSegs.csv", "r") as fin:
        c = csv.DictReader(fin)
        for row in c:
            bid = int(row[' Rabbi ID after Link'])
            if bid in bonayich_metadata:
                continue
            bonayich_metadata[bid] = {
                "type": row[" Rabbi Type after Link"],
                "gen": row[" Rabbi Generation after Link"]
            }
    num_not_matched = 0
    with open(f"{DATA_LOC}/sperling_en_and_he.csv", "r") as fin:
        sperling_entities = []
        c = csv.DictReader(fin)
        for row in c:
            if row['Exists in DB'] == 'y':
                continue
            en1 = row["En 1"].strip()
            if len(en1) == 0 or en1 == "N/A" or en1 == "MM":
                continue
            bid = row['Bonayich ID']
            en_titles = []
            for i in range(6):
                temp_en = row[f'En {i+1}']
                if len(temp_en) == 0:
                    continue
                en_titles += [temp_en]
            try:
                if int(bid) in matched_bon_id_set:
                    print("MATCHED", bid, en_titles)
                    continue
                else:
                    num_not_matched += 1
                    # print("NOT MATCHED", bid, en_titles)
            except ValueError:
                pass # these are extra rabbis I added that weren't in Bonayich
            tag = "NORP" if len(row["Is Group"]) > 0 else "PERSON"
            sperling_entities += [{
                "tag": tag,
                "id": f"BONAYICH:{bid}",
                "idIsSlug": False,
                "manualTitles": [{"text": title, "lang": "he" if is_hebrew(title) else "en"} for title in en_titles] + [{"text": row["He"], "lang": "he"}],
                "gen": bonayich_metadata[int(bid)]["gen"] if (bid != 'N/A' and False) else None,  # manually leave this data out for now
                "type": bonayich_metadata.get(int(bid), {}).get("type", '') if bid != 'N/A' else None
            }]
        with open(f"external_named_entities/sperling_named_entities.json", "w") as fout:
            json.dump(sperling_entities, fout, ensure_ascii=False, indent=2)
        print("TOTAL NOT MATCHED", num_not_matched)

def create_csv_for_rav_nataf():
    sef_rabbis = Topic.init('talmudic-people').topics_by_link_type_recursively(only_leaves=True) + Topic.init('mishnaic-people').topics_by_link_type_recursively(only_leaves=True)
    sef_id_map = {}
    with open("/home/nss/sefaria/data/research/knowledge_graph/named_entity_recognition/sefaria_bonayich_reconciliation - Sheet2.csv", "r") as fin:
        c = csv.DictReader(fin)
        for row in c:
            try:
                sef_id_map[row['Slug']] = int(row["bonayich"])
            except ValueError:
                continue
    rows = []
    for rab in sef_rabbis:
        rows += [{
            "Slug": rab.slug,
            "En": rab.get_primary_title("en"),
            "He": rab.get_primary_title("he"),
            "Bonayich ID": sef_id_map.get(rab.slug, '')
        }]
    with open(f"{DATA_LOC}/curr_sefaria_bonayich_mapping.csv", "w") as fout:
        c = csv.DictWriter(fout, ['Slug', 'En', 'He', 'Bonayich ID'])
        c.writeheader()
        c.writerows(rows)
    
    bon_rabs = defaultdict(lambda: {"segments": set(), "mentions": set()})
    with open(f"{DATA_LOC}/AllRabbisWithSegs.csv", "r") as fin:
        c = csv.DictReader(fin)
        for row in c:
            bid = row[' Rabbi ID after Link']
            bon_rabs[bid]['he'] = row[' Rabbi Name after Link']
            bon_rabs[bid]['mentions'].add(row[' Rabbi Name w/o Prefix'])
            bon_rabs[bid]['segments'].add(row['Segment'])
    
    bon_to_en = {}
    with open(f"{DATA_LOC}/sperling_en_and_he.csv", "r") as fin:
        c = csv.DictReader(fin)
        for row in c:
            en = row['En 1']
            if en == "MM" or en == "N/A" or len(en) == 0:
                continue 
            bon_to_en[row['Bonayich ID']] = en
    rows = []
    for bid, bdict in bon_rabs.items():
        rows += [{
            "Bonayich ID": bid,
            "He": bdict['he'],
            "En": bon_to_en.get(bid, ''),
            'Mentions': ' | '.join(bdict['mentions']),
            "Segments": ' | '.join(bdict['segments'])
        }]
    with open(f"{DATA_LOC}/all_bonayich_rabbis.csv", "w") as fout:
        c = csv.DictWriter(fout, ["Bonayich ID", "He", "En", "Mentions", "Segments"])
        c.writeheader()
        c.writerows(rows)

def import_bonayich_into_topics():
    from sefaria.model.abstract import AbstractMongoRecord
    with open(f"research/knowledge_graph/named_entity_recognition/sperling_named_entities.json", "r") as fin:
        j = json.load(fin)
    tds_json = {
        "slug": "sperling-bonayich",
        "displayName": {
            "en": "Bonyaich via Michael Sperling",
            "he": "Bonyaich via Michael Sperling"
        }
    }
    tds = TopicDataSource().load({"slug": tds_json['slug']})
    if tds is None:
        TopicDataSource(tds_json).save()
    for r in tqdm(j):
        en_prime = None
        he_prime = None
        titles = list({f"{t['text']}|{t['lang']}": t for t in r['manualTitles']}.values())

        for title in titles:
            if title['lang'] == 'en' and en_prime is None:
                en_prime = title['text']
                title['primary'] = True
            if title['lang'] == 'he' and he_prime is None:
                he_prime = title['text']
                title['primary'] = True
        
        slug = en_prime if en_prime is not None else he_prime
        if slug is None:
            print("SLUG IS NONE", r)
        topic_json = {
            "slug": AbstractMongoRecord.normalize_slug(slug),
            "titles": titles
        }
        try:
            bid = int(r['id'].replace('BONAYICH:', ''))
            topic_json['alt_ids'] = { "bonayich": bid }
        except ValueError:
            print("BAD ID", r['id'])
            pass
        type_is_guess = False
        try:
            assert r['type'] in {'תנא', 'אמורא', 'בדור תנאים', 'בדור אמוראים'}, r
        except AssertionError:
            # print("GUESSING AMORA", r)
            type_is_guess = True
            r['type'] = 'אמורא' 
        type_symbol = "T" if 'תנא' in r['type'] else 'A'
        if 'gen' in r and r['gen'] is not None and len(r['gen']) > 0:
            try:
                r['gen'] = re.sub('[אב]', '', r['gen'])
                gens = re.split('[\-/]', r['gen'])
                gen_list = []
                for g in gens:
                    gen_list += [f"{type_symbol}{int(g)}"]
                symbol = "/".join(gen_list)

                try:
                    assert TimePeriod().load({"symbol": symbol}) is not None, r
                    topic_json['properties'] = { "generation": { "value": symbol, "dataSource": tds_json['slug']}}
                except AssertionError:
                    print("BAD GEN SYMBOL", symbol, r)
            except ValueError:
                print("BAD GEN NUM", r)
        # doesn't work...
        # t = Topic(topic_json)
        # t = Topic.init(t.normalize_slug_field('slug'))
        # if t is not None:
        #     t.delete()

        t = Topic(topic_json)
        t.save()

        if r['tag'] == 'NORP':
            toTopic = "group-of-mishnaic-people" if type_symbol == "T" else "group-of-talmudic-people"
            print(t.slug)
        else:
            toTopic = "mishnaic-people" if type_symbol == "T" else "talmudic-people"
        link_json = {
            "class": "intraTopic",
            "fromTopic": t.slug,
            "toTopic": toTopic,
            "linkType": "is-a",
            "dataSource": tds_json['slug']
        }
        if type_is_guess:
            link_json['generatedBy'] = "import_bonayich_into_topics. may not be amora."
        itl = IntraTopicLink().load(link_json)
        if itl is not None:
            itl.delete()
        itl = IntraTopicLink(link_json)
        itl.save()

def import_rabi_rav_rabbis_into_topics():
    from research.knowledge_graph.named_entity_recognition.ner_tagger import TextNormalizer
    from sefaria.utils.hebrew import is_hebrew
    with open("/home/nss/sefaria/datasets/ner/sefaria/new_rabbis.json", "r") as fin:
        j = json.load(fin)
    TopicSet({'alt_ids.rav_rabi': {"$exists": True}}).delete()
    for _, d in j.items():
        d['alt_ids'] = {"rav_rabi": True}
        typ = d['type']
        del d['type']
        t = Topic(d)
        t.save()
        toTopic = "mishnaic-people" if typ == "tanna" else "talmudic-people"
        link_json = {
            "class": "intraTopic",
            "fromTopic": t.slug,
            "toTopic": toTopic,
            "linkType": "is-a",
            "dataSource": "sperling-bonayich"
        }
        itl = IntraTopicLink(link_json)
        itl.save()

    with open(f"/home/nss/sefaria/datasets/ner/sefaria/Fix Rabi and Rav Errors - rav_rabbi_errors.csv", "r") as fin:
        c = csv.DictReader(fin)
        rows = list(c)
    for row in rows:
        typ = row['Error Type (rabbi, title, mistake, correct)']
        is_heb = is_hebrew(row['Snippet'])

        if typ == 'title':
            slug_list = [row['Missing Title Slug']]
            other_slugs = row['Additional Missing Title Slugs']
            if len(other_slugs) > 0:
                slug_list += other_slugs.split(', ')
            topic_list = [Topic.init(slug) for slug in slug_list]
            for t, s in zip(topic_list, slug_list):
                if not t:
                    print("NO TOPIC", s)
                    continue
                has_title = False
                for tit in t.titles:
                    if tit['text'] == row['Missing Title']:
                        has_title = True
                        break
                if has_title:
                    continue
                t.add_title(row['Missing Title'], 'he' if is_heb else 'en')
                t.save()

def add_ambiguous_topics():
    from sefaria.utils.hebrew import is_hebrew
    TopicSet({"isAmbiguous": True}).delete()
    IntraTopicLinkSet({"generatedBy": "add_ambiguous_topics"}).delete()
    with open("/home/nss/sefaria/datasets/ner/sefaria/ner_output_talmud.json", "r") as fin:
        j = json.load(fin)
    unique_ambiguities = defaultdict(set)
    for m in j:
        if len(m['id_matches']) < 2:
            continue
        unique_ambiguities[tuple(m['id_matches'])].add(m['mention'])
    out = []
    for k, v in unique_ambiguities.items():
        titles = [{
            "text": title,
            "lang": "he" if is_hebrew(title) else "en"
        } for title in sorted(v, key=lambda x: len(x))]
        primary_langs_found = set()
        for title in titles:
            if title['lang'] not in primary_langs_found:
                title['primary'] = True
                primary_langs_found.add(title['lang'])

        topic = Topic({
            "slug": f"{titles[0]['text']}-(ambiguous)",
            "titles": titles,
            "isAmbiguous": True,
            "shouldDisplay": False
        })
        topic.save()
        for other_slug in k:
            itl = IntraTopicLink({
                "fromTopic": other_slug,
                "toTopic": topic.slug,
                "linkType": "possibility-for",
                "dataSource": "sefaria",
                "generatedBy": "add_ambiguous_topics",
            })
            itl.save()

        out += [{
            "ids": list(k),
            "titles": list(v)
        }]
    slug2bid = {}
    with open("/home/nss/sefaria/datasets/ner/michael-sperling/Match Bonayich Rabbis with Sefaria Rabbis - Sefaria Rabbis Matched.csv", "r") as fin:
        c = csv.DictReader(fin)
        for row in c:
            slug2bid[row['Slug']] = row['Bonayich ID']
    for item in out:
        item["bids"] = [slug2bid.get(slug, '') for slug in item['ids']]
    # out = list(filter(lambda x: len(set(x['bids'])) > 1, out))
    with open("/home/nss/sefaria/datasets/ner/sefaria/ambiguous_rabbis.json", "w") as fout:
        json.dump(out, fout, ensure_ascii=False, indent=2)

def deduplicate_new_rabbis_rav_nataf():
    same_as_dict = defaultdict(dict)
    with open("/home/nss/sefaria/datasets/ner/sefaria/Fix Rabi and Rav Errors - Current Known Rabbis.csv", "r") as fin:
        c = csv.DictReader(fin)
        for row in c:
            if len(row["Same as Slug"]) == 0:
                continue
            slug1, slug2 = row['Slug'], row['Same as Slug']
            slug1, slug2 = (slug1, slug2) if slug1 > slug2 else (slug2, slug1)
            if slug2 in same_as_dict:
                slug1, slug2 = slug2, slug1
            same_as_dict[slug1][slug1] = (row['Is Judgment Call?'] == 'y')
            same_as_dict[slug1][slug2] = (row['Is Judgment Call?'] == 'y')
    out = {}
    for _, v in same_as_dict.items():
        rabbis = list(sorted(v.keys(), key=lambda x: len(x), reverse=True))
        topics = [Topic.init(r) for r in rabbis]
        # look for longest name that is in Sefaria
        main_rabbi = rabbis[0]
        other_rabbis = rabbis[1:]
        for i, (r, t) in enumerate(zip(rabbis, topics)):
            if t is not None and getattr(t, 'alt_ids', {}).get('bonayich', None) is None:
                # Sefaria rabbi
                main_rabbi = r
                other_rabbis = rabbis[:i] + rabbis[i+1:]
        for other_rabbi in other_rabbis:
            out[other_rabbi] = main_rabbi
    with open('/home/nss/sefaria/datasets/ner/sefaria/swap_rabbis.json', 'w') as fout:
        json.dump(out, fout, ensure_ascii=True, indent=2)
        

"""
one slug/mention per line. only choose one mention in each language
also add basic info on topic (en, he, description, link)
also some examples of them being referred to that way (it will be ambiguous, so how helpful is this?)
"""
if __name__ == "__main__":
    # convert_final_en_names_to_csv()
    # find_ambiguous_rabbis()
    # check_rabbi_yehuda_hanasi()
    convert_final_en_names_to_ner_tagger_input()
    # create_csv_for_rav_nataf()
    # import_bonayich_into_topics()
    # import_rabi_rav_rabbis_into_topics()
    # add_ambiguous_topics()
    # deduplicate_new_rabbis_rav_nataf()