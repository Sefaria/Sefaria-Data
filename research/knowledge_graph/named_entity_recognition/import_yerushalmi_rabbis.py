import django, re, csv, json
from tqdm import tqdm
django.setup()
from sefaria.model import *
from collections import defaultdict

# ROOT = "data"
# SPERLING = "data"
# NER = "data"
# TEMP = "data"

ROOT = "/home/nss/Downloads"
SPERLING = "/home/nss/sefaria/datasets/ner/michael-sperling"
NER = "/home/nss/sefaria/data/research/knowledge_graph/named_entity_recognition"
TEMP = "/home/nss/sefaria/datasets/ner/sefaria/temp"

en_file = "Yerushalmi People Deduplication - English Titles.csv"  # contains mapping of English titles to existing and Bonayich people
he_file = "Yerushalmi People Deduplication - Hebrew Titles.csv"  # contains Hebrew titles for new topics
existing_he_file = "Yerushalmi People Deduplication - New Titles for Existing Topics.csv"  # contains Hebrew titles for existing topics

def modify_existing_topics():
    slug_title_map = defaultdict(list)
    with open(f"{ROOT}/{en_file}", "r") as fin:
        cin = csv.DictReader(fin)
        for row in cin:
            if len(row['En Title']) == 0: continue
            slug = row['Slug or Bonayich ID']
            refs_as_data = row['Use Refs as Data?'] == 'y'
            if refs_as_data: continue
            if 'BONAYICH' in slug: continue
            if len(slug) == 0: continue
            slug_title_map[slug] += [{
                "text": row['En Title'].strip(),
                "lang": "en"
            }]
    with open(f"{ROOT}/{existing_he_file}", "r") as fin:
        cin = csv.DictReader(fin)
        for row in cin:
            slug = row['Rabbi']
            if len(slug) == 0: continue
            for i in range(1, 4):
                temp_he = row[f'He {i}'].strip()
                if len(temp_he) == 0: continue
                slug_title_map[slug] += [{
                    "text": temp_he,
                    "lang": "he"
                }]
    # temp
    out = {k: list(v) for k, v in slug_title_map.items()}
    with open(f"{ROOT}/new_topic_titles.json", "w") as fout:
        json.dump(out, fout, ensure_ascii=False, indent=2)
    for slug, titles in slug_title_map.items():
        topic = Topic.init(slug)
        if topic is None:
            print("NONE", slug)
            continue
        for title in titles:
            topic.add_title(title['text'], title['lang'])
        topic.save()

def get_manual_yerushalmi_corrections():
    corrections = []
    mentions_by_text = defaultdict(list)
    with open("/home/nss/sefaria/datasets/ner/sefaria/ner_output_yerushalmi.json", "r") as fin:
        mentions = json.load(fin)
        for m in mentions:
            mentions_by_text[m['mention']] += [m]

    with open(f"{ROOT}/{en_file}", "r") as fin:
        cin = csv.DictReader(fin)
        for row in cin:
            if len(row['En Title']) == 0: continue
            slug = row['Slug or Bonayich ID']
            refs_as_data = row['Use Refs as Data?'] == 'y'
            if not refs_as_data: continue
            refs = []
            for i in range(1, 6):
                temp_ref = row[f'Ref {i}'].replace('JTmock', 'Jerusalem Talmud')
                if len(temp_ref) == 0: continue
                refs += [temp_ref]
            full_temp_mentions = mentions_by_text[row['En Title']]
            temp_mentions = list(filter(lambda x: x['ref'] in refs, full_temp_mentions))
            try:
                assert len(temp_mentions) == len(refs)
            except AssertionError:
                if len(full_temp_mentions) == 0: continue
                print(f"{len(temp_mentions)} {len(refs)} {len(full_temp_mentions)} {row['En Title']} {slug} {full_temp_mentions[0]['mention']}")
            corrections += [{
                "start": m['start'],
                "end": m['end'],
                "versionTitle": m['versionTitle'],
                "language": m['language'],
                "ref": m['ref'],
                "mention": m['mention'],
                "correctionType": "mistake" if len(slug) == 0 else "manualIds",
                "id_matches": [slug] if len(slug) > 0 else None
            } for m in temp_mentions]
        with open('/home/nss/sefaria/data/research/knowledge_graph/named_entity_recognition/manual_corrections_yerushalmi.json', 'w') as fout:
            json.dump(corrections, fout, ensure_ascii=False, indent=2)

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
    with open(f"{ROOT}/{en_file}", "r") as fin:
        cin = csv.DictReader(fin)
        for row in cin:
            if len(row['En Title']) == 0: continue
            slug = row['Slug or Bonayich ID']
            if 'BONAYICH' not in slug: continue
            refs_as_data = row['Use Refs as Data?'] == 'y'
            if refs_as_data: continue
            if len(slug) == 0: continue
            bid = int(slug.replace('BONAYICH:', ''))
            bids_to_import.add(bid)
            bid_en_title_map[bid].add(row['En Title'].strip())

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
    PersonTopicSet({"properties.bonayich.value": "true"}).delete()
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
        topic.set_property('bonayich', 'true', 'sefaria')
        topic.set_slug_to_primary_title()
        topic.save()

        # ontology link
        IntraTopicLink({
            "fromTopic": topic.slug,
            "toTopic": "mishnaic-people" if rtype == 'T' else "talmudic-people",
            "dataSource": "sefaria",
            "linkType": "is-a",
            "generatedBy": "yerushalmi-rabbi-import"
        }).save()
    with open(f"{ROOT}/new_bonayich_topics.json", "w") as fout:
        json.dump(out, fout, ensure_ascii=False, indent=2)


