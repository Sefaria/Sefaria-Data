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

def get_mas(mas, vtitle='William Davidson Edition - Aramaic'):
    i = library.get_index(mas)
    trefs = [r.normal() for r in i.all_segment_refs()]
    tc = Ref(mas).text(lang='he', vtitle=vtitle)
    text = tc.ja().flatten_to_array()
    return zip(trefs, text), tc.version().versionTitle
    
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

def get_rabbi_char_loc_list(context_list, seg_text, norm_regex=None, repl=None, **match_text_kwargs):
    orig_seg_text = seg_text
    if norm_regex is not None:
        seg_text = re.sub(norm_regex, repl, seg_text)
    matches = match_text(seg_text.split(), [context.replace('~', '') for context in context_list], with_num_abbrevs=False, place_all=True, place_consecutively=True, verbose=False, max_overlap_percent=1.1, **match_text_kwargs)
    rabbi_span_list = []
    for match_span, matched_text, context in zip(matches["matches"], matches["match_text"], context_list):
        rabbi_span_list += [get_rabbi_char_loc(match_span, matched_text, context, seg_text, orig_seg_text, norm_regex, repl)]
    return rabbi_span_list

def get_rabbi_char_loc(match_span, matched_text, context, seg_text, orig_seg_text, norm_regex, repl):
    from data_utilities.util import get_mapping_after_normalization, convert_normalized_indices_to_unnormalized_indices
    from research.knowledge_graph.named_entity_recognition.ner_tagger import TextNormalizer
    if match_span[0] == -1:
        return None, None
    matched = matched_text[0]
    pre_rabbi, rabbi, _ = context.split('~')
    context_start = list(re.finditer(r'\S+', seg_text))[match_span[0]].start()
    if matched != context.replace('~', ''):
        # cant assume rabbi_start_rel is same as it was in `context`
        word_b4_rabbi = pre_rabbi.split()[-1] + ' ' if len(pre_rabbi.strip()) > 0 else ''
        rabbi_matches = match_text(matched.split(), [word_b4_rabbi + rabbi], with_num_abbrevs=False, place_all=True, place_consecutively=True, verbose=False)
        rabbi_matched = rabbi_matches["match_text"][0][0]
        if rabbi_matched == '':
            return None, None
        rcount = matched.count(rabbi_matched)
        if rcount > 1:
            print("TON_O_RABANAN")
            return None, None
        rabbi_start_rel = matched.find(rabbi_matched)
        if len(word_b4_rabbi) > 0 and rabbi_matched.startswith(word_b4_rabbi):
            # first word is not part of rabbi abbreviation (unlike א"ר where first word should be considered part of the rabbi)
            # wait until now to remove word_b4_rabbi to reduce the rabbi's ambiguity in matched
            rabbi_matched = rabbi_matched[len(word_b4_rabbi):]
            rabbi_start_rel += len(word_b4_rabbi)
        rabbi_len = len(rabbi_matched)
    else:
        rabbi_start_rel = context.find('~')
        rabbi_len = len(rabbi)
    start = context_start + rabbi_start_rel
    end = start + rabbi_len
    if norm_regex is not None:
        def find_text_to_remove(s):
            return [(m, repl) for m in re.finditer(norm_regex, s)]
        norm_map = get_mapping_after_normalization(orig_seg_text, find_text_to_remove)
        mention_indices = convert_normalized_indices_to_unnormalized_indices([(start, end)], norm_map)
        start, end = TextNormalizer.include_trailing_nikkud(mention_indices[0], orig_seg_text)
    return start, end

def convert_to_spacy_format(rabbi_mentions, vtitle='William Davidson Edition - Aramaic', norm_regex=None, repl=None, **match_text_kwargs):
    by_book = defaultdict(lambda: defaultdict(list))
    for row in rabbi_mentions:
        by_book[row["Book"]][row["Segment"]] += [row]
    spacy_formatted = []
    new_rabbi_mentions = []
    found_set = set()
    for book, segs in tqdm(by_book.items()):
        book_data, book_vtitle = get_mas(book, vtitle)
        for tref, text in book_data:
            rabbi_contexts = [r["Context"] for r in segs[tref]]
            row = {"text": text, "ents": []}
            rabbi_spans = get_rabbi_char_loc_list(rabbi_contexts, text, norm_regex, repl, **match_text_kwargs)
            for icontext, (start, end) in enumerate(rabbi_spans):
                if start == None:
                    continue
                row["ents"] += [{"start": start, "end": end, "label": "PERSON"}]
                found_key = f"{tref}|{start}|{end}"
                if found_key in found_set:
                    print("Already found", found_key, text[start:end])
                    continue
                found_set.add(found_key)
                new_rabbi_mentions += [{
                    "Book": book,
                    "Ref": tref,
                    "Bonayich ID": segs[tref][icontext]["Bonayich ID"],
                    "Start": start,
                    "End": end,
                    "Mention": text[start:end],
                    "Version Title": book_vtitle,
                    "Language": "he"
                }]
            spacy_formatted += [row]
    return spacy_formatted, new_rabbi_mentions

