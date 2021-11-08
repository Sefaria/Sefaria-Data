import argparse, math
from pymongo import MongoClient
import json, codecs, re
from tqdm import tqdm
from collections import defaultdict
import django
django.setup()
from sefaria.model import *
from research.mesorat_hashas_sefaria.mesorat_hashas import ParallelMatcher
from research.knowledge_graph.sefer_haagada.main import disambiguate_ref_list
from sefaria.settings import MONGO_HOST, MONGO_PORT
from sefaria.system.exceptions import InputError
from sefaria.system.database import db
client = MongoClient(MONGO_HOST, MONGO_PORT)
db_aspaklaria = client.aspaklaria

# in order to print Hebrew on K8S
# import sys
# reload(sys)
# sys.setdefaultencoding('utf8')

NONEXISTANT_BOOKS = {
    "רש\"ר הירש",
    "רשר\"ה",
    "ילקוט ראובני",
    "ילקוט המכירי",
    "אמונות ודעות",
    "תומר דבורה",
    "רמ\"ע מפאנו",
    "מכתב מאליהו",
    "יוסף לקח",
    "אגרת שמואל",
    "מגילת סתרים",
    "מגלת סתרים",
    "מהר\"י יעבץ",
    "מהר\"י יעב\"ץ",
    "חכמה ומוסר",
    "שערי קדושה",
    "רבינו ירוחם",
    "מנורת המאור",
    "ספר חרדים",
    "כוכבי אור",
    "גבור - גבורה",
    "מבעלי התוספות",
    "מבעלי תוספות",
    "דמשק",
    "שיעורי דעת",
    "רוח חיים",
    "בכור",
    "עקרים",
    "אגרת שמואל ומדרש שמואל",
    "יוסיף לקח",
    "תעלומות חכמה",
    "הע\"ד",
    "מסכת כותים",
    "פירוש המשניות",
    "דרשים",
    "ציבא",
    "צרור המור, לחם דמעה"
}

TODEALWITH = [
    "מוהר\"ן",
    "מדרש הגדול",
    "זהר",
    "מדרשים",
    "מדרש תדשא",
    "אותיות דר' עקיבא",
    "אותיות דרבי עקיבא",
    "אותיות דר\"ע",
    "אגרת תימן",



]

# with codecs.open("aspaklaria_db.json", "rb", encoding="utf8") as fin:
#     jin = json.load(fin)
# with codecs.open("aspaklaria_good.json", "rb", encoding="utf8") as fin:
#     prev_good = json.load(fin)
# with codecs.open("aspaklaria_bad.json", "rb", encoding="utf8") as fin:
#     prev_bad = json.load(fin)
# prev_good_id_set = {
#     (doc['topic'], doc['cnt']): doc for doc in prev_good
# }
# prev_bad_id_set = {
#     (doc['topic'], doc['cnt']): doc for doc in prev_bad
# }

