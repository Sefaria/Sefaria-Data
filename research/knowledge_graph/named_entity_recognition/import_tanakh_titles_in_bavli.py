import django, re, csv, json
from tqdm import tqdm
django.setup()
from sefaria.model import *
from sefaria.utils.hebrew import is_hebrew
from sefaria.helper.normalization import NormalizerComposer
from collections import defaultdict

# ROOT = "data"
# SPERLING = "data"
# NER = "data"
# TEMP = "data"

ROOT = "/home/nss/Downloads"
SPERLING = "/home/nss/sefaria/datasets/ner/michael-sperling"
NER = "/home/nss/sefaria/data/research/knowledge_graph/named_entity_recognition/external_named_entities"
TEMP = "/home/nss/sefaria/datasets/ner/sefaria/temp"

new_titles = "Manual Corrections for Tanakh Figures in Talmud - Titles.csv"
new_people = "Manual Corrections for Tanakh Figures in Talmud - New People.csv"
manual_corrections = "Manual Corrections for Tanakh Figures in Talmud - Manual Corrections.csv"

normalizer = NormalizerComposer(['unidecode'])
b_replacements = [' ben ', ' bar ', ', son of ', ', the son of ', ' son of ', ' the son of ']

def normalize_title(title):
    title = title.strip()
    title = normalizer.normalize(title)
    for b_repl in b_replacements:
        title = title.replace(b_repl, ' b. ')
    return title

def add_titles():
    with open(f'{ROOT}/{new_titles}', 'r') as fin:
        cin = csv.DictReader(fin)
        for row in cin:
            slug = row['Slug']
            if 'BONAYICH' in slug: continue
            t = Topic.init(slug)
            if t is None:
                print('Slug is None', slug)
                continue
            new_title = normalize_title(row['New title 1'])
            lang = 'he' if is_hebrew(new_title) else 'en'
            t.add_title(new_title, lang)
            t.save()

def import_bonayich_rabbis():
    bid_en_title_map = defaultdict(set)
    bid_he_title_map = defaultdict(set)
    bid_type_map = {}
    with open(f"{SPERLING}/sperling_en_and_he.csv", "r") as fin:
        c = csv.DictReader(fin)
        for row in c:
            if row['Exists in DB'] == 'y':
                continue
            en1 = row["En 1"].strip()
            if len(en1) == 0 or en1 == "N/A" or en1 == "MM" or row['Bonayich ID'] == 'N/A':
                continue
            bid = int(row['Bonayich ID'])
            en_titles = []
            for i in range(6):
                temp_en = row[f'En {i+1}'].strip()
                if len(temp_en) == 0:
                    continue
                en_titles += [temp_en]
            bid_en_title_map[bid] = set(en_titles)
            bid_he_title_map[bid].add(row['He'])
    bids_to_import = set()
    with open(f"{ROOT}/{new_titles}", "r") as fin:
        cin = csv.DictReader(fin)
        for row in cin:
            slug = row['Slug']
            if 'BONAYICH' not in slug: continue
            if len(slug) == 0: continue
            bid = int(slug.replace('BONAYICH:', ''))
            bids_to_import.add(bid)
            new_title = normalize_title(row['New title 1'])
            if is_hebrew(new_title):
                bid_he_title_map[bid].add(new_title)
            else:
                bid_en_title_map[bid].add(new_title)

    # type
    with open(f"{NER}/sperling_named_entities.json", "r") as fin:
        sperling_nes = json.load(fin)
    for r in sperling_nes:
        try:
            bid = int(r['id'].replace('BONAYICH:', ''))
        except ValueError:
            continue
        type_is_guess = False
        try:
            assert r['type'] in {'תנא', 'אמורא', 'בדור תנאים', 'בדור אמוראים'}, r
        except AssertionError:
            # print("GUESSING AMORA", r)
            type_is_guess = True
            r['type'] = 'אמורא'
        bid_type_map[bid] = "T" if 'תנא' in r['type'] else 'A'

    # save
    out = {}
    PersonTopicSet({"properties.bonayich-bavli.value": "true"}).delete()
    for bid, en_titles in bid_en_title_map.items():
        if bid not in bids_to_import: continue
        he_titles = bid_he_title_map[bid]
        rtype = bid_type_map[bid]
        topic = PersonTopic({'slug': ''})
        out[bid] = {
            'en': list(en_titles),
            'he': list(he_titles),
            'type': rtype
        }
        for lang, titles in (('en', en_titles), ('he', he_titles)):
            for ititle, title in enumerate(sorted(titles, key=lambda x: (len(x), x), reverse=True)):
                # arbitrarily decide longest title is primary. fallback on alphabetical order when there are ties
                topic.add_title(title, lang, ititle == 0)
        topic.set_property('bonayich-bavli', 'true', 'sefaria')
        topic.set_slug_to_primary_title()
        topic.save()

        # ontology link
        IntraTopicLink({
            "fromTopic": topic.slug,
            "toTopic": "mishnaic-people" if rtype == 'T' else "talmudic-people",
            "dataSource": "sefaria",
            "linkType": "is-a",
            "generatedBy": "bavli-rabbi-import"
        }).save()
    with open(f"{ROOT}/new_bonayich_topics.json", "w") as fout:
        json.dump(out, fout, ensure_ascii=False, indent=2)

def get_manual_bavli_corrections():
    corrections = []
    mentions_by_text = defaultdict(list)
    with open("/home/nss/sefaria/datasets/ner/sefaria/ner_output_bavli.json", "r") as fin:
        mentions = json.load(fin)
        for m in mentions:
            mentions_by_text[m['mention']] += [m]

    with open(f"{ROOT}/{manual_corrections}", "r") as fin:
        # TODO rewrite
        cin = csv.DictReader(fin)
        for row in cin:
            refs = [row['Ref']]
            full_temp_mentions = mentions_by_text[row['Error']]
            temp_mentions = list(filter(lambda x: x['ref'] in refs, full_temp_mentions))
            # try:
            #     assert len(temp_mentions) == len(refs)
            # except AssertionError:
            #     if len(full_temp_mentions) == 0: continue
            #     print(f"{len(temp_mentions)} {refs[0]} {len(full_temp_mentions)} {row['Error']} {full_temp_mentions[0]['mention']}")
            corrections += [{
                "start": m['start'],
                "end": m['end'],
                "versionTitle": m['versionTitle'],
                "language": m['language'],
                "ref": m['ref'],
                "mention": m['mention'],
                "correctionType": "mistake" if row['Type'] == 'mistake' else "manualIds",
                "id_matches": [row['Replace with']] if row['Type'] == 'replace' else None
            } for m in temp_mentions]
        with open('/home/nss/sefaria/data/research/knowledge_graph/named_entity_recognition/manual_corrections/manual_corrections_bavli2.json', 'w') as fout:
            json.dump(corrections, fout, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    # IntraTopicLinkSet({"generatedBy": "bavli-rabbi-import"}).delete()
    # add_titles()
    # import_bonayich_rabbis()
    get_manual_bavli_corrections()