def display_displacy(jsonl_loc):
    jsonl_data = list(filter(lambda x: len(x['text']) > 0, srsly.read_jsonl(jsonl_loc)))
    spacy.displacy.serve(jsonl_data, style='ent', manual=True)

def convert_to_mentions_file(he_mentions_file, output_file, only_bonayich_rabbis=True):
    import json
    from sefaria.utils.hebrew import is_hebrew
    from research.knowledge_graph.named_entity_recognition.ner_tagger import Mention

    manual_sef_id_map = defaultdict(set)
    with open(f"{DATA_LOC}/Match Bonayich Rabbis with Sefaria Rabbis - Sefaria Rabbis Matched.csv", "r") as fin:
        c = csv.DictReader(fin)
        for row in c:
            try:
                manual_sef_id_map[int(row["Bonayich ID"])].add(row["Slug"])
            except ValueError:
                continue
    db_sef_id_map = defaultdict(set)
    topic_set = TopicSet({"alt_ids.bonayich": {"$exists": True}})
    for t in topic_set:
        db_sef_id_map[int(t.alt_ids['bonayich'])].add(t.slug)

    ids_not_in_sefaria_db = set()
    with open(f"{DATA_LOC}/sperling_en_and_he.csv", "r") as fin:
        c = csv.DictReader(fin)
        for row in c:
            if row['Exists in DB'] == 'y':
                continue
            en1 = row["En 1"].strip()
            if len(en1) == 0 or en1 == "N/A" or en1 == "MM":
                continue
            try:
                bid = int(row['Bonayich ID'])
                ids_not_in_sefaria_db.add(bid)
            except ValueError:
                continue
    print("NUM DB IDS", len(db_sef_id_map))
    unique_missed = {}
    new_mentions = set()
    for mention in srsly.read_jsonl(he_mentions_file):
        if int(mention['Bonayich ID']) not in ids_not_in_sefaria_db and only_bonayich_rabbis:
            # already exists in sefaria db. we can skip
            continue
        slug_set = manual_sef_id_map.get(int(mention['Bonayich ID']), None)
        if slug_set is None:
            slug_set = db_sef_id_map.get(int(mention['Bonayich ID']), None)
        if slug_set is None and False:
            # disabling this if b/c we want mentions that dont appear in db
            # these are 'missing' mostly because they're false positives in michael's results
            unique_missed[mention['Bonayich ID']] = mention['Mention']
            continue
        if slug_set is not None and only_bonayich_rabbis:
            # ignore any bids that match sefaria slugs 
            continue
        new_mentions.add(Mention().add_metadata(**{
            "start": mention["Start"],
            "end": mention["End"],
            "mention": mention["Mention"],
            "ref": mention["Ref"],
            "id_matches": [f"BONAYICH:{mention['Bonayich ID']}"] if slug_set is None else list(slug_set),
            "versionTitle": mention["Version Title"],
            "language": mention["Language"]
        }))
    new_new_mentions = []
    for mention in new_mentions:
        new_new_mentions += [{
            "start": mention.start,
            "end": mention.end,
            "mention": mention.mention,
            "ref": mention.ref,
            "id_matches": mention.id_matches,
            "versionTitle": mention.versionTitle,
            "language": mention.language
        }]
    if False:
        # skipping since we already have these mentions fixed in db
        # modify mentions based on manual corrections
        with open(f"{DATA_LOC}/../sefaria/Fix Rabi and Rav Errors - rav_rabbi_errors.csv", "r") as fin:
            c = csv.DictReader(fin)
            rows = list(c)
        to_delete = defaultdict(list)
        to_modify = defaultdict(list)
        for row in rows:
            typ = row['Error Type (rabbi, title, mistake, correct)']
            is_heb = is_hebrew(row['Snippet'])
            if not is_heb:
                continue
            mention = row['Snippet'].split('~')[1]
            key = f"{row['Ref']}|{mention}"
            if typ == 'mistake':
                to_delete[key] += [row]
            elif typ == 'title' or typ == 'rabbi':
                to_modify[key] += [row]
        def delete_mistakes(mention):
            key = f"{mention['ref']}|{mention['mention']}"
            to_keep = key not in to_delete
            if not to_keep and len(to_delete[key]) == 0:
                pass
                # print("ALREADY USED but seems right anyway to delete", mention)
            elif not to_keep:
                to_delete[key].pop()
            return to_keep
        print("BEFORE DELETE", len(new_new_mentions))
        new_new_mentions = list(filter(delete_mistakes, new_new_mentions))
        print("AFTER DELETE", len(new_new_mentions))
        for mention in new_new_mentions:
            key = f"{mention['ref']}|{mention['mention']}"
            if key not in to_modify:
                continue
            row = to_modify[key][0]
            typ = row['Error Type (rabbi, title, mistake, correct)']

            new_mention = row['Missing Title'].strip() if typ == 'title' else row['Missing Rabbi Hebrew'].strip()
            try:
                index = new_mention.index(mention['mention'])
            except ValueError:
                prefixes = ['ו', 'מד', 'כ', 'ד', 'ול', 'ל']
                prefixes.sort(key=lambda x: len(x), reverse=True)
                prefixed_mention = None
                for p in prefixes:
                    if mention['mention'].startswith(p):
                        prefixed_mention = mention['mention'][len(p):]
                        break
                if prefixed_mention is None:
                    print("Couldn't find prefix", mention['mention'], new_mention)
                    continue
                try:
                    index = new_mention.index(prefixed_mention)
                except ValueError:
                    print("Couldn't find after prefix", prefixed_mention, new_mention)
                    continue
            new_start = mention['start'] - index
            new_end = new_start + len(new_mention)
            mention['start'] = new_start
            mention['end'] = new_end
            mention['mention'] = new_mention
            if typ == "title":
                new_id_matches = [row['Missing Title Slug']]
                more_id_matches_str = row['Additional Missing Title Slugs']
                if len(more_id_matches_str) > 0:
                    new_id_matches += more_id_matches_str.split(', ')
                assert all([Topic.init(slug) is not None for slug in new_id_matches])
            elif typ == "rabbi":
                topics = TopicSet({"titles.text": {"$all": [row['Missing Rabbi Hebrew'].strip(), row['Missing Rabbi English'].strip()]}})
                if topics.count() > 1:
                    for t in topics:
                        print("POSSIBLE RABBI", t.slug)
                    continue
                elif topics.count() == 0:
                    print("NO NEW RABBI", row)
                    continue
                new_id_matches = [topics.array()[0].slug]
            mention['id_matches'] = new_id_matches
            """
            find index of mention['mention'] in Missing Title
            if -1, :shrug:
            else:
                start = old_start - index
                end = start + len(Missing Title)
            """
    with open(f"research/knowledge_graph/named_entity_recognition/{output_file}", "w") as fout:
        json.dump(new_new_mentions, fout, ensure_ascii=False, indent=2)
    print("NUM MISSED", len(unique_missed))
    print("NUM GOT", len(new_new_mentions))
    # for k, v in unique_missed.items():
    #     print(k, v)