# good = []
# bad = []
# num_pmed = 0
# num_nonexistant = 0
# total = 0
# index_guess_set = defaultdict(lambda: {"count": 0, "examples": []})
# curr_author = None
# prev_doc = None
# pm_index_map = defaultdict(list)
# for doc in tqdm(jin, leave=False, smoothing=0):
#     total += 1
#     if doc["author"] in NONEXISTANT_BOOKS:
#         num_nonexistant += 1
#     if doc["author"] != curr_author:
#         curr_author = doc["author"]
#         prev_doc = None
#     if not doc.get('is_sham', False):
#         prev_doc = None
#     key = (doc['topic'], doc['cnt'])
#     if key in prev_good_id_set and len(doc.get("pm_ref", "")) > 0:
#         doc['solution'] = prev_good_id_set[key]['solution']
#         doc['index'] = prev_good_id_set[key]['index']
#         doc['pm_ref'] = prev_good_id_set[key]['pm_ref']
#         good += [doc]
#         continue
#     elif key in prev_bad_id_set:
#         prev_doc = prev_bad_id_set[key]
#         if prev_doc['issue'] == 'index derived':
#             pm_index_map[prev_doc['index']] += [prev_doc]
#         else:
#             doc['issue'] = prev_doc['issue']
#             bad += [doc]
#         continue
#     if doc.get("pm_ref", "") is not None and len(doc.get("pm_ref", "")) > 0:
#         # assume this is fine
#         doc['solution'] = 'easy'
#         good += [doc]
#         prev_doc = doc
#         continue
#     elif len(doc.get("ref", "")) > 0:
#         prev_doc = doc
#         try:
#             results = disambiguate_ref_list(doc['ref'], [(doc['text'], '0')])
#         except AttributeError as e:
#             print(doc['ref'])
#             doc['issue'] = 'attribute error'
#             bad += [doc]
#             continue
#         pm_ref = results['0']['A Ref'] if results['0'] else results['0']
#         if pm_ref:
#             num_pmed += 1
#             doc['pm_ref'] = pm_ref
#             doc['solution'] = "pm again"
#             good += [doc]
#         else:
#             doc['issue'] = 'pm failed twice'
#             bad += [doc]
#     elif doc.get('is_sham', False) and len(doc.get("index", "")) == 0 and prev_doc is not None:
#         doc['issue'] = "index derived"
#         doc['prev_raw_ref'] = prev_doc['raw_ref']
#         doc['prev_ref'] = prev_doc.get("ref", "")
#         doc['prev_author'] = prev_doc['author']
#         bad += [doc]
#     else:
#         doc['issue'] = "unknown"
#         bad += [doc]
#         # inds = tuple(doc["index_guess"].split(" |"))
#         # index_guess_set[inds]["count"] += 1
#         # index_guess_set[inds]["examples"] += [{"t": doc["topic"], "c": doc["cnt"], "a": doc["author"], "r": doc["raw_ref"]}]

# count = 0
# for index, doc_list in tqdm(pm_index_map.items(), leave=False, smoothing=0):
#     count += 1
#     if count > 10000:
#         bad += doc_list
#         continue
#     doc_map = {
#         u"{}||{}".format(doc['topic'], doc['cnt']): doc for doc in doc_list
#     }
#     try:
#         print("DISAMBIGUATING {} TOTAL {}".format(index, len(doc_list)))
#         results = disambiguate_ref_list(index, [(doc['text'], u"{}||{}".format(doc['topic'], doc['cnt'])) for doc in doc_list], max_words_between=3, min_words_in_match=5, ngram_size=5, verbose=True)
#         good_count = 0
#         for key, result in results.items():
#             doc = doc_map[key]
#             if result is None:
#                 doc['issue'] = 'index derived pm failed'
#                 bad += [doc]
#             else:
#                 pm_ref = result['A Ref']
#                 doc['pm_ref'] = pm_ref
#                 doc['solution'] = 'index derived pm'
#                 good += [doc]
#                 good_count += 1
#         print("Found {}/{}".format(good_count, len(doc_list)))
#     except AttributeError as e:
#         doc['issue'] = 'index derived pm attribute error'
#         print("ATTRIBUTE ERROR!!")
#         bad += doc_list
# print("Num Nonexistant {}".format(num_nonexistant))
# print("Num Good {} Num Bad {}. Percent {}".format(len(good), len(bad), 1.0*len(good)/len(jin)))
# with codecs.open("aspaklaria_good.json", "wb", encoding="utf8") as fout:
#     json.dump(good, fout, ensure_ascii=False, indent=2)
# with codecs.open("aspaklaria_bad.json", "wb", encoding="utf8") as fout:
#     json.dump(bad, fout, ensure_ascii=False, indent=2)

def update_doc(doc, is_good):
    collection = db.aspaklaria_good if is_good else db.aspaklaria_bad
    del doc['_id']
    collection.replace_one({"topic": doc['topic'], "cnt": doc['cnt']}, doc, upsert=True)


