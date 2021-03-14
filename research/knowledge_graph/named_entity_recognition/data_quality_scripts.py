import json, re, csv, srsly, django
from sefaria.utils.hebrew import is_hebrew
django.setup()
from sefaria.model import *

DATASET_LOC = "/home/nss/sefaria/datasets/ner/sefaria"

def make_rav_rabbi_csv():
    out = []
    with open(f"{DATASET_LOC}/cross_validated_by_language.csv", "r") as fin:
        c = csv.DictReader(fin)
        for row in c:
            if row['id'] in {'rabi', 'rav'}:
                out += [{
                    'Slug': row['id'],
                    'Ref': row['example ref'],
                    'Snippet': row['example snippet']
                }]
    with open(f"{DATASET_LOC}/rav_rabbi_errors.csv", "w") as fout:
        c = csv.DictWriter(fout, ['Slug', 'Ref', 'Snippet'])
        c.writeheader()
        c.writerows(out)

def make_levi_shmuel_csv():
    search_set = {'levi-b-sisi', 'shmuel-(amora)'}
    out = []
    with open(f"{DATASET_LOC}/cross_validated_by_language.csv", "r") as fin:
        c = csv.DictReader(fin)
        for row in c:
            rabbi_set = set(row['Rabbi'].split(', '))
            with_rabbi_set = set(row['With Rabbi'].split(', '))
            all_rabbi_set = rabbi_set | with_rabbi_set
            if len(all_rabbi_set & search_set) > 0 :
                if len(all_rabbi_set & search_set) > 1:
                    print("Multiple Found!!", row)
                    continue
                slug = list(all_rabbi_set & search_set)[0]
                out += [{
                    'Slug': slug,
                    'Ref': row['Ref'],
                    'Snippet': row['Rabbi Snippet'],
                    'En': Ref(row['Ref']).text('en').text,
                    'He': Ref(row['Ref']).text('he').text
                }]
    with open(f"{DATASET_LOC}/levi_shmuel_errors.csv", "w") as fout:
        c = csv.DictWriter(fout, ['Slug', 'Ref', 'Snippet', 'En', 'He'])
        c.writeheader()
        c.writerows(out)

def make_csv_of_alt_titles():
    rabbis = Topic.init('talmudic-people').topics_by_link_type_recursively(only_leaves=True) + Topic.init('mishnaic-people').topics_by_link_type_recursively(only_leaves=True)
    rows = []
    max_alt_title = 0
    for rabbi in rabbis:
        row = {
            "Slug": rabbi.slug,
            "Description": getattr(rabbi, "description", {}).get("en", "")
        }
        titles = rabbi.get_titles()
        if len(titles) > max_alt_title:
            max_alt_title = len(titles)
        for ititle, title in enumerate(titles):
            row[f"Title {ititle + 1}"] = title
        rows += [row]
    with open(f"{DATASET_LOC}/rabbi_alt_titles.csv", "w") as fout:
        c = csv.DictWriter(fout, ['Slug', 'Description'] + [f'Title {i}' for i in range(1, max_alt_title+1)])
        c.writeheader()
        c.writerows(rows)