def convert_mentions_for_alt_version(nikkud_vtitle, mentions_output, manual_changes_file=None, limit=None):
    import json
    from research.knowledge_graph.named_entity_recognition.ner_tagger import Mention
    from data_utilities.dibur_hamatchil_matcher import match_text
    from data_utilities.util import get_mapping_after_normalization, convert_normalized_indices_to_unnormalized_indices
    if manual_changes_file is not None:
        changes = srsly.read_json(manual_changes_file)
    with open("research/knowledge_graph/named_entity_recognition/sperling_mentions.json", "r") as fin:
        j = json.load(fin)
    # add mentions in db b/c sperling_mentions only includes bonayich-only mentions
    for tl in RefTopicLinkSet({"class": "refTopic", "linkType": "mention", "charLevelData.versionTitle": "William Davidson Edition - Aramaic"}):
        j += [{
            "start": tl.charLevelData['startChar'],
            "end": tl.charLevelData['endChar'],
            "ref": tl.ref,
            "mention": tl.charLevelData['text'],
            "id_matches": [tl.toTopic]
        }]
    mentions_by_seg = defaultdict(list)
    print("TOTAL MENTIONS", len(j))
    for mention in j:
        mentions_by_seg[mention['ref']] += [Mention().add_metadata(**mention)]
    indexes = library.get_indexes_in_category("Bavli") if limit is None else limit

    def get_norm_pos(start, end, s):
        num_to_remove = s.count(':', 0, start)
        return start - num_to_remove, end - num_to_remove
    replace_reg_parens = r"(?:[\u0591-\u05bd\u05bf-\u05c5\u05c7,.:!?״()]+|\s—|\s…)"
    replace_reg = r"(?:[\u0591-\u05bd\u05bf-\u05c5\u05c7,.:!?״]+|\s—|\s…)"
    def get_find_text_to_remove(remove_parens=True):
        return lambda s: [(m, '') for m in re.finditer(replace_reg_parens if remove_parens else replace_reg, s)]

    new_mentions = []
    num_failed = 0
    for mas in tqdm(indexes):
        if Version().load({"title": mas, "versionTitle": nikkud_vtitle, "language": "he"}) is None:
            continue
        index = library.get_index(mas)
        for seg in index.all_segment_refs():
            temp_mentions = mentions_by_seg[seg.normal()]
            if len(temp_mentions) == 0:
                continue
            text = TextChunk(seg, lang='he', vtitle='William Davidson Edition - Aramaic').text
            norm_text = re.sub(':', '', text)
            text_nikkud = TextChunk(seg, lang='he', vtitle=nikkud_vtitle).text
            remove_parens = True
            if re.sub(replace_reg_parens, '', text_nikkud) != text:
                remove_parens = False
            norm_text_nikkud = re.sub(replace_reg_parens if remove_parens else replace_reg, '', text_nikkud)

            if len(text_nikkud) == 0:
                continue
            mention_indices = [get_norm_pos(mention.start, mention.end, text) for mention in temp_mentions]
            if manual_changes_file is None:
                norm_map = get_mapping_after_normalization(text_nikkud, find_text_to_remove=get_find_text_to_remove(remove_parens))
            else:
                temp_wiki_changes = changes.get(seg.normal(), {}).get('wiki', [])

                temp_will_changes = changes.get(seg.normal(), {}).get('will', [])
                temp_wiki_changes = list(filter(lambda x: x not in temp_will_changes, temp_wiki_changes))
                temp_wiki_changes.sort(key=lambda x: x[0][0])
                for tc in temp_wiki_changes:
                    tc[0][0] += 1
                    tc[0][1] += 1
                norm_map = get_mapping_after_normalization(text_nikkud, removal_list=temp_wiki_changes)
  
            mention_indices = convert_normalized_indices_to_unnormalized_indices(mention_indices, norm_map)
            temp_new_mentions = []
            for mention, (unnorm_start, unnorm_end) in zip(temp_mentions, mention_indices):
                if manual_changes_file is None:
                    new_mention = re.sub(replace_reg_parens if remove_parens else replace_reg, '', text_nikkud[unnorm_start:unnorm_end])
                else:
                    new_mention = text_nikkud[unnorm_start:unnorm_end]
                try:
                    if len(new_mention) == 0:
                        print("ZERO LENGTH MENTION", mention.mention, seg.normal())
                    assert len(new_mention) > 0
                    if manual_changes_file is None:
                        assert new_mention == mention.mention, f"'{new_mention} != {mention.mention}' {unnorm_start} {unnorm_end}"
                    else:
                        for offset in [0, -1, 1, -2, 2]:
                            new_mention = text_nikkud[unnorm_start+offset:unnorm_end+offset]
                            # likely to be abbreviations in new_mention. use dh matcher to see if they're 'equivalent'
                            old_mention_comparison = mention.mention
                            if new_mention.startswith('א"ר'):
                                old_mention_comparison = "אמר " + old_mention_comparison
                            if new_mention.startswith('"'):
                                # middle of abbrev
                                new_mention_comparison = new_mention[1:2] + "'" + new_mention[2:]
                            else:
                                new_mention_comparison = new_mention
                            new_words = new_mention_comparison.split()
                            matched = match_text(new_words, [old_mention_comparison], with_abbrev_matches=True, daf_skips=0, rashi_skips=0, overall=0)
                            if matched['matches'][0][0] != -1:
                                # need look at actual match and figure out if any words are missing
                                # recalculate unnorm_start and unnorm_end to leave out these words. Test case: Arakhin 5a:18
                                istart_word, iend_word = matched['matches'][0]
                                start_text = " ".join(new_words[:istart_word])
                                start_offset = len(start_text) + (1 if len(start_text) > 0 else 0)  # add 1 to account for space right after start_text
                                end_text = " ".join(new_words[iend_word+1:])
                                end_offset = len(end_text) + (1 if len(end_text) > 0 else 0)
                                unnorm_start += offset + start_offset
                                unnorm_end += offset - end_offset
                                break
                        # move unnorm_start and end to nearest word break
                        if unnorm_end == len(text_nikkud) + 1:
                            # one too big
                            unnorm_end -= 1
                        if unnorm_end > len(text_nikkud):
                            # too big give up
                            # print("UPDATE END TOO BIG. GIVE UP...", mention.mention, seg.normal())
                            assert False
                        if text_nikkud[unnorm_start] in {' ', ':'}:
                            # move forward by one
                            unnorm_start += 1
                        if text_nikkud[unnorm_end-1] in {' ', ':'}:
                            unnorm_end -= 1
                        start_nearest_break = max(text_nikkud.rfind(' ', 0, unnorm_start), text_nikkud.rfind(':', 0, unnorm_start))
                        end_nearest_break_match = re.search(r'[\s:]', text_nikkud[unnorm_end:])
                        end_nearest_break = (end_nearest_break_match.start() + unnorm_end) if end_nearest_break_match is not None else -1
                        if start_nearest_break != -1:
                            unnorm_start = start_nearest_break + 1
                        elif unnorm_start != 0:
                            # if couldn't find space before, must be at beginning
                            # print("UPDATE START", mention.mention, seg.normal())
                            unnorm_start = 0
                        if end_nearest_break != -1:
                            unnorm_end = end_nearest_break
                        elif unnorm_end != len(text_nikkud):
                            # print("UPDATE END", mention.mention, seg.normal())
                            unnorm_end = len(text_nikkud)
                        assert matched['matches'][0][0] != -1
                    mention.add_metadata(start=unnorm_start, end=unnorm_end, mention=text_nikkud[unnorm_start:unnorm_end])
                    temp_new_mentions += [mention]
                except AssertionError:
                    norm_start, norm_end = get_norm_pos(mention.start, mention.end, text)
                    snip_size = 10
                    start_snip_naive = norm_start - snip_size if norm_start >= snip_size else 0
                    start_snip = norm_text.rfind(" ", 0, start_snip_naive)
                    if start_snip == -1:
                        start_snip = start_snip_naive
                    end_snip_naive = norm_end + snip_size if norm_end + snip_size <= len(norm_text) else len(norm_text)
                    end_snip = norm_text.find(" ", end_snip_naive)
                    if end_snip == -1:
                        end_snip = end_snip_naive
                    snippet = f"{norm_text[start_snip:norm_start]}~{norm_text[norm_start:norm_end]}~{norm_text[norm_end:end_snip]}"

                    new_norm_start, new_norm_end = get_rabbi_char_loc(snippet, norm_text_nikkud)
                    if new_norm_start is None:
                        # print("new_norm_start is None")
                        num_failed += 1
                        continue
                    new_start, new_end = convert_normalized_indices_to_unnormalized_indices([(new_norm_start, new_norm_end)], norm_map)[0]
                    new_mention = re.sub(replace_reg_parens if remove_parens else replace_reg, '', text_nikkud[new_start:new_end])
                    try:
                        assert new_mention == mention.mention, f"'{new_mention} != {mention.mention}' {unnorm_start} {unnorm_end}"
                        mention.add_metadata(start=new_start, end=new_end, mention=text_nikkud[new_start:new_end])
                        temp_new_mentions += [mention]
                    except AssertionError:
                        num_failed += 1
                    # get_rabbi_char_pos using context and text_nikkud
                    # get_unnormalized pos
            new_mentions += temp_new_mentions
    out = [m.serialize(delete_keys=['versionTitle', 'language']) for m in new_mentions]
    with open(f"research/knowledge_graph/named_entity_recognition/{mentions_output}", "w") as fout:
        json.dump(out, fout, ensure_ascii=False, indent=2)
    print("NUM FAILED", num_failed)