def delete_doc(doc, is_good):
    collection = db.aspaklaria_good if is_good else db.aspaklaria_bad
    collection.remove({"topic": doc['topic'], "cnt": doc['cnt']})


def doit(num_divisions, position):
    prev_good_id_set = {}
    for doc in db_aspaklaria.aspaklaria_good.find():
        prev_good_id_set[(doc['topic'], doc['cnt'])] = doc

    good = []
    bad = []
    num_pmed = 0
    num_nonexistant = 0
    total = 0
    index_guess_set = defaultdict(lambda: {"count": 0, "examples": []})
    curr_author = None
    prev_doc = None
    pm_index_map = defaultdict(list)
    for doc in tqdm(db_aspaklaria.aspaklaria_source.find(), leave=False, smoothing=0):
        total += 1
        if doc["author"] in NONEXISTANT_BOOKS:
            num_nonexistant += 1
        if doc["author"] != curr_author:
            curr_author = doc["author"]
            prev_doc = None
        if not doc.get('is_sham', False):
            prev_doc = None
        key = (doc['topic'], doc['cnt'])
        prev_good = prev_good_id_set.get(key, None)
        if prev_good is not None and prev_good.get("pm_ref", "") is not None and len(prev_good.get("pm_ref", "")) > 0:
            doc['solution'] = prev_good['solution']
            try:
                doc['index'] = prev_good['index']
            except KeyError as e:
                print("{} {} {}".format(prev_good['topic'], prev_good['cnt'], prev_good['pm_ref']))
            doc['pm_ref'] = prev_good['pm_ref']
            good += [doc]
            continue
        # elif prev_bad is not None:
        #     if prev_bad['issue'] == 'index derived':
        #         pm_index_map[prev_bad['index']] += [prev_bad]
        #     else:
        #         doc['issue'] = prev_bad['issue']
        #         bad += [doc]
        #     continue
        if doc.get("pm_ref", "") is not None and len(doc.get("pm_ref", "")) > 0:
            # assume this is fine
            doc['solution'] = 'easy'
            update_doc(doc, True)
            prev_doc = doc
            continue
        elif len(doc.get("ref", "")) > 0 and False:
            prev_doc = doc
            pm_index_map[doc['ref']] += [doc]
        elif doc.get('is_sham', False) and len(doc.get("index", "")) == 0 and prev_doc is not None:
            doc['issue'] = "index derived"
            doc['index'] = prev_doc['index']
            doc['prev_raw_ref'] = prev_doc['raw_ref']
            doc['prev_ref'] = prev_doc.get("ref", "")
            doc['prev_author'] = prev_doc['author']
            pm_index_map[doc['index']] += [doc]
        elif doc.get('index_guess', '') is not None and len(doc.get('index_guess', '')) > 0 and len(doc.get('index_guess', '').split(' |')) > 0:
            indexes = "|".join([x for x in doc.get('index_guess', '').split(' |') if len(x) > 0])
            if "Introductions to the Babylonian Talmud" in indexes and "Jerusalem Talmud" in indexes:
                # there was an error generating these indexes. generate again
                indexes = "|".join(library.get_indexes_in_category("Yerushalmi"))
            if "Mishneh Torah" in indexes and "Kessef Mishneh" in indexes and "Hasagot HaRaavad on Mishneh Torah" in indexes:
                indexes = "|".join(library.get_indexes_in_category("Mishneh Torah"))

            if len(indexes.split("|")) > 200:
                print("TOO MANY INDEXES!! {} {} {}".format(doc['topic'], doc['cnt'], doc['index_guess']))
                continue
            pm_index_map[indexes] += [doc]
        else:
            doc['issue'] = "unknown"
            update_doc(doc, False)
            # inds = tuple(doc["index_guess"].split(" |"))
            # index_guess_set[inds]["count"] += 1
            # index_guess_set[inds]["examples"] += [{"t": doc["topic"], "c": doc["cnt"], "a": doc["author"], "r": doc["raw_ref"]}]

    count = 0
    total = len(pm_index_map.items())
    start = total/num_divisions * position
    end = total if position == num_divisions - 1 else start + total/num_divisions  # ad v'lo ad b'chlal
    for idoc, (index, doc_list) in tqdm(enumerate(pm_index_map.items()), leave=False, smoothing=0):
        if start > count or count >= end:
            count += 1
            continue
        count += 1
        doc_map = {
            "{}||{}".format(doc['topic'], doc['cnt']): doc for doc in doc_list
        }
        try:
            print("DISAMBIGUATING {} TOTAL {} ({}/{})".format(index, len(doc_list), idoc, len(pm_index_map)))
            results = disambiguate_ref_list(index, [(doc['text'], "{}||{}".format(doc['topic'], doc['cnt'])) for doc in doc_list], max_words_between=3, min_words_in_match=5, ngram_size=5, verbose=True, with_match_text=True)
            good_count = 0
            for key, result in results.items():
                doc = doc_map[key]
                if result is None:
                    doc['issue'] = 'index derived pm failed'
                    update_doc(doc, False)
                else:
                    pm_ref = result['A Ref']
                    doc['pm_ref'] = pm_ref
                    doc['solution'] = 'index derived pm'
                    doc['score'] = result['Score']
                    doc['match_text_sef'] = result['Match Text A']
                    doc['match_text_asp'] = result['Match Text B']
                    update_doc(doc, True)
                    good_count += 1
            print("Found {}/{} in {}".format(good_count, len(doc_list), index))
        except AttributeError as e:
            print("ATTRIBUTE ERROR!!")