def make_csvs_for_stub_rabbis():
    stubs = {
        "rabbi-ilai": ["rabbi-ilai-(i)", "rabbi-ilai-(ii)"],
        "rav-kahana": ["rav-kahana-(i)", "rav-kahana-(ii)", "rav-kahana-(iii)", "rav-kahana-(iv)", "rav-kahana-(v)"],
        "rav-adda-b-ahavah": ["rav-adda-b-ahavah-(i)", "rav-adda-b-ahavah-(ii)"],
        "rav-hamnuna": ["rav-hamnuna-(i)", "rav-hamnuna-(ii)"],
        "rav-idi-b-avin": ["rav-idi-b-avin-(i)", "rav-idi-b-avin-(ii)"],
        "rabbi-eliezer-b-yaakov": ["rabbi-eliezer-b-yaakov-(i)", "rabbi-eliezer-b-yaakov-(ii)"],
        "rabbi-yehudah-b-betera": ["rabbi-yehudah-b-betera-(i)", "rabbi-yehudah-b-betera-(ii)"],
        "rabban-gamliel": ["rabban-gamliel-hazaken-(i)", "rabban-gamliel-of-yavneh-(ii)", "rabban-gamliel-b-rabbi-(iii)"],
        "rabban-shimon-b-gamliel": ["rabban-shimon-b-gamliel-(i)", "rabban-shimon-b-gamliel-(ii)"],
        "rabbi-elazar-b-tzadok": ["rabbi-elazar-b-tzadok-(i)", "rabbi-elazar-b-tzadok-(ii)"],
        "rabbi-tzadok": ["rabbi-tzadok-(i)", "rabbi-tzadok-(ii)"]
    }
    rows = []
    rows2= []
    max_titles = 0
    for stub, options in stubs.items():
        t = Topic.init(stub)
        for opt in options:
            tt = Topic.init(opt)
            rows2 += [{
                "Slug": tt.slug,
                "Description": getattr(tt, 'description', {}).get('en', ''),
                "Link": f"sefaria.org/topics/{tt.slug}",
            }]
            for i, title in enumerate(tt.get_titles()):
                rows2[-1][f'Title {i+1}'] = title
                if i > max_titles:
                    max_titles = i
        ref_links = t.link_set(_class='refTopic', query_kwargs={"is_sheet": False})
        for rl in ref_links:
            oref = Ref(rl.ref)
            en = re.sub(r"<[^>]+>", " ", oref.text("en").ja().flatten_to_string())
            he = re.sub(r"<[^>]+>", " ", oref.text("he").ja().flatten_to_string())
            rows += [{
                "Stub": stub,
                "Ref": rl.ref,
                "En": en,
                "He": he,
                "Options": f"1-{len(options)}",
                "URL": f"sefaria.org/{oref.url()}"
            }]
    with open(f"{DATASET_LOC}/stub_rabbis.csv", "w") as fout:
        c = csv.DictWriter(fout, ["Stub", "Ref", "En", "He", "Options", "URL"])
        c.writeheader()
        c.writerows(rows)
    with open(f"{DATASET_LOC}/stub_rabbis_info.csv", "w") as fout:
        c = csv.DictWriter(fout, ['Slug', 'Description', 'Link'] + [f'Title {i+1}' for i in range(max_titles+1)])
        c.writeheader()
        c.writerows(rows2)

def check_rabi_rav_results():
    from research.knowledge_graph.named_entity_recognition.ner_tagger import TextNormalizer
    from sefaria.utils.hebrew import is_hebrew

    with open(f"{DATASET_LOC}/Fix Rabi and Rav Errors - rav_rabbi_errors.csv", "r") as fin:
        c = csv.DictReader(fin)
        rows = list(c)
    
    # check titles appear in text
    for row in rows:
        typ = row['Error Type (rabbi, title, mistake, correct)']
        is_heb = is_hebrew(row['Snippet'])
        text = TextNormalizer.normalize_text('he' if is_heb else 'en', row['Snippet'].replace('~', ''))
        if typ == 'title':
            title = row['Missing Title']
        elif typ == 'rabbi':
            title = row[f"Missing Rabbi {'Hebrew' if is_heb else 'English'}"]
        else:
            continue


        title_reg = TextNormalizer.get_rabbi_regex(TextNormalizer.myunidecode(title.strip()))
        m = re.search(title_reg, text)
        if not m:
            if typ == 'rabbi' and len(row['Missing Rabbi Title in Text']) > 0:
                title = row['Missing Rabbi Title in Text']
                title_reg = TextNormalizer.get_rabbi_regex(TextNormalizer.myunidecode(title.strip()))
                m = re.search(title_reg, text)
                if not m:
                    print(f"MISSED '{title}':" , text, row['Ref'])
            else:       
                print(f"MISSED '{title}':" , text, row['Ref'])

