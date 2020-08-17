import django, re, json, csv
django.setup()
from collections import defaultdict
from tqdm import tqdm
from sefaria.model import *
from sefaria.utils.hebrew import strip_cantillation
# How to get all people in Tanakh
# query to get all lexicon_entries for people: {parent_lexicon: "BDB Augmented Strong", $or: [{"content.morphology": "n-pr-m"}, {"content.morphology": "n-pr-f"}]}
# query to get all word_forms for prev result {"lookups.parent_lexicon": "BDB Augmented Strong", "lookups.headword": <HEADWORD>}
# this gives me all the refs with this person (could be ambiguous)

def generate_mentions_by_ref():
    les = LexiconEntrySet({"parent_lexicon": "BDB Augmented Strong", "content.morphology": re.compile("n-pr(-[mf])?")})
    num_missing = 0
    num_found = 0
    found_mentions = 0
    missed_mentions = 0
    total_mentions = 0
    wfs = WordFormSet({"lookups.parent_lexicon": "BDB Augmented Strong", "language_code": "x-pn"})
    wf_by_hw = defaultdict(list)
    for wf in wfs:
        for lookup in wf.lookups:
            if ('־' in lookup['headword'] and '־' not in wf.form) or (' ' in lookup['headword'] and ' ' not in wf.form):
                print("SKIPPING", lookup['headword'], wf.form)
                continue
            total_mentions += len(wf.refs)
            wf_by_hw[lookup['headword']] += [wf]
    tanakh_topics = Topic.init("biblical-figures").topics_by_link_type_recursively(only_leaves=True)
    tanakh_names = defaultdict(list)
    for topic in tanakh_topics:
        for title in topic.get_titles(with_disambiguation=False, lang='he'):
            tanakh_names[strip_cantillation(title, strip_vowels=True)] += [topic]
    for k, v in tanakh_names.items():
        v_dict = {t.slug: t for t in v}  # make unique by slug
        tanakh_names[k] = sorted(v_dict.values(), key=lambda x: getattr(x, 'numSources', 0), reverse=True)

    matches_by_ref = defaultdict(list)
    for le in tqdm(les, total=les.count()):
        head = le.headword
        temp_topics = tanakh_names[strip_cantillation(head, strip_vowels=True)]
        temp_wfs = wf_by_hw[head]
        if len(temp_topics) == 0:
            continue
        for temp_wf in temp_wfs:
            entry = {
                "Form": temp_wf.form,
                "Topics": " ".join(t.slug for t in temp_topics)
            }
            for ref in temp_wf.refs:
                matches_by_ref[ref] += [entry]

        if len(temp_topics) == 0:
            num_missing +=1
        else:
            num_found += 1

    with open("research/knowledge_graph/named_entity_recognition/tanakh_mentions.json", "w") as fout:
        json.dump(matches_by_ref, fout, ensure_ascii=False, indent=2)


def create_html():
    tanakh_topics = {t.slug: t for t in Topic.init("biblical-figures").topics_by_link_type_recursively(only_leaves=True)}

    with open("research/knowledge_graph/named_entity_recognition/tanakh_mentions.json", "r") as fin:
        mentions_by_ref = json.load(fin)
    text_by_ref = {}
    all_refs = []
    for index in library.get_indexes_in_category("Tanakh", full_records=True)[:5]:
        he = Ref(index.title).text("he").text
        en = Ref(index.title).text("en", vtitle="Metsudah Chumash, Metsudah Publications, 2009").text
        all_refs += [r.normal() for r in index.all_segment_refs()]
        for iperek, perek in enumerate(he):
            for ipasuk, he_pasuk in enumerate(perek):
                ref = f"{index.title} {iperek+1}:{ipasuk+1}"
                en_pasuk = en[iperek][ipasuk]
                text_by_ref[ref] = {"he": he_pasuk, "en": en_pasuk}

    html = """
    <html>
        <head>
            <style>
                body {
                    width: 700px;
                    margin-right: auto;
                    margin-bottom: 50px;
                    margin-top: 50px;
                    margin-left: auto;
                }
                .he {
                    direction: rtl;
                }
                .missing {
                    color: red;
                }
                .found {
                    color: green;
                }
            </style>
        </head>
        <body>
    """
    missing_html = html[:]
    he_found = 0
    en_found = 0
    missing_rows = 0
    for ref in all_refs:
        mentions = mentions_by_ref.get(ref, [])
        mentions.sort(key=lambda x: len(x['Form']), reverse=True)
        mentions = {m["Topics"]: m for m in mentions}.values()
        try:
            text = text_by_ref[ref]
        except KeyError:
            print("No", ref)
        he_text = strip_cantillation(text['he'])
        en_text = text['en']
        for mention in mentions:
            if len(mention["Form"]) == 0:
                continue
            if strip_cantillation(mention["Form"],strip_vowels=True) == 'אל':
                # hard-coded because of silly dictionary bug
                continue
            topics = mention["Topics"].split()
            disambiguated_topic = topics[0]  # TODO actually disambiguate
            titles = sorted(tanakh_topics[disambiguated_topic].get_titles(lang='en', with_disambiguation=False), key=lambda x: len(x), reverse=True)
            en_text = re.sub(fr'(?<!/)({"|".join(titles)})(?=[\s,.:;"\'’”()\[\]!?—\-<]|$)', fr'<a href="https://www.sefaria.org/topics/{disambiguated_topic}">\1</a>', en_text)
            he_text = re.sub(fr'(?<!>)({mention["Form"]})', fr'<a href="https://www.sefaria.org/topics/{disambiguated_topic}">\1</a>', he_text)
        he_found += he_text.count('<a ')
        en_found += en_text.count('<a ')

        row = f'''
        <p>{ref}</p>
        <p class="he">{he_text}</p>
        <p>{en_text}</p>
        '''
        if he_text.count('<a ') > en_text.count('<a '):
            missing_rows += 1
            missing_html += row
        html += row
    html += """
        </body>
    </html>
    """
    missing_html += """
        </body>
    </html>
    """
    print("HE", he_found)
    print("EN", en_found)
    print("MISSING", missing_rows)
    with open("research/knowledge_graph/named_entity_recognition/tanakh.html", "w") as fout:
        fout.write(html)
    with open("research/knowledge_graph/named_entity_recognition/tanakh_missing.html", "w") as fout:
        fout.write(missing_html)
if __name__ == "__main__":
    generate_mentions_by_ref()
    create_html()