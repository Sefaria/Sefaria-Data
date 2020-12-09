import django, re, json, csv
django.setup()
from collections import defaultdict
from tqdm import tqdm
from sefaria.model import *
from sefaria.utils.hebrew import strip_cantillation
from data_utilities.util import get_mapping_after_normalization, convert_normalized_indices_to_unnormalized_indices
from research.knowledge_graph.named_entity_recognition.ner_tagger import CorpusManager
import unicodedata
# How to get all people in Tanakh
# query to get all lexicon_entries for people: {parent_lexicon: "BDB Augmented Strong", $or: [{"content.morphology": "n-pr-m"}, {"content.morphology": "n-pr-f"}]}
# query to get all word_forms for prev result {"lookups.parent_lexicon": "BDB Augmented Strong", "lookups.headword": <HEADWORD>}
# this gives me all the refs with this person (could be ambiguous)

def filter_wfs_to_lookup(hw, wfs):
    return filter(lambda wf: hw in {lookup['headword'] for lookup in wf.lookups}, wfs)

def filter_refs(hw, refs, wfs_by_ref):
    expected_len = len(re.split(r'[\s־]', hw))
    matched_refs = []
    matched_forms = []
    for ref in refs:
        wfs = wfs_by_ref[ref]
        wfs_for_hw = {wf.form: wf for wf in filter_wfs_to_lookup(hw, wfs)}
        if len(wfs_for_hw) < expected_len:
            continue
        he = strip_cantillation(Ref(ref).text("he").text)
        words = re.split(r'\s*(?:\s|׀|־|׃)\s*', he)
        curr_form = []        
        for word in words:
            wf = wfs_for_hw.get(word, False)            
            if wf:
                curr_form += [word]
            else:
                if len(curr_form) == expected_len:
                    matched_refs += [ref]
                    matched_forms += [" ".join(curr_form)]
                curr_form = []
        if len(curr_form) == expected_len:
            matched_refs += [ref]
            matched_forms += [" ".join(curr_form)]
    return matched_refs, matched_forms

def generate_mentions_by_ref():
    extra_lexicon_entries = [
        {"headword" : "פַּרְעֹה"}
    ]
    les = LexiconEntrySet({"parent_lexicon": "BDB Augmented Strong", "content.morphology": re.compile("n-pr(-[mf])?")}).array()
    for extra in extra_lexicon_entries:
        extra["parent_lexicon"] = "BDB Augmented Strong"
        le = LexiconEntry().load(extra)
        if le is None:
            print(le, "is None")
            continue
        les += [le]
    num_missing = 0
    num_found = 0
    found_mentions = 0
    missed_mentions = 0
    total_mentions = 0
    wfs = WordFormSet({"lookups.parent_lexicon": "BDB Augmented Strong", "language_code": "x-pn"})
    wfs_by_ref = defaultdict(list)
    for wf in wfs:
        for ref in wf.refs:
            wfs_by_ref[ref] += [wf]
    wf_by_hw = defaultdict(list)
    for wf in tqdm(wfs, total=wfs.count()):
        for lookup in wf.lookups:
            form = wf.form
            refs = wf.refs
            # if ('־' in lookup['headword'] and '־' not in wf.form) or (' ' in lookup['headword'] and ' ' not in wf.form):
            #     refs, forms = filter_refs(lookup['headword'], wf.refs, wfs_by_ref)
            #     if len(forms) == 0:
            #         print("Failed", lookup['headword'], wf.form)
            #         continue
            #     form = forms[0]
                # print("Fixed", lookup['headword'], wf.form)
                # print("New Form", form)
                # print("New Refs", ", ".join(refs))
                # print("---")
            total_mentions += len(wf.refs)
            wf_by_hw[lookup['headword']] += [{"refs": refs, "form": form}]
    ner_file_prefix = "/home/nss/sefaria/datasets/ner/sefaria"
    corpus_manager = CorpusManager(
        "research/knowledge_graph/named_entity_recognition/ner_tagger_input_tanakh.json",
        f"{ner_file_prefix}/ner_output_tanakh.json",
        f"{ner_file_prefix}/html"
    )
    tanakh_topics = corpus_manager.named_entities
    tanakh_names = defaultdict(list)
    for topic in tanakh_topics:
        for title in topic.get_titles(with_disambiguation=False, lang='he'):
            tanakh_names[strip_cantillation(title, strip_vowels=True)] += [topic]
    for k, v in tanakh_names.items():
        v_dict = {t.slug: t for t in v}  # make unique by slug
        tanakh_names[k] = sorted(v_dict.values(), key=lambda x: getattr(x, 'numSources', 0), reverse=True)

    matches_by_ref = defaultdict(list)
    for le in tqdm(les):
        head = le.headword
        temp_topics = tanakh_names[re.sub('־', ' ', strip_cantillation(head, strip_vowels=True))]
        temp_forms = wf_by_hw[head]
        if len(temp_topics) == 0:
            continue
        for temp_form in temp_forms:
            entry = {
                "Form": temp_form['form'],
                "Topics": " ".join(t.slug for t in temp_topics)
            }
            for ref in temp_form['refs']:
                matches_by_ref[ref] += [entry]

        if len(temp_topics) == 0:
            num_missing +=1
        else:
            num_found += 1

    with open("research/knowledge_graph/named_entity_recognition/tanakh_mentions.json", "w") as fout:
        json.dump(matches_by_ref, fout, ensure_ascii=False, indent=2)