def check_new_rabbis_to_create():
    from research.knowledge_graph.named_entity_recognition.ner_tagger import TextNormalizer
    from sefaria.utils.hebrew import is_hebrew
    with open(f"{DATASET_LOC}/Fix Rabi and Rav Errors - rav_rabbi_errors.csv", "r") as fin:
        c = csv.DictReader(fin)
        rows = list(c)

    new_rabbis = {}
    for row in rows:
        typ = row['Error Type (rabbi, title, mistake, correct)']
        is_heb = is_hebrew(row['Snippet'])
        if typ == "rabbi":
            en = TextNormalizer.myunidecode(row["Missing Rabbi English"].strip())
            he = TextNormalizer.myunidecode(row["Missing Rabbi Hebrew"].strip())
            titles = [{
                "text": en,
                "primary": True,
                "lang": "en"
            },
            {
                "text": he,
                "primary": True,
                "lang": "he"
            }
            ]
            if len(en) == 0:
                print("WARNING:", en, he)

            if len(row['Missing Rabbi Title in Text']) > 0:
                alt_title = TextNormalizer.myunidecode(row['Missing Rabbi Title in Text'].strip())
                titles += [{
                    "text": alt_title,
                    "lang": "he" if is_hebrew(alt_title) else "en"
                }]

            key = f"{en}|{he}"
            if key in new_rabbis:
                other_titles = new_rabbis[key]['titles']
                for ot in other_titles:
                    exists = False
                    for t in titles:
                        if t['lang'] == ot['lang'] and t['text'] == ot['text']:
                            exists = True
                            break
                    if not exists:                        
                        titles += [ot]
            if len(row['Missing Rabbi Type (tanna, amora)']) == 0:
                print('NO RABBI TYPE', row)
            topic = {
                "slug": en,
                "titles": titles,
                "type": row['Missing Rabbi Type (tanna, amora)']
            }
            new_rabbis[key] = topic
    with open(f"{DATASET_LOC}/new_rabbis.json", "w") as fout:
        json.dump(new_rabbis, fout, ensure_ascii=False, indent=2)
    rows = []
    max_titles = 0
    for k, v in new_rabbis.items():
        row = {
            "Type": v["type"]
        }          
        if len(v['titles']) > max_titles:
            max_titles = len(v['titles'])
        for i, t in enumerate(v['titles']):
            row[f"Title {i+1}"] = t['text']
        rows += [row]
    with open(f"{DATASET_LOC}/new_rabbis.csv", "w") as fout:
        c = csv.DictWriter(fout, ['Type'] + [f"Title {i+1}" for i in range(max_titles)])
        c.writeheader()
        c.writerows(rows)

def get_number_of_rabbis_in_perek(book, perek):
    index = library.get_index(book)
    perek_tref = index.alt_structs['Chapters']['nodes'][perek]['wholeRef']
    oref = Ref(perek_tref)
    segment_set = {r.normal() for r in oref.all_segment_refs()}
    with open(f'{DATASET_LOC}/ner_output_talmud.json', 'r') as fin:
        j = json.load(fin)
    
    temp_mentions = []
    for m in j:
        if m['ref'] in segment_set and m['versionTitle'] == 'William Davidson Edition - Aramaic':
            temp_mentions += [m]
    temp_mentions.sort(key=lambda x: Ref(x['ref']).order_id())
    with open(f'{DATASET_LOC}/{book} Perek {perek + 1} Mentions.json', 'w') as fout:
        json.dump(temp_mentions, fout, ensure_ascii=False, indent=2)
    print(len(temp_mentions))

