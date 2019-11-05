#encoding=utf-8

import json, codecs, re
from tqdm import tqdm
from collections import defaultdict
import django
django.setup()
from sefaria.model import *
from research.mesorat_hashas_sefaria.mesorat_hashas import ParallelMatcher
from research.knowledge_graph.sefer_haagada.main import disambiguate_ref_list

NONEXISTANT_BOOKS = {
    u"רש\"ר הירש",
    u"רשר\"ה",
    u"ילקוט ראובני",
    u"ילקוט המכירי",
    u"אמונות ודעות",
    u"תומר דבורה",
    u"רמ\"ע מפאנו",
    u"מכתב מאליהו",
    u"יוסף לקח",
    u"אגרת שמואל",
    u"מגילת סתרים",
    u"מגלת סתרים",
    u"מהר\"י יעבץ",
    u"מהר\"י יעב\"ץ",
    u"חכמה ומוסר",
    u"שערי קדושה",
    u"רבינו ירוחם",
    u"מנורת המאור",
    u"ספר חרדים",
    u"כוכבי אור",
    u"גבור - גבורה",
    u"מבעלי התוספות",
    u"מבעלי תוספות",
    u"דמשק",
    u"שיעורי דעת",
    u"רוח חיים",
    u"בכור",
    u"עקרים",
    u"אגרת שמואל ומדרש שמואל",
    u"יוסיף לקח",
    u"תעלומות חכמה",
    u"הע\"ד",
    u"מסכת כותים",
    u"פירוש המשניות",
    u"דרשים",
    u"ציבא",
    u"צרור המור, לחם דמעה"
}

TODEALWITH = [
    u"מוהר\"ן",
    u"מדרש הגדול",
    u"זהר",
    u"מדרשים",
    u"מדרש תדשא",
    u"אותיות דר' עקיבא",
    u"אותיות דרבי עקיבא",
    u"אותיות דר\"ע",
    u"אגרת תימן",



]

with codecs.open("aspaklaria_db.json", "rb", encoding="utf8") as fin:
    jin = json.load(fin)
with codecs.open("aspaklaria_good.json", "rb", encoding="utf8") as fin:
    prev_good = json.load(fin)
with codecs.open("aspaklaria_bad.json", "rb", encoding="utf8") as fin:
    prev_bad = json.load(fin)
prev_good_id_set = {
    (doc['topic'], doc['cnt']): doc for doc in prev_good
}
prev_bad_id_set = {
    (doc['topic'], doc['cnt']): doc for doc in prev_bad
}

good = []
bad = []
num_pmed = 0
num_nonexistant = 0
total = 0
index_guess_set = defaultdict(lambda: {"count": 0, "examples": []})
curr_author = None
prev_doc = None
pm_index_map = defaultdict(list)
for doc in tqdm(jin, leave=False, smoothing=0):
    total += 1
    if doc["author"] in NONEXISTANT_BOOKS:
        num_nonexistant += 1
    if doc["author"] != curr_author:
        curr_author = doc["author"]
        prev_doc = None
    if not doc.get('is_sham', False):
        prev_doc = None
    key = (doc['topic'], doc['cnt'])
    if key in prev_good_id_set and len(doc.get("pm_ref", "")) > 0:
        doc['solution'] = prev_good_id_set[key]['solution']
        doc['index'] = prev_good_id_set[key]['index']
        doc['pm_ref'] = prev_good_id_set[key]['pm_ref']
        good += [doc]
        continue
    elif key in prev_bad_id_set:
        prev_doc = prev_bad_id_set[key]
        if prev_doc['issue'] == 'index derived':
            pm_index_map[prev_doc['index']] += [prev_doc]
        else:
            doc['issue'] = prev_doc['issue']
            bad += [doc]
        continue
    if doc.get("pm_ref", "") is not None and len(doc.get("pm_ref", "")) > 0:
        # assume this is fine
        doc['solution'] = 'easy'
        good += [doc]
        prev_doc = doc
        continue
    elif len(doc.get("ref", "")) > 0:
        prev_doc = doc
        try:
            results = disambiguate_ref_list(doc['ref'], [(doc['text'], '0')])
        except AttributeError as e:
            print doc['ref']
            doc['issue'] = 'attribute error'
            bad += [doc]
            continue
        pm_ref = results['0']['A Ref'] if results['0'] else results['0']
        if pm_ref:
            num_pmed += 1
            doc['pm_ref'] = pm_ref
            doc['solution'] = "pm again"
            good += [doc]
        else:
            doc['issue'] = 'pm failed twice'
            bad += [doc]
    elif doc.get('is_sham', False) and len(doc.get("index", "")) == 0 and prev_doc is not None:
        doc['issue'] = "index derived"
        doc['prev_raw_ref'] = prev_doc['raw_ref']
        doc['prev_ref'] = prev_doc.get("ref", "")
        doc['prev_author'] = prev_doc['author']
        bad += [doc]
    else:
        doc['issue'] = "unknown"
        bad += [doc]
        # inds = tuple(doc["index_guess"].split(" |"))
        # index_guess_set[inds]["count"] += 1
        # index_guess_set[inds]["examples"] += [{"t": doc["topic"], "c": doc["cnt"], "a": doc["author"], "r": doc["raw_ref"]}]

count = 0
for index, doc_list in tqdm(pm_index_map.items(), leave=False, smoothing=0):
    count += 1
    if count > 10000:
        bad += doc_list
        continue
    doc_map = {
        u"{}||{}".format(doc['topic'], doc['cnt']): doc for doc in doc_list
    }
    try:
        print u"DISAMBIGUATING {} TOTAL {}".format(index, len(doc_list))
        results = disambiguate_ref_list(index, [(doc['text'], u"{}||{}".format(doc['topic'], doc['cnt'])) for doc in doc_list], max_words_between=3, min_words_in_match=5, ngram_size=5, verbose=True)
        good_count = 0
        for key, result in results.items():
            doc = doc_map[key]
            if result is None:
                doc['issue'] = 'index derived pm failed'
                bad += [doc]
            else:
                pm_ref = result['A Ref']
                doc['pm_ref'] = pm_ref
                doc['solution'] = 'index derived pm'
                good += [doc]
                good_count += 1
        print u"Found {}/{}".format(good_count, len(doc_list))
    except AttributeError as e:
        doc['issue'] = 'index derived pm attribute error'
        print "ATTRIBUTE ERROR!!"
        bad += doc_list
print "Num Nonexistant {}".format(num_nonexistant)
print "Num Good {} Num Bad {}. Percent {}".format(len(good), len(bad), 1.0*len(good)/len(jin))
with codecs.open("aspaklaria_good.json", "wb", encoding="utf8") as fout:
    json.dump(good, fout, ensure_ascii=False, indent=2)
with codecs.open("aspaklaria_bad.json", "wb", encoding="utf8") as fout:
    json.dump(bad, fout, ensure_ascii=False, indent=2)