def doit_author_mapper(num_divisions, position):
    author_mapping = {
        "שוחר טוב": ["Midrash Tehillim"],
        "עקדה": ["Akeidat Yitzchak"],
        'מוהר"ן': ["Likutei Moharan"],
        "ברייתא דמלאכת המשכן": ["Otzar Midrashim"] + library.get_indexes_in_category('Midrash Rabbah'),
        "דרשים": ["Otzar Midrashim"] + library.get_indexes_in_category('Midrash Rabbah'),
        "מדרשים": ["Otzar Midrashim"] + library.get_indexes_in_category('Midrash Rabbah'),
        "הראקנטי": ["Recanati on the Torah"],
        "הריקאנטי": ["Recanati on the Torah"],
        "הרקאנטי": ["Recanati on the Torah"],
        'של"ה': ["Shenei Luchot HaBerit"],
        'דרשות הר"ן': ["Darashos HaRan"],
        "אור ה'": ["Ohr Hashem"],
        "ר' צדוק": library.get_indexes_in_category("R' Tzadok HaKohen"),
        "תנך": library.get_indexes_in_category('Tanakh'),
        "מדרש רבה": library.get_indexes_in_category('Midrash Rabbah'),
        'רד"ק': ['Radak on Genesis', 'Radak on Joshua', 'Radak on Judges', 'Radak on I Samuel', 'Radak on II Samuel', 'Radak on I Kings', 'Radak on II Kings', 'Radak on Isaiah', 'Radak on Jeremiah', 'Radak on Ezekiel', 'Radak on Hosea', 'Radak on Joel', 'Radak on Amos', 'Radak on Obadiah', 'Radak on Jonah', 'Radak on Micah', 'Radak on Nahum', 'Radak on Habakkuk', 'Radak on Zephaniah', 'Radak on Haggai', 'Radak on Zechariah', 'Radak on Malachi', 'Radak on Psalms', 'Radak on I Chronicles', 'Radak on II Chronicles'],
        'רש"י': ['Rashi on Genesis', 'Rashi on Exodus', 'Rashi on Leviticus', 'Rashi on Numbers', 'Rashi on Deuteronomy', 'Rashi on Joshua', 'Rashi on Judges', 'Rashi on I Samuel', 'Rashi on II Samuel', 'Rashi on I Kings', 'Rashi on II Kings', 'Rashi on Isaiah', 'Rashi on Jeremiah', 'Rashi on Ezekiel', 'Rashi on Hosea', 'Rashi on Joel', 'Rashi on Amos', 'Rashi on Obadiah', 'Rashi on Jonah', 'Rashi on Micah', 'Rashi on Nahum', 'Rashi on Habakkuk', 'Rashi on Zephaniah', 'Rashi on Haggai', 'Rashi on Zechariah', 'Rashi on Malachi', 'Rashi on Psalms', 'Rashi on Proverbs', 'Rashi on Job', 'Rashi on Song of Songs', 'Rashi on Ruth', 'Rashi on Lamentations', 'Rashi on Ecclesiastes', 'Rashi on Esther', 'Rashi on Daniel', 'Rashi on Ezra', 'Rashi on Nehemiah', 'Rashi on I Chronicles', 'Rashi on II Chronicles'],
        "כלי יקר": ["Or HaChaim on Genesis", "Or HaChaim on Exodus", "Or HaChaim on Leviticus", "Or HaChaim on Numbers", "Or HaChaim on Deuteronomy"],
        "תלמוד בבלי": library.get_indexes_in_category('Bavli')
    }
    pm_index_map = defaultdict(list)
    for doc in tqdm(db_aspaklaria.aspaklaria_bad.find()):
        if doc['author'] in author_mapping:
            pm_index_map["|".join(author_mapping[doc['author']])] += [doc]

    count = 0
    total = len(pm_index_map.items())
    start = total/num_divisions * position
    end = total if position == num_divisions - 1 else start + total/num_divisions  # ad v'lo ad b'chlal
    for idoc, (index, doc_list) in tqdm(enumerate(pm_index_map.items()), leave=False, smoothing=0):
        if start > count or count >= end:
            count += 1
            continue
        count += 1
        doc_map = {
            "{}||{}".format(doc['topic'], doc['cnt']): doc for doc in doc_list
        }
        try:
            print("DISAMBIGUATING {} TOTAL {} ({}/{})".format(index, len(doc_list), idoc, len(pm_index_map)))
            results = disambiguate_ref_list(index, [(doc['text'], "{}||{}".format(doc['topic'], doc['cnt'])) for doc in doc_list], max_words_between=3, min_words_in_match=5, ngram_size=5, verbose=True, with_match_text=True)
            good_count = 0
            for key, result in results.items():
                doc = doc_map[key]
                if result is None:
                    doc['issue'] = 'index derived pm failed'
                    update_doc(doc, False)
                else:
                    pm_ref = result['A Ref']
                    doc['pm_ref'] = pm_ref
                    doc['solution'] = 'index derived pm'
                    doc['score'] = result['Score']
                    doc['match_text_sef'] = result['Match Text A']
                    doc['match_text_asp'] = result['Match Text B']
                    update_doc(doc, True)
                    good_count += 1
            print("Found {}/{} in {}".format(good_count, len(doc_list), index))
        except AttributeError as e:
            print("ATTRIBUTE ERROR!!")