def fix_stub_rabbis():
    # all deleted except rabban-gamliel and rabban-shimon-b-gamliel
    stubs = {
        "rabbi-ilai": ["rabbi-ilai-(i)", "rabbi-ilai-(ii)"],
        "rav-kahana": ["rav-kahana-(i)", "rav-kahana-(ii)", "rav-kahana-(iii)", "rav-kahana-(iv)", "rav-kahana-(v)"],
        "rav-adda-b-ahavah": ["rav-adda-b-ahavah-(i)", "rav-adda-b-ahavah-(ii)"],
        "rav-hamnuna": ["rav-hamnuna-(i)", "rav-hamnuna-(ii)"],
        "rav-idi-b-avin": ["rav-idi-b-avin-(i)", "rav-idi-b-avin-(ii)"],
        "rabbi-eliezer-b-yaakov": ["rabbi-eliezer-b-yaakov-(i)", "rabbi-eliezer-b-yaakov-(ii)"],  # weirdness
        "rabbi-yehudah-b-betera": ["rabbi-yehudah-b-betera-(i)", "rabbi-yehudah-b-betera-(ii)"],  # weirdness
        "rabban-gamliel": ["rabban-gamliel-hazaken-(i)", "rabban-gamliel-of-yavneh-(ii)", "rabban-gamliel-b-rabbi-(iii)"],  # lots of sheets
        "rabban-shimon-b-gamliel": ["rabban-shimon-b-gamliel-(i)", "rabban-shimon-b-gamliel-(ii)"],  # 4 sheets
        "rabbi-elazar-b-tzadok": ["rabbi-elazar-b-tzadok-(i)", "rabbi-elazar-b-tzadok-(ii)"],  
        "rabbi-tzadok": ["rabbi-tzadok-(i)", "rabbi-tzadok-(ii)"]  # has description
    }
    with open("data/Fix Stub Rabbis - stub_rabbis.csv", "r") as fin:
        c = csv.DictReader(fin)
        for row in c:
            choice = int(row["Choice"]) if len(row["Choice"]) > 0 else None
            judgement = len(row["Is Judgement Call?"]) > 0
            delete = len(row["Should Delete?"]) > 0
            ls = RefTopicLinkSet({"toTopic": row["Stub"], "ref": row["Ref"]})
            if delete:
                print("Deleting", row["Stub"], row["Ref"])
                ls.delete()
            elif choice is None:
                print("No choice", row["Stub"], row["Ref"])
                continue
            else:
                replacement = stubs[row["Stub"]][choice-1]
                # print("Replace", row["Stub"], replacement, row["Ref"], judgement)
                for l in ls:
                    l.toTopic = replacement
                    if judgement:
                        l.isJudgementCall = True
                    l.save()

def how_much_is_coming_from_bonayich():
    bon_rabbis = TopicSet({"alt_ids.bonayich": {"$exists": True}})
    print(bon_rabbis.count())
    bon_set = {t.slug for t in bon_rabbis}
    with open(f"{DATASET_LOC}/ner_output_talmud.json", "r") as fin:
        j = json.load(fin)
    bon_count = 0
    total = 0
    for m in j:
        if m['versionTitle'] != 'William Davidson Edition - Aramaic':
            continue
        total += 1
        if len(set(m['id_matches']) & bon_set) > 0:    
            bon_count += 1
    print(bon_count)
    print(total)
    print(bon_count/total)

def remove_gen_data():
    ts = TopicSet()
    count = 0
    for t in ts:
        if getattr(t, 'alt_ids', {}).get('bonayich', None) is None:
            continue
        if getattr(t, 'properties', {}).get('generation', None) is None:
            continue
        count += 1
        # print('Delete gen', t.slug, t.get_property('generation'), t.alt_ids['bonayich'])
        del t.properties['generation']
        t.save()
    print(count)

def base_tokenizer(base_str, comp_stri):
    import bleach

    base_str = bleach.clean(base_str, tags=[], strip=True)
    for match in re.finditer(r'[({\[].*?[\])}]', base_str):
        if library.get_titles_in_string(match.group()) and len(match.group().split()) <= 5:
            base_str = base_str.replace(match.group(), "")
            # base_str = re.sub(r"(?:\(.*?\)|<.*?>)", "", base_str)
    nice_goy = 'עובד כוכבים'
    repl = get_goy_repl(base_str, comp_stri)
    if repl is not None:
        base_str = base_str.replace(nice_goy, repl)
    word_list = re.split(r"\s+", base_str)
    word_list = [re.sub(r":", "", w) for w in word_list if w]  # remove empty strings
    return word_list


