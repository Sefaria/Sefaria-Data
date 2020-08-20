import django, srsly, spacy
import csv, re
django.setup()
from sefaria.model import *
from collections import defaultdict
from data_utilities.dibur_hamatchil_matcher import match_ref, match_text
from tqdm import tqdm

DATA_LOC = "/home/nss/sefaria/datasets/ner/michael-sperling"

full_text = None
def get_mas_text(mas):
    global full_text
    v = Version().load({"title": mas, "versionTitle": "William Davidson Edition - Aramaic"})
    full_text = defaultdict(list)
    def action(s, e, h, v1):
        global full_text
        full_text[e.replace(f"{mas} ", '').split(":")[0]] += [s]
    v.walk_thru_contents(action)
    return full_text

def get_start_seg(sentances, search_space):
    start_seg = None
    prev_start_seg = 0
    count = 0
    while count < 10:
        if count > 0:
            print("Retry")

        for i, tempseg in enumerate(search_space[prev_start_seg:]):
            if sentances[0] in tempseg:
                prev_start_char = tempseg.index(sentances[0])
                start_seg = i
                break
        if start_seg is None:
            break
        count += 1
        has_extrance_sentances = True
        for j, extra_sentance in enumerate(sentances[1:]):
            if extra_sentance not in search_space[start_seg+1+j]:
                prev_start_seg = start_seg+1
                start_seg = None
                has_extrance_sentances = False
                break
        if has_extrance_sentances:
            # break free!!!!
            break
    return start_seg

def get_snippet_seg(snippet, amud, amud_prev):
    has_amud_break = re.search(r'  \[\d+[AB]\]  ', snippet) is not None
    search_space = amud[:]
    if has_amud_break:
        search_space = amud_prev + search_space
        snippet = re.sub(r'  \[\d+[AB]\]', '', snippet)
    sentances = snippet.split(".  ")
    rabbi_loc = 0
    for i, sent in enumerate(sentances):
        if '~' in sent:
            rabbi_loc = i
        sentances[i] = sent.replace('~', '')
    start_seg = get_start_seg(sentances, search_space)
    rabbi_seg = start_seg + rabbi_loc
    if has_amud_break and rabbi_seg >= len(amud_prev):
        rabbi_seg -= len(amud_prev)
    return rabbi_seg
    
def next_amud(curr_amud):
    letter = curr_amud[-1]
    daf = int(curr_amud[:-1])
    if letter == "a":
        return f"{daf}b"
    return f"{daf+1}a"

def prev_amud(curr_amud):
    letter = curr_amud[-1]
    daf = int(curr_amud[:-1])
    if letter == "b":
        return f"{daf}a"
    return f"{daf-1}b"

def dh_extract_method(s):
    s = re.sub(r'^.+  \[\d+[AB]\]  ', '', s)
    return s.replace('~', '').replace('.', '')
def base_tokenizer(s):
    return s.split()

def get_rabbi_seg(match_seg, snippet):
    if match_seg is None:
        return None, None
    snippet = re.sub(r'^.+  \[\d+[AB]\]  ', '', snippet)
    sentances = list(filter(lambda x: len(x.strip()) > 0, snippet.split(".  ")))
    rabbi_loc = 0
    context = None
    for k, sent in enumerate(sentances):
        if '~' in sent:
            rabbi_loc = k
            context = sent
    if not match_seg.is_range():
        return match_seg, context
    try:
        return match_seg.range_list()[rabbi_loc], context
    except IndexError:
        print("INDEXERROR")
        for s in sentances:
            print(s)
        print("RABBI LOC", rabbi_loc)
        print("REF", match_seg.normal())
        return None, None

def get_mas(mas):
    i = library.get_index(mas)
    trefs = [r.normal() for r in i.all_segment_refs()]
    text = Ref(mas).text(lang='he', vtitle='William Davidson Edition - Aramaic').ja().flatten_to_array()
    return zip(trefs, text)
    
def get_rabbi_mention_segments(rows_by_mas, limit=None):
    total = 0
    missed = 0
    new_rows = []

    indexes = library.get_indexes_in_category("Bavli") if limit is None else limit
    for mas in tqdm(indexes):
        for i, amud in enumerate(rows_by_mas[mas]):
            curr_amud = amud[0][' Amud'].lower()
            tc = Ref(f"{mas} {curr_amud}").text("he", vtitle="William Davidson Edition - Aramaic")
            matches = match_ref(tc, [r[' Snippet'] for r in amud], base_tokenizer, dh_extract_method=dh_extract_method, with_num_abbrevs=False, place_all=True, place_consecutively=True, verbose=False)
            total+=len(matches['matches'])
            rabbi_match_segs = []
            seg_char_locs = []
            for j, m in enumerate(matches['matches']):
                snippet = amud[j][' Snippet']
                rabbi_match_segs += [get_rabbi_seg(m, snippet)]
                if m is None:
                    missed += 1

            for j, r in enumerate(amud):
                seg, context = rabbi_match_segs[j]
                new_rows += [{
                    "Segment": None if seg is None else seg.normal(),
                    "Context": context,
                    "Book": mas,
                    "Bonayich ID": r[" Rabbi ID after Link"]
                }]
    print(missed, total)
    return new_rows