def make_new_alt_titles_file():
    import json
    from sefaria.utils.hebrew import is_hebrew
    from research.knowledge_graph.named_entity_recognition.ner_tagger import Mention

    manual_sef_id_map = defaultdict(set)
    with open(f"{DATA_LOC}/Match Bonayich Rabbis with Sefaria Rabbis - Sefaria Rabbis Matched.csv", "r") as fin:
        c = csv.DictReader(fin)
        for row in c:
            try:
                manual_sef_id_map[int(row["Bonayich ID"])].add(row["Slug"])
            except ValueError:
                continue

    slug2titles = defaultdict(set)
    with open(f"{DATA_LOC}/sperling_en_and_he.csv", "r") as fin:
        c = csv.DictReader(fin)
        for row in c:
            try:
                bid = int(row["Bonayich ID"])
            except ValueError:
                print(row)
                continue
            slugs = manual_sef_id_map[bid]
            titles = set()
            for i in range(1,4):
                title = row[f'En {i}'].strip()
                if len(title) == 0 or title == "N/A" or title == "MM":
                    break
                titles.add(title)
            for slug in slugs:
                slug2titles[slug] |= titles
    out = {}
    for k, v in slug2titles.items():
        out[k] = list(v)
    with open(f"/home/nss/sefaria/datasets/ner/sefaria/new_alt_titles.json", "w") as fout:
        json.dump(out, fout, ensure_ascii=False, indent=2)