def base_tokenizer_removed_indices(stri, comp_stri):
    import bisect
    from functools import reduce
    filter_reg_html = r"<[^>]+>"
    filter_reg_paren = r"[({\[].*?[\])}]"
    regs = [filter_reg_html, filter_reg_paren]
    repl = get_goy_repl(stri, comp_stri)
    if repl is not None:
        regs += [r'עובד']
    match_spans = []
    match_text = []

    for ireg, reg in enumerate(regs):
        lookahead = r'(?=\s|$)' if ireg < 2 else r'(?= כוכבים\s|$)'
        filter_iter = re.finditer(r"(?<=\s){}{}|^{}{}".format(reg, lookahead, reg, lookahead), stri)
        match_spans.append([m.span(0) for m in filter_iter])
        filter_iter = re.finditer(r"(?<=\s){}{}|^{}{}".format(reg, lookahead, reg, lookahead), stri)
        match_text.append([m.group() for m in filter_iter])

    match_spans[1] = list(filter(
        lambda x: library.get_titles_in_string(match_text[1][x[0]]) and len(match_text[1][x[0]].split()) <= 5,
        enumerate(match_spans[1])))
    match_text[1] = list(filter(
        lambda x: library.get_titles_in_string(x) and len(x.split()) <= 5,
        match_text[1]))
    match_spans[1] = [ms[1] for ms in match_spans[1]] #remove enumerate
    match_spans = reduce(lambda a, b: a + b, match_spans, [])
    match_text = reduce(lambda a, b: a + b, match_text, [])
    match_word_counts = [len(re.split(r'\s+',s)) for s in match_text]

    match_spans_original = []
    for reg in regs:
        filter_iter_original = re.finditer(reg, stri)
        match_spans_original += [m.span(0) for m in filter_iter_original]

    match_spans = filter(lambda x: x in match_spans_original, match_spans)

    word_iter = re.finditer(r"\s+", stri)
    word_spans = [m.start(0) for m in word_iter]
    word_removed_indices = [bisect.bisect_right(word_spans, span[0]) for span in match_spans]
    word_removed_indices = reduce(lambda a, b: a + [b - len(a)], word_removed_indices, [])

    #add multiples for multiple words removed in a row
    real_word_removed_indices = []
    for iwri,wri in enumerate(word_removed_indices):
        num_skipped_words_passed = sum(match_word_counts[:iwri]) - iwri
        real_word_removed_indices += ([wri - num_skipped_words_passed]*match_word_counts[iwri])
    # also add all locations of double spaces
    naive_split = re.split(r'\s', stri)
    for i, w in enumerate(naive_split):
        if len(w) == 0:
            # double space here
            insert_index = bisect.bisect_right(real_word_removed_indices, i)
            real_word_removed_indices += [i-insert_index]
            real_word_removed_indices.sort()
    real_word_removed_indices.sort()
    return real_word_removed_indices