def doit_rashi():
    for doc in tqdm(db_aspaklaria.aspaklaria_bad.find({"author": 'רש"י'})):
        if doc.get("ref", ""):
            key = "{}||{}".format(doc['topic'], doc['cnt'])
            tref = 'Rashi on ' + doc['ref'] if 'Rashi' not in doc['ref'] else doc['ref']
            try:
                results = disambiguate_ref_list(tref, [(doc['text'], key)], verbose=True, with_match_text=True)
            except InputError:
                continue
            result = results[key]
            if result is None:
                continue
            pm_ref = result['A Ref']
            doc['pm_ref'] = pm_ref
            doc['solution'] = 'index derived pm'
            doc['score'] = result['Score']
            doc['match_text_sef'] = result['Match Text A']
            doc['match_text_asp'] = result['Match Text B']
            update_doc(doc, True)
            delete_doc(doc, False)
        else:
            print("{} | {}".format(doc['topic'], doc['cnt']))


def doit_talmud():
    doc_list = []
    doc_map = {}
    for doc in tqdm(db_aspaklaria.aspaklaria_bad.find({"author": 'תלמוד בבלי'})):
        key = "{}||{}".format(doc['topic'], doc['cnt'])
        doc_list += [(doc['text'], key)]
        doc_map[key] = doc
    num_good = 0
    results = disambiguate_ref_list("|".join(library.get_indexes_in_category('Bavli')), doc_list, max_words_between=3, min_words_in_match=4, ngram_size=4, verbose=True, with_match_text=True)
    for key, result in results.items():
        if result is None:
            continue

        doc = doc_map[key]
        pm_ref = result['A Ref']
        doc['pm_ref'] = pm_ref
        doc['solution'] = 'index derived pm'
        doc['score'] = result['Score']
        doc['match_text_sef'] = result['Match Text A']
        doc['match_text_asp'] = result['Match Text B']
        update_doc(doc, True)
        delete_doc(doc, False)
        num_good += 1
    print("NUM GOOD {}".format(num_good))