def convert_mishnah_and_tosefta_to_mentions(tractate_prefix, in_file, out_file1, out_file2, vtitle, title_map=None):
    import json
    title_map = title_map or {}
    mentions = []
    crude_mentions = []
    issues = 0
    with open(in_file, "r") as fin:
        c = csv.DictReader(fin)
        for row in c:
            row["Tractate"] = title_map.get(row["Tractate"], row["Tractate"])
            tref = f'{row["Tractate"]} {row["Chapter"]}:{row["Number"]}'
            if not row['Tractate'].startswith('Pirkei Avot'):
                tref = tractate_prefix + tref
            oref = Ref(tref)
            context = row["Context"]
            crude_mentions += [{
                "Book": oref.index.title,
                "Segment": oref.normal(),
                "Bonayich ID": row["rabbi_id"],
                "Context": context
            }]
    print("Issues", issues)

    spacy_formatted, rabbi_mentions = convert_to_spacy_format(crude_mentions, vtitle=vtitle, norm_regex="[\u0591-\u05bd\u05bf-\u05c5\u05c7]+", repl='', daf_skips=0, rashi_skips=0, overall=0)
    srsly.write_jsonl(out_file1, rabbi_mentions)
    convert_to_mentions_file(out_file1, out_file2, only_bonayich_rabbis=False)
    with open(f'research/knowledge_graph/named_entity_recognition/{out_file2}', 'r') as fin:
        j = json.load(fin)
    with open(f'{DATA_LOC}/../sefaria/{out_file2}', 'w') as fout:
        json.dump(j, fout, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    # rows_by_mas = get_rows_by_mas()
    # rabbi_mentions = get_rabbi_mention_segments(rows_by_mas)
    # spacy_formatted, rabbi_mentions = convert_to_spacy_format(rabbi_mentions)
    # srsly.write_jsonl(f'{DATA_LOC}/he_mentions.jsonl', rabbi_mentions)
    # srsly.write_jsonl(f'{DATA_LOC}/he_training.jsonl', spacy_formatted)
    # display_displacy(f"{DATA_LOC}/he_training.jsonl")
    
    # convert_to_mentions_file(f"{DATA_LOC}/he_mentions.jsonl", "sperling_mentions.json", only_bonayich_rabbis=True)
    # convert_mentions_for_alt_version('William Davidson Edition - Vocalized Aramaic', 'sperling_mentions_nikkud.json')
    # convert_mentions_for_alt_version('William Davidson Edition - Vocalized Punctuated Aramaic', 'sperling_mentions_nikkud_punctuated.json')
    # convert_mentions_for_alt_version("Wikisource Talmud Bavli", 'sperling_mentions_wikisource.json', '/home/nss/sefaria/datasets/ner/sefaria/wiki_will_changes.json')
    
    convert_mishnah_and_tosefta_to_mentions("Mishnah ", f"{DATA_LOC}/mishna_names.csv", f'{DATA_LOC}/he_mentions_mishnah.jsonl', "sperling_mentions_mishnah.json", "Torat Emet 357")
    # convert_mishnah_and_tosefta_to_mentions("Tosefta ", f"{DATA_LOC}/tosefta_names.csv", f'{DATA_LOC}/he_mentions_tosefta.jsonl', "sperling_mentions_tosefta.json", None, {"Oholot": "Ohalot", "Oktzin": "Uktsin", "Rosh Hashanah": "Rosh HaShanah"})
  
    # make_new_alt_titles_file()