def base_tokenizer_removed_chars(stri, comp_stri):
    import bisect
    from functools import reduce
    filter_reg_html = r"(\s*)<[^>]+>(\s*)"
    filter_reg_paren = r"(\s*)[({\[].*?[\])}](\s*)"
    regs = [filter_reg_html, filter_reg_paren]
    match_spans = []
    match_text = []

    for reg in regs:
        filter_iter = re.finditer(reg, stri)
        match_spans.append([(m.span(0), ' ' if (len(m.group(1) + m.group(2)) > 0 and m.span(0)[0] > 0) else '') for m in filter_iter])
        filter_iter = re.finditer(reg, stri)
        match_text.append([m.group() for m in filter_iter])

    match_spans[1] = list(filter(
        lambda x: library.get_titles_in_string(match_text[1][x[0]]) and len(match_text[1][x[0]].split()) <= 5,
        enumerate(match_spans[1])))
    match_text[1] = list(filter(
        lambda x: library.get_titles_in_string(x) and len(x.split()) <= 5,
        match_text[1]))
    match_spans[1] = [ms[1] for ms in match_spans[1]] #remove enumerate
    match_spans = match_spans[0] + match_spans[1]
    match_text = match_text[0] + match_text[1]

    nice_goy = 'עובד כוכבים'
    repl = get_goy_repl(stri, comp_stri)
    if repl is not None:
        match_spans += [((m.start(), m.end()), repl) for m in re.finditer(nice_goy, stri)]
    return match_spans

def get_goy_repl(s, t):
    goy_repls = ['גוי', 'נכרי']
    nice_goy = 'עובד כוכבים'
    repl = None
    if nice_goy in s and nice_goy not in t:
        for grepl in goy_repls:
            if grepl in t:
                repl = grepl
                break
    return repl

def get_words_removed(s, t):
    removed_indices = base_tokenizer_removed_indices(s, t)
    words = re.split(r'\s', s)
    removed_chars = base_tokenizer_removed_chars(s, t)
    return removed_indices, words, removed_chars

def find_changes_between_wiki_and_will():
    import math, bisect
    from data_utilities import dibur_hamatchil_matcher
    from tqdm import tqdm

    out = {}
    total = 0
    missed = 0
    for title in tqdm(library.get_indexes_in_category("Bavli")):
        wiki = Version().load({"title": title, "versionTitle": "Wikisource Talmud Bavli", "language": "he"})
        will = Version().load({"title": title, "versionTitle": "William Davidson Edition - Aramaic", "language": "he"})
        for isec, (wiki_section, will_section) in enumerate(zip(wiki.chapter, will.chapter)):
            for iseg, (wiki_segment, will_segment) in enumerate(zip(wiki_section, will_section)):
                daf = math.ceil((isec+1)/2)
                amud = 'b' if (isec+1) % 2 == 0 else 'a'
                tref = f"{title} {daf}{amud}:{iseg+1}"
                wiki_removed_indices, wiki_original_words, wiki_removed_chars = get_words_removed(wiki_segment, will_segment)
                wiki_tokenized_words = base_tokenizer(wiki_segment, will_segment)
                will_removed_indices, will_original_words, will_removed_chars = get_words_removed(will_segment, will_segment)
                will_tokenized_words = base_tokenizer(will_segment, will_segment)

                matched = dibur_hamatchil_matcher.match_text(wiki_tokenized_words, [" ".join(will_tokenized_words)], verbose=False, strict_boundaries=True, place_all=True, with_abbrev_matches=True)
                total += 1
                if matched['matches'][0][0] == -1:
                    # no match
                    missed += 1
                    continue
                for abbrev_list in matched['abbrevs']:
                    for abbrev in abbrev_list:
                        # print('orig', abbrev.gemaraRange, abbrev.rashiRange)
                        wikiWordRange = [x + bisect.bisect_right(wiki_removed_indices, x) for x in abbrev.gemaraRange]                        
                        willWordRange = [x + bisect.bisect_right(will_removed_indices, x) for x in abbrev.rashiRange]
                        wiki_start_char = len(" ".join(wiki_original_words[:wikiWordRange[0]]))
                        if wiki_start_char > 0:
                            # account for space after initial words
                            wiki_start_char += 1
                        wiki_end_char = len(" ".join(wiki_original_words[:wikiWordRange[1]+1]))
                        wikiCharRange = [wiki_start_char, wiki_end_char]
                        will_start_char = len(" ".join(will_original_words[:willWordRange[0]]))
                        if will_start_char > 0:
                            will_start_char += 1
                        will_end_char = len(" ".join(will_original_words[:willWordRange[1]+1]))
                        willCharRange = [will_start_char, will_end_char]
                        wiki_removed_chars += [(tuple(wikiCharRange), will_segment[willCharRange[0]:willCharRange[1]])]
                        # print(f"~{wiki_segment[wikiCharRange[0]:wikiCharRange[1]]}~")
                        # print(f"~{will_segment[willCharRange[0]:willCharRange[1]]}~")
                        # print('after', wikiWordRange, willWordRange)
                        # print(wiki_original_words[wikiWordRange[0]:wikiWordRange[1]+1])
                        # print(will_original_words[willWordRange[0]:willWordRange[1]+1])
                out[tref] = {
                    'wiki': wiki_removed_chars,
                    'will': will_removed_chars
                }
    print('Total', total)
    print('Missed', missed)
    print('Perc', missed/total)
    with open(f"{DATASET_LOC}/wiki_will_changes.json", 'w') as fout:
        json.dump(out, fout)

