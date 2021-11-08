import django, json, csv, re, sklearn, sys, fasttext, random, pickle
django.setup()
import numpy as np
from tqdm import tqdm
from collections import defaultdict
from sefaria.model import *
from difflib import SequenceMatcher
from sefaria.utils.hebrew import strip_cantillation
from sources.puncutation_project.lift_punctuation import ConnectedTalmud, SteinsaltzIntro, build_maps
DATA = "/home/nss/sefaria/data/research/steinsaltz_punctuation_ml/data"
RAW_PUNCT = f"{DATA}/raw_punct_out"
titles = ["Berakhot", "Shabbat", "Eruvin", "Pesachim", "Yoma", "Sukkah"]
alt_vtitle_titles = ["Pesachim"]
vtitle_wo_vowels = 'William Davidson Edition - Aramaic'
VTITLE = "William Davidson Edition - Vocalized Aramaic"
VTITLE_ALT = "William Davidson Edition - Vocalized Punctuated Aramaic"
GERSHAYIM = '\u05F4'
DASH = '\u2014'
punctuation = f'\s.,:!?—"{GERSHAYIM}'
bad_puncts = {':.': '.', '?,': '?', '!.': '!', '!,': '!'}

def calc_rows_from_single_diff(raw_punct, gold_punct, tag):
    rows = []
    if tag == 'equal':
        while len(raw_punct) > 0:
            m = re.search(fr'^(\s*[{punctuation}]+\s*|[^{punctuation}]+)', raw_punct)
            rows += [{
                'In': m.group(),
                'Tag': tag,
                'Out': m.group(),
            }]
            raw_punct = raw_punct[m.end():]
    else:
        # just return one row and assume change is atomic
        raw_punct = re.sub(fr'[^{punctuation}\s]+', '', raw_punct)
        gold_punct = re.sub(fr'[^{punctuation}\s]+', '', gold_punct)
        if len(raw_punct) == 0 and len(gold_punct) == 0:
            return rows
        rows += [{
            'In': raw_punct,
            'Tag': tag,
            'Out': gold_punct,
        }]
    return rows

def collapse_inserts(in_rows):
    def is_collapsable(row):
        return re.match(fr'^[{punctuation}\s]*$', row['In']) is not None
    def is_text(row):
        return re.match(r'^[\u05d0-\u05ea]+$', row['In']) is not None
    out_rows = []
    skip_next = False
    for i, row in enumerate(in_rows):
        if skip_next:
            skip_next = False
            continue
        if i < (len(in_rows) - 1) and is_collapsable(in_rows[i+1]) and is_collapsable(row):
            skip_next = True
            combo_row = {
                'In': row['In'] + in_rows[i+1]['In'],
                'Out': row['Out'] + in_rows[i+1]['Out'],
                'Tag': 'replace',
            }
            out_rows += [combo_row]
        elif row['Tag'] == 'insert' and (0 < i < (len(in_rows) - 1)) and is_text(in_rows[i-1]) and is_text(in_rows[i+1]):
            # both prev and next row are all text, we're in the middle of a word
            combo_row = {
                'In': '----',  # special token for indicating this is the middle of a word
                'Out': row['Out'],
                'Tag': 'replace',
            }
            out_rows += [combo_row]
        elif row['Tag'] == 'equal' and i < (len(in_rows) - 1) and is_text(row) and is_text(in_rows[i+1]):
            combo_row = {
                'In': row['In'] + in_rows[i+1]['In'],
                'Out': row['Out'] + in_rows[i+1]['Out'],
                'Tag': 'equal',
            }
            skip_next = True
            out_rows += [combo_row]
        else:
            out_rows += [row]
    return out_rows

def calc_diff(raw_punct, gold_punct):
    def rows_equal(row1, row2):
        for k, v in row1.items():
            if v != row2[k]:
                return False
        return True
    # add trailing space to be able to collapse insert at end of segment if needed
    gold_punct = " " + strip_cantillation(gold_punct, strip_vowels=True) + " "
    raw_punct = " " + raw_punct.replace('"', GERSHAYIM) + " "
    s = SequenceMatcher(None, raw_punct + " ", gold_punct + " ", False)
    codes = s.get_opcodes()
    diff_rows = []
    for tag, i1, i2, j1, j2 in codes:
        diff_rows += calc_rows_from_single_diff(raw_punct[i1:i2], gold_punct[j1:j2], tag)

    is_diff = True
    while is_diff:
        new_diff_rows = collapse_inserts(diff_rows)
        if len(new_diff_rows) == len(diff_rows):
            if all(rows_equal(new_row, old_row) for new_row, old_row in zip(new_diff_rows, diff_rows)):
                is_diff = False
        diff_rows = new_diff_rows
    return diff_rows

def create_for_tractate(title):
    raw_punct_map = {}
    en_map = {}
    he_map = {}
    out_rows = []
    with open(f"{RAW_PUNCT}/{title}.csv", "r") as fin:
        c = csv.DictReader(fin)
        for row in c:
            raw_punct_map[row['Ref']] = row['Text']
    def en_action(s, en_tref, he_tref, v):
        nonlocal en_map
        en_map[en_tref] = s
    def he_action(s, en_tref, he_tref, v):
        nonlocal he_map
        he_map[en_tref] = s
    def action(s, en_tref, he_tref, v):
        nonlocal raw_punct_map, out_rows, en_map, he_map
        oref = Ref(en_tref)
        next_oref = oref.next_segment_ref()
        en_text = en_map.get(oref.normal(), '')
        is_last_on_amud = next_oref is not None and next_oref.sections[0] != oref.sections[0]
        is_cutoff = len(en_text) > 0 and is_last_on_amud and re.search(r'[.!?]$', re.sub(r'<[^>]+>', '', en_text.strip())) is None

        raw_punct_text = raw_punct_map[en_tref]
        gold_punct_text = s
        if is_cutoff:
            raw_punct_text += " " + raw_punct_map[next_oref.normal()]
            gold_punct_text = s + " " + he_map[next_oref.normal()]
            en_tref = oref.to(next_oref).normal()
        diff_rows = calc_diff(raw_punct_text, gold_punct_text)
        for row in diff_rows:
            row['Ref'] = en_tref
            out_rows += [row]

    vtitle = VTITLE_ALT if title in alt_vtitle_titles else VTITLE
    en_version = Version().load({"title": title, "language": "en", "versionTitle": "William Davidson Edition - English"})
    en_version.walk_thru_contents(en_action)
    version = Version().load({"title": title, "language": "he", "versionTitle": vtitle})
    version.walk_thru_contents(he_action)
    version.walk_thru_contents(action)

    with open(f"{DATA}/punct_diff/{title}.csv", "w") as fout:
        c = csv.DictWriter(fout, ['Ref', 'In', 'Out', 'Tag'])
        c.writeheader()
        c.writerows(out_rows)

def create_all():
    for title in titles:
        create_for_tractate(title)

def process_file_for_running(title):
    """
    for running on punct file w/o gold
    """
    with open(f"{RAW_PUNCT}/{title}.csv", "r") as fin:
        c = csv.DictReader(fin)
if __name__ == "__main__":
    create_all()

"""
TODO
- replace squigglys
- collapse "inserts"s on either prev or next row, assuming one of them is a space / punct
- make sure there are only punct chars in diff

python lift_punctuation.py -t "Rosh Hashanah" -c "/home/nss/sefaria/data/research/steinsaltz_punctuation_ml/data/raw_punct_out/Rosh Hashanah"
"""