def add_new_topics():
    out = []
    PersonTopicSet({"properties.dedup_needed.value": "true"}).delete()
    with open(f"{ROOT}/{he_file}", "r") as fin:
        cin = csv.DictReader(fin)
        for row in cin:
            if len(row['En Title']) == 0: continue
            ptype = row['Person Type']
            titles = [
                {
                    "lang": "en",
                    "text": row['En Title']
                }
            ] + [
                {
                    "lang": "he",
                    "text": row[f'He Title {i}']
                } for i in range(1, 5) if len(row[f'He Title {i}']) > 0
            ]
            if len(ptype) == 0:
                # add to manual titles
                out += [{
                    "tag": "PERSON",
                    "id": row['En Title'],
                    "idIsSlug": False,
                    "manualTitles": titles
                }]
            else:
                # create new topic
                topic = PersonTopic({'slug': ''})
                for i, title in enumerate(titles):
                    primary = title['lang'] == 'en' or i == 1
                    topic.add_title(title['text'], title['lang'], primary=primary)
                topic.set_property('dedup_needed', 'true', 'sefaria')
                topic.set_slug_to_primary_title()
                topic.save()

                # ontology link
                toTopic = None
                if ptype == 'tanakh':
                    toTopic = 'biblical-figures'
                elif ptype == 'tanna':
                    toTopic = "mishnaic-people"
                elif ptype == 'amora' or 'not sure if tanna or amora':
                    toTopic = "talmudic-people"
                IntraTopicLink({
                    "fromTopic": topic.slug,
                    "toTopic": toTopic,
                    "dataSource": "sefaria",
                    "linkType": "is-a",
                    "generatedBy": "yerushalmi-rabbi-import"
                }).save()

    with open(f"{TEMP}/yerushalmi_nonexisting_topics.json", "w") as fout:
        json.dump(out, fout, ensure_ascii=True, indent=2)

def find_most_popular_yerushalmi_rabbis():
    with open("/home/nss/sefaria/datasets/ner/sefaria/ner_output_yerushalmi.json", "r") as fin:
        jin = json.load(fin)
    slug_counts = defaultdict(list)
    for mention in jin:
        for slug in mention['id_matches']:
            slug_counts[slug] += [mention['ref']]
    sorted_slug_counts = sorted(slug_counts.items(), key=lambda x: len(x[1]), reverse=True)
    rows = []
    for slug, refs in sorted_slug_counts[:100]:
        topic = Topic.init(slug)
        has_desc = False if topic is None else topic.has_description()
        if not has_desc and topic is not None:
            rows += [{
                "En": topic.get_primary_title('en'),
                "He": topic.get_primary_title('he'),
                "Slug": topic.slug,
                "Link": f"https://sefaria.org/topics/{slug}"
            }]
            for i in range(1, 6):
                rows[-1][f'Ref {i}'] = refs[i-1]
    with open("/home/nss/sefaria/datasets/ner/sefaria/temp/yerushalmi_topics_no_description.csv", "w") as fout:
        cout = csv.DictWriter(fout, ['Slug', 'En', 'He', 'Link'] + [f'Ref {i}' for i in range(1, 6)])
        cout.writeheader()
        cout.writerows(rows)

def add_ys_to_bonayich_sheet():
    bids_to_add_y = set()
    with open(f"{ROOT}/{en_file}", "r") as fin:
        cin = csv.DictReader(fin)
        for row in cin:
            if 'BONAYICH' in row['Slug or Bonayich ID']:
                bids_to_add_y.add(row['Slug or Bonayich ID'].replace('BONAYICH:', ''))

    new_sperling_en_and_he = []
    with open(f"{SPERLING}/sperling_en_and_he.csv", "r") as fin:
        cin = csv.DictReader(fin)
        for row in cin:
            if row['Bonayich ID'] in bids_to_add_y:
                row['Exists in DB'] = 'y'
                print(row['Bonayich ID'])
            new_sperling_en_and_he += [row]
    with open(f"{SPERLING}/sperling_en_and_he2.csv", "w") as fout:
        cout = csv.DictWriter(fout, cin.fieldnames)
        cout.writeheader()
        cout.writerows(new_sperling_en_and_he)

if __name__ == '__main__':
    # IntraTopicLinkSet({"generatedBy": "yerushalmi-rabbi-import"}).delete()
    # import_bonayich_rabbis()  # must go first to create new topics
    # modify_existing_topics()
    # add_new_topics()
    # find_most_popular_yerushalmi_rabbis()
    # get_manual_yerushalmi_corrections()
    add_ys_to_bonayich_sheet()