def doit_ellipses(num_divisions, position):
    from sefaria.system.database import db
    pm_index_map = defaultdict(list)
    for doc in tqdm(db.aspaklaria_good.find({"text": re.compile(r"[א-ת]\s*\.\.\.\s*[א-ת]")})):
        try:
            oref = Ref(doc['pm_ref'])
        except (KeyError, InputError):
            print("{} | {}".format(doc['topic'], doc['cnt']))
            continue
        if oref.primary_category in {"Talmud", "Tanakh"}:
            prev_section = oref.prev_section_ref()
            next_section = oref.next_section_ref()
            start_ref = prev_section if prev_section is not None else oref.section_ref()
            end_ref = next_section if next_section is not None else oref.section_ref()
            search_ref = start_ref.to(end_ref)
        else:
            search_ref = oref.section_ref()
        pm_index_map[search_ref.normal()] += [doc]
    count = 0
    total = len(pm_index_map.items())
    start = total/num_divisions * position
    end = total if position == num_divisions - 1 else start + total/num_divisions  # ad v'lo ad b'chlal
    for idoc, (index, doc_list) in tqdm(enumerate(pm_index_map.items()), leave=False, smoothing=0):
        if start > count or count >= end:
            count += 1
            continue
        count += 1
        doc_map = {
            "{}||{}".format(doc['topic'], doc['cnt']): doc for doc in doc_list
        }
        try:
            print("DISAMBIGUATING {} TOTAL {} ({}/{})".format(index, len(doc_list), idoc, len(pm_index_map)))
            pm_input = []
            for doc in doc_list:
                ellipses = [x.strip() for x in doc['text'].split('...') if len(x.strip()) > 0]
                if len(ellipses) < 2:
                    print('NOT ENOUGH ELLIPSES FOR {} | {}'.format(doc['topic'], doc['cnt']))
                    continue
                pm_input += [(ellipses[0], "{}||{}||A".format(doc['topic'], doc['cnt'])), (ellipses[-1], "{}||{}||B".format(doc['topic'], doc['cnt']))]
            results = disambiguate_ref_list(index, pm_input, max_words_between=3, min_words_in_match=4, ngram_size=4, verbose=True, with_match_text=True)
            good_count = 0
            sorted_items = sorted(results.items(), key=lambda x: x[0])
            for ikey, (key, resultA) in list(enumerate(sorted_items))[::2]:
                resultB = sorted_items[ikey + 1][1]
                doc = doc_map[re.sub(r"\|\|A$", "", key)]
                if resultA is None or resultB is None:
                    doc['issue'] = 'easy index derived pm failed'
                    update_doc(doc, False)
                    delete_doc(doc, True)
                else:
                    try:
                        pm_ref = Ref(resultA['A Ref']).to(Ref(resultB['A Ref'])).normal()
                    except InputError:
                        print("INPUT ERROR AFTER RESULT {} {}".format(resultA['A Ref'], resultB['A Ref']))
                        continue
                    doc['pm_ref'] = pm_ref
                    doc['solution'] = 'easy index derived pm'
                    doc['score'] = resultA['Score']
                    doc['match_text_sef'] = "{} ... {}".format(resultA['Match Text A'], resultB['Match Text A'])
                    doc['match_text_asp'] = "{} ... {}".format(resultA['Match Text B'], resultB['Match Text B'])
                    update_doc(doc, True)
                    good_count += 1
            print("Found {}/{} in {}".format(good_count, len(doc_list), index))
        except AttributeError as e:
            print("ATTRIBUTE ERROR!!")