def num_tanakh_person(slug, vtitle, lang):
    j = srsly.read_json(f"{DATASET_LOC}/ner_output_tanakh.json")
    print(len(list(filter(lambda x: slug in x['id_matches'] and x['versionTitle'] == vtitle and x['language'] == lang, j))))

def find_true_bonayich_rabbis():
    with open("/home/nss/sefaria/datasets/ner/michael-sperling/sperling_en_and_he_original.csv", "r") as fin:
        c = csv.DictReader(fin)
        rows = list(c)
    exist_count = 0
    na_count = 0
    for row in rows:
        titles = set()
        for i in range(1,4):
            title = row[f'En {i}'].strip()
            if len(title) == 0 or title == "N/A" or title == "MM":
                break
            titles.add(title)
        exists_in_db = False
        for title in titles:
            ts = TopicSet({"titles.text": title})
            for t in ts:
                if IntraTopicLink().load({"$or": [{"toTopic": yo, "fromTopic": t.slug} for yo in ['mishnaic-people', 'talmudic-people', 'group-of-mishnaic-people', 'group-of-talmudic-people']]}) is not None:
                    exists_in_db = True
                    break
                else:
                    print("Title exists but no link", titles)
            if exists_in_db:
                break
        if exists_in_db:
            exist_count += 1
            row['Exists in DB'] = 'y'
        else:
            # print(titles, row['He'])
            row['Exists in DB'] = 'n'
            na_count += 1
    with open("/home/nss/sefaria/datasets/ner/michael-sperling/sperling_en_and_he.csv", "w") as fout:
        c = csv.DictWriter(fout, rows[0].keys())
        c.writeheader()
        c.writerows(rows)
    print(exist_count, na_count)

def add_more_mishnah_titles():
    from sefaria.utils.hebrew import is_hebrew, strip_cantillation
    with open("/home/nss/sefaria/datasets/ner/sefaria/temp/Rabbis in Mishnah Corrections - cross_validated_by_language.csv", "r") as fin:
        c = csv.DictReader(fin)
        for row in c:
            # TODO deal with mistakes
            if row['Error Type (rabbi, title, mistake, correct, skip)'] != 'title':
                continue
            new_title = strip_cantillation(row['Missing Title'], strip_vowels=True)
            if new_title == 'TYPO':
                continue
            slug = row['Missing Title Slug']
            if len(slug) == 0:
                print('NO MISSING TITLE SLUG', row)
                continue
            if slug.startswith('BONAYICH'):
                continue
            t = Topic.init(slug)
            if t is None:
                print("NO TOPIC FOR SLUG", slug, row)
                continue

            if len(new_title) == 0:
                print("ZERO LEN NEW TITLE", row)
                continue
            t.titles += [{
                "text": new_title,
                "lang": "he" if is_hebrew(new_title) else "en"
            }]
            t.save()