def get_rows_by_mas():
    rows_by_mas = defaultdict(list)
    with open(f"{DATA_LOC}/AllNameReferences.csv", "r") as fin:
        c = csv.DictReader(fin)
        for r in c:
            rows_by_mas[r[' Masechet']] += [r]
    for k, v in rows_by_mas.items():
        for r in v:
            r['Start'] = int(r[' Begin Offset'])
            r['End'] = int(r[' End Offset'])
            r['Rabbi'] = r[' Snippet'].split('~')[1]
        mas_rows = sorted(v, key=lambda x: x['Start'])
        amud =  []
        amudim = []
        for i, r in enumerate(mas_rows):
            amud += [r]
            if i == len(mas_rows) - 1 or mas_rows[i+1][' Amud'] != r[' Amud']:
                amudim += [amud]
                amud = []
        rows_by_mas[k] = amudim
    return rows_by_mas

def get_rabbi_char_loc(context, seg_text):
    matches = match_text(seg_text.split(), [context.replace('~', '')], with_num_abbrevs=False, place_all=True, place_consecutively=True, verbose=False)
    if matches["matches"][0][0] == -1:
        return None, None
    matched = matches["match_text"][0][0]
    count = seg_text.count(matched)
    if count == 0:
        return None, None
    if count > 1:
        # print(f"Context\n{context}\nappears {count} times!")
        return None, None
    rabbi = context.split('~')[1]
    rabbi_len = len(rabbi)
    context_start = seg_text.find(matched)
    if matched != context.replace('~', ''):
        # cant assume rabbi_start_rel is same as it was in `context`
        rcount = matched.count(rabbi)
        if rcount == 0:
            print("NO_RABBI")
            return None, None
        if rcount > 1:
            print("TON_O_RABANAN")
            return None, None
        rabbi_start_rel = matched.find(rabbi)
    else:
        rabbi_start_rel = context.find('~')
    start = context_start + rabbi_start_rel
    end = start + rabbi_len
    return start, end

def convert_to_spacy_format(rabbi_mentions):
    by_book = defaultdict(lambda: defaultdict(list))
    for row in rabbi_mentions:
        by_book[row["Book"]][row["Segment"]] += [row]
    spacy_formatted = []
    new_rabbi_mentions = []
    for book, segs in tqdm(by_book.items()):
        book_data = get_mas(book)
        for tref, text in book_data:
            rabbi_contexts = [r["Context"] for r in segs[tref]]
            row = {"text": text, "ents": []}
            for icontext, context in enumerate(rabbi_contexts):
                start, end = get_rabbi_char_loc(context, text)
                if start == None:
                    continue
                row["ents"] += [{"start": start, "end": end, "label": "PERSON"}]
                new_rabbi_mentions += [{
                    "Book": book,
                    "Ref": tref,
                    "Bonayich ID": segs[tref][icontext]["Bonayich ID"],
                    "Start": start,
                    "End": end,
                    "Mention": text[start:end]
                }]
            spacy_formatted += [row]
    return spacy_formatted, new_rabbi_mentions

def display_displacy(jsonl_loc):
    jsonl_data = list(filter(lambda x: len(x['text']) > 0, srsly.read_jsonl(jsonl_loc)))
    spacy.displacy.serve(jsonl_data, style='ent', manual=True)

def convert_to_mentions_file():
    import json

    sef_id_map = {}
    with open("research/knowledge_graph/named_entity_recognition/sefaria_bonayich_reconciliation - Sheet2.csv", "r") as fin:
        c = csv.DictReader(fin)
        for row in c:
            try:
                sef_id_map[int(row["bonayich"])] = row["Slug"]
            except ValueError:
                continue

    new_mentions = []
    for mention in srsly.read_jsonl(f"{DATA_LOC}/he_mentions.jsonl"):
        slug = sef_id_map.get(int(mention['Bonayich ID']), None)
        new_mentions += [{
            "start": mention["Start"],
            "end": mention["End"],
            "mention": mention["Mention"],
            "ref": mention["Ref"],
            "id_matches": [f"BONAYICH:{mention['Bonayich ID']}" if slug is None else slug]
        }]
    with open("research/knowledge_graph/named_entity_recognition/sperling_mentions.json", "w") as fout:
        json.dump(new_mentions, fout, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    # rows_by_mas = get_rows_by_mas()
    # rabbi_mentions = get_rabbi_mention_segments(rows_by_mas)
    # spacy_formatted, rabbi_mentions = convert_to_spacy_format(rabbi_mentions)
    # srsly.write_jsonl(f'{DATA_LOC}/he_mentions.jsonl', rabbi_mentions)
    # srsly.write_jsonl(f'{DATA_LOC}/he_training.jsonl', spacy_formatted)
    # display_displacy(f"{DATA_LOC}/he_training.jsonl")
    
    convert_to_mentions_file()