def doit_pm_easy_again(num_divisions, position):
    pm_index_map = defaultdict(list)
    for doc in tqdm(db_aspaklaria.aspaklaria_bad.find({"issue": "easy failed"})):
        try:
            oref = Ref(doc['pm_ref'])
        except (KeyError, InputError):
            print("{} | {}".format(doc['topic'], doc['cnt']))
            continue
        #pm_index_map[doc['pm_ref']] += [doc]
        pm_index_map[oref.index.title] += [doc]
    count = 0
    total = len(pm_index_map.items())
    start = total / num_divisions * position
    end = total if (position == num_divisions - 1) else (start + total / num_divisions)  # ad v'lo ad b'chlal
    for idoc, (index, doc_list) in tqdm(list(enumerate(pm_index_map.items())), leave=False, smoothing=0):
        if start > count or count >= end:
            count += 1
            continue
        count += 1
        doc_map = {
            "{}||{}".format(doc['topic'], doc['cnt']): doc for doc in doc_list
        }
        try:
            print("DISAMBIGUATING {} TOTAL {} ({}/{})".format(index, len(doc_list), idoc, len(pm_index_map)))
            results = disambiguate_ref_list(index, [(doc['text'], "{}||{}".format(doc['topic'], doc['cnt'])) for doc in
                                                    doc_list], max_words_between=3, min_words_in_match=4, ngram_size=4,
                                            verbose=False, with_match_text=True)
            good_count = 0
            for key, result in results.items():
                doc = doc_map[key]
                if result is None:
                    doc['issue'] = 'easy failed again'
                    delete_doc(doc, True)
                    update_doc(doc, False)
                else:
                    pm_ref = result['A Ref']
                    doc['pm_ref'] = pm_ref
                    doc['solution'] = 'easy pm verified after fail'
                    doc['score'] = result['Score']
                    doc['match_text_sef'] = result['Match Text A']
                    doc['match_text_asp'] = result['Match Text B']
                    delete_doc(doc, False)
                    update_doc(doc, True)
                    good_count += 1
            print("Found {}/{} in {}".format(good_count, len(doc_list), index))
        except AttributeError as e:
            print("ATTRIBUTE ERROR!!")


def cleanup_time():
    for good_doc in tqdm(db_aspaklaria.aspaklaria_good.find()):
        db_aspaklaria.aspaklaria_bad.remove({"topic": good_doc["topic"], "cnt": good_doc["cnt"]})


if __name__ == "__main__":
    # args = argparse.ArgumentParser()
    # args.add_argument("-n", "--num_divisions", dest="num_divisions", default=None, help="you know...")
    # args.add_argument("-p", "--position", dest="position", default=None, help="duh")
    # user_args = args.parse_args()
    # doit(1, 0)
    # doit_author_mapper(1, 0)
    # cleanup_time()
    # doit_rashi()
    # doit_talmud()
    # doit_ellipses(int(user_args.num_divisions), int(user_args.position))
    # doit_pm_easy_again(int(user_args.num_divisions), int(user_args.position))
    # print "Num Good {} Num Bad {}. Percent {}".format(len(good), len(bad), 1.0*len(good)/len(jin))
    doit_ellipses(1, 0)