def save_manual_mistakes_mishnah():
    with open("/home/nss/sefaria/datasets/ner/sefaria/temp/Rabbis in Mishnah Corrections - cross_validated_by_language.csv", "r") as fin:
        c = csv.DictReader(fin)
        out_rows = []
        for row in c:
            if row['Error Type (rabbi, title, mistake, correct, skip)'] != 'mistake':
                continue
            out_rows += [{
                "start": int(row["Start"]),
                "end": int(row["End"]),
                "versionTitle": row["Version"],
                "language": row["Language"],
                "ref": row["Ref"],
                "mention": row["Rabbi Snippet"].split("~")[1],
                "correctionType": "mistake"
            }]
    with open("/home/nss/sefaria/data/research/knowledge_graph/named_entity_recognition/manual_corrections_mishnah.json", "w") as fout:
        json.dump(out_rows, fout, ensure_ascii=False, indent=2)

def save_mike_noah_differences_csv():
    from collections import defaultdict
    manual_sef_id_map = defaultdict(set)
    with open(f"/home/nss/sefaria/datasets/ner/michael-sperling/Match Bonayich Rabbis with Sefaria Rabbis - Sefaria Rabbis Matched.csv", "r") as fin:
        c = csv.DictReader(fin)
        for row in c:
            try:
                manual_sef_id_map[int(row["Bonayich ID"])].add(row["Slug"])
            except ValueError:
                continue

    def save_diff(diff_set, out_file):
        rows = []
        diff_list = sorted(diff_set, key=lambda x: Ref(x[3]).order_id())
        for diff in diff_list:
            rows += [{
                "Start": diff[0],
                "End": diff[1],
                "Mention": diff[2],
                "Ref": diff[3],
            }]
        with open(out_file, "w") as fout:
            c = csv.DictWriter(fout, ['Ref', 'Mention', 'Start', 'End'])
            c.writeheader()
            c.writerows(rows)

    def get_sets(a_not_bf, b_not_af):
        with open(a_not_bf, "r") as fin:
            a_not_b = {(a['start'], a['end'], a['mention'], a['ref']) for a in json.load(fin)}
        with open(b_not_af, "r") as fin:
            b_not_a = {(a['start'], a['end'], a['mention'], a['ref']) for a in json.load(fin)}
        return a_not_b.difference(b_not_a), b_not_a.difference(a_not_b)

    a_not_b, b_not_a = get_sets("/home/nss/sefaria/datasets/ner/sefaria/a_not_b.json", "/home/nss/sefaria/datasets/ner/sefaria/b_not_a.json")
    save_diff(a_not_b, "/home/nss/sefaria/datasets/ner/michael-sperling/sefaria_not_sperling.csv")
    save_diff(b_not_a, "/home/nss/sefaria/datasets/ner/michael-sperling/sperling_not_sefaria.csv")

    

if __name__ == "__main__":
    # make_rav_rabbi_csv()
    # make_csv_of_alt_titles()
    # make_csvs_for_stub_rabbis()
    # check_rabi_rav_results()
    # check_new_rabbis_to_create()
    # fix_stub_rabbis()
    # how_much_is_coming_from_bonayich()
    # remove_gen_data()
    # find_changes_between_wiki_and_will()
    # num_tanakh_person('aaron', "Tanakh: The Holy Scriptures, published by JPS", 'en')
    # find_true_bonayich_rabbis()
    # make_levi_shmuel_csv()
    # add_more_mishnah_titles()
    # save_manual_mistakes_mishnah()
    save_mike_noah_differences_csv()
"""
Confirm new rabbis to create
Create them
Add alt tiltes
For Hebrew
- Mistakes: Modify script that makes Sperling links to delete these links
- New rabbis / alt titles: Modfiy script ... to replace these links with new titles / rabbis
"""


"""
find exact characters that are removed when whole words are removed
find exact characters that are swapped when there's an abbreviation
output file with map per ref of characters to remove/swap
add optional input to convert nikkud func that takes this mapping
the regex to find swapped characters will read this map and output the proper regex
"""

"""
'abbrevs'
    list
        list
            gemaraRange aka wiki
            rashiRange aka will
"""