normalizing_re = r"[\u0591-\u05af\u05bd\u05bf\u05c0\u05c4\u05c5]+"
def find_text_to_remove(s):
    return [(m, '') for m in re.finditer(normalizing_re, s)]

def add_html_links(mentions, text):
    linked_text = ""
    mentions.sort(key=lambda x: x['start'])
    dummy_char = "$"
    char_list = list(text)
    rabbi_dict = {}
    for m in mentions:
        if m['id_matches'] is None:
            continue
        rabbi_dict[m['start']] = (text[m['start']:m['end']], m['id_matches'][0])
        char_list[m['start']:m['end']] = list(dummy_char*(m['end']-m['start']))
    dummy_text = "".join(char_list)
    
    # assert len(dummy_text) == len(text), f"DUMMY {dummy_text}\nREAL {text}"

    def repl(match):
        try:
            mention, slug = rabbi_dict[match.start()]
        except KeyError:
            print("KEYERROR", match.group())
            return match.group()
        # TODO find better way to determine if slug is in topics collection
        return f"""<a href="https://www.sefaria.org/topics/{slug}" class="{"missing" if ':' in slug else "found"}">{mention}</a>"""
    linked_text = re.sub(r"\$+", repl, dummy_text)
    return linked_text

def create_html():
    tanakh_topics = {t.slug: t for t in Topic.init("biblical-figures").topics_by_link_type_recursively(only_leaves=True)}

    with open("research/knowledge_graph/named_entity_recognition/tanakh_mentions.json", "r") as fin:
        mentions_by_ref = json.load(fin)
    text_by_ref = {}
    all_refs = []
    for index in library.get_indexes_in_category("Tanakh", full_records=True):
        he = Ref(index.title).text("he").text
        en = Ref(index.title).text("en", vtitle="Tanakh: The Holy Scriptures, published by JPS").text
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
    he_mentions = []
    missing_html = html[:]
    he_found = 0
    en_found = 0
    missing_rows = 0

    for ref in all_refs:
        temp_mentions = []
        mentions = mentions_by_ref.get(ref, [])
        mentions.sort(key=lambda x: len(x['Form']), reverse=True)
        mentions = {m["Topics"]: m for m in mentions}.values()
        try:
            text = text_by_ref[ref]
        except KeyError:
            print("No", ref)
        he_text = unicodedata.normalize("NFKC", re.sub('־', ' ', strip_cantillation(text['he'])))
        en_text = text['en']
        for mention in mentions:
            if len(mention["Form"]) == 0:
                continue
            topics = mention["Topics"].split()
            form = unicodedata.normalize("NFKC", re.sub('־', ' ', mention["Form"]))
            if form not in he_text:
                print("Missing form", form, ref)
                continue
            for he_match in re.finditer(fr"(?:^|\s|׀|־|׃)({form})(?:$|\s|׀|־|׃)", he_text):
                temp_mentions += [{
                    "start": he_match.start(1),
                    "end": he_match.end(1),
                    "mention": form,
                    "id_matches": topics,
                    "ref": ref
                }]

            # disambiguated_topic = topics[0]  # TODO actually disambiguate
            # titles = sorted(tanakh_topics[disambiguated_topic].get_titles(lang='en', with_disambiguation=False), key=lambda x: len(x), reverse=True)
            # en_text = re.sub(fr'(?<!/)({"|".join(titles)})(?=[\s,.:;"\'’”()\[\]!?—\-<]|$)', fr'<a href="https://www.sefaria.org/topics/{disambiguated_topic}">\1</a>', en_text)
            # he_text = re.sub(fr'(?<!>)({mention["Form"]})', fr'<a href="https://www.sefaria.org/topics/{disambiguated_topic}">\1</a>', he_text)
        # he_found += he_text.count('<a ')
        # en_found += en_text.count('<a ')
        mention_indices = [(m["start"], m["end"]) for m in temp_mentions]
        norm_map = get_mapping_after_normalization(text['he'], find_text_to_remove)
        mention_indices = convert_normalized_indices_to_unnormalized_indices(mention_indices, norm_map)
        for m, (unnorm_start, unnorm_end) in zip(temp_mentions, mention_indices):
            m["start"] = unnorm_start
            m["end"] = unnorm_end
        he_mentions += temp_mentions
        he_html = add_html_links(temp_mentions, text['he'])
        row = f'''
        <p>{ref}</p>
        <p class="he">{he_html}</p>
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
    with open("research/knowledge_graph/named_entity_recognition/he_tanakh_mentions.json", "w") as fout:
        json.dump(he_mentions, fout, ensure_ascii=False, indent=2)
if __name__ == "__main__":
    generate_mentions_by_ref()
    create_html()