import django, json, csv, re, sklearn, sys, fasttext, random, pickle
django.setup()
import numpy as np
from tqdm import tqdm
from collections import defaultdict
import tensorflow as tf
import tensorview as tv
from tensorflow import keras
from tensorflow.keras import preprocessing, datasets, layers, models, optimizers, losses, metrics, callbacks, initializers, backend, constraints
from tensorflow.python.platform import gfile
from sklearn.model_selection import train_test_split
from sefaria.model import *
from sefaria.utils.hebrew import strip_cantillation
from sources.puncutation_project.lift_punctuation import ConnectedTalmud, SteinsaltzIntro, build_maps

DATA = "/home/nss/sefaria/data/research/steinsaltz_punctuation_ml/data"
titles = ["Berakhot", "Shabbat", "Eruvin", "Pesachim", "Yoma", "Sukkah"]
alt_vtitle_titles = ["Pesachim"]
vtitle_wo_vowels = 'William Davidson Edition - Aramaic'
vtitle = "William Davidson Edition - Vocalized Aramaic"
vtitle_alt = "William Davidson Edition - Vocalized Punctuated Aramaic"
GERSHAYIM = '\u05F4'
DASH = '\u2014'
punctuation = f'\s.,:!?—"{GERSHAYIM}'
bad_puncts = {':.': '.'}

def split_by_type(s, type):
    char_group = punctuation
    if type == 'punct':
        char_group = '^' + char_group
    return list(filter(lambda x: len(x) > 0, re.split(fr'[{char_group}]+', s)))

def get_talmud_punct_possibilities(s):
    return split_by_type(s, 'punct')

def extract_punct_map(s):
    s = s.replace('"', GERSHAYIM)
    words  = split_by_type(s, 'words')
    puncts = split_by_type(s, 'punct')
    if len(words) == len(puncts) + 1:
        puncts += [""]
    if len(words) == len(puncts) - 1:
        words = [""] + words
    assert len(words) == len(puncts)
    return words, puncts

def extract_steinsaltz_possibilities(base_text, stein_text, word_punct_pairs):
    """
    strip off intro
    any punct found in bold is extracted separately
    any punct at end of bold or in commentary is combined and any subset is possible (accounting for order that punct appeared)
    """

    # algorithm works better when bold tags are consolidated
    stein_text = re.sub(r'</b>(\s*)<b>', r'\g<1>', stein_text)
    maps = build_maps(base_text, stein_text)
    talmud_word_index = 0
    for ts_map in maps:
        if not ts_map.actually_has_talmud() and (isinstance(ts_map.talmud_steinsaltz, SteinsaltzIntro) or isinstance(ts_map.talmud_steinsaltz, ConnectedTalmud)):
            continue
        talmud_words = split_by_type(ts_map.reg_talmud, 'words')
        talmud_possibilities = get_talmud_punct_possibilities(ts_map.talmud_steinsaltz.talmud)
        
        # all punct in talmud portion of stein can theoretically be on any word in talmud (since we don't have a word-to-word mapping) except last word
        for i, (tw1, (tw2, punct)) in enumerate(zip(talmud_words[:-1], word_punct_pairs[talmud_word_index:talmud_word_index+len(talmud_words)-1])):
            assert tw1 == strip_cantillation(tw2, strip_vowels=True)
            word_punct_pairs[talmud_word_index+i] += [talmud_possibilities]

        # last word can have punctuation on it + any combo of punctuation in stein
        talmud_word_index += len(talmud_words)
def create_dataset():
    fout = open(f"{DATA}/dataset.csv", "w")
    c = csv.DictWriter(fout, ['Ref', 'Word', 'Punctuation', 'Pre-quote', 'Post-quote', 'Dash'])
    c.writeheader()
    unique_puncts = defaultdict(int)
    def action(s, en_tref, he_tref, v):
        nonlocal fout
        try:
            words, puncts = extract_punct_map(s)
        except AssertionError:
            print("Len of words and puncts mismatch:", en_tref)
            return
        pre_quote_next = False
        for w, p in zip(words, puncts):
            pre_quote = pre_quote_next
            post_quote = re.search(fr'^\S*{GERSHAYIM}', p) is not None
            pre_quote_next = re.search(fr'{GERSHAYIM}$', p) is not None
            dash = DASH in p
            p = p.replace(GERSHAYIM, '').replace(DASH, '').strip()
            if p in bad_puncts:
                p = bad_puncts[p]
            unique_puncts[p] += 1
            c.writerow({
                "Ref": en_tref,
                "Word": w,
                "Punctuation": p,
                "Pre-quote": pre_quote,
                "Post-quote": post_quote,
                "Dash": dash,
            })

    for title in tqdm(titles):
        temp_vtitle = vtitle_alt if title in alt_vtitle_titles else vtitle
        version = Version().load({"title": title, "versionTitle": temp_vtitle, "language": "he"})
        if version is None:
            print("sad face", title)
            continue
        version.walk_thru_contents(action)
    fout.close()
    print('Num unique punctuation', len(unique_puncts))
    total_punct = 0
    for p, count in unique_puncts.items():
        total_punct += count
    for p, count in unique_puncts.items():
        print(f"{p.replace(' ', '_')}\t{count}\t{round(count/total_punct*100, 2)}")

def add_steinsaltz_possibilities():
    ref_mapping = defaultdict(list)
    with open(f"{DATA}/dataset.csv", "r") as fin:
        c = csv.DictReader(fin)
        for row in c:
            ref_mapping[row['Ref']] += [[row['Word'], row['Punctuation']]]

    fout = open(f"{DATA}/dataset_with_stein.csv", "w")
    c = csv.DictWriter(fout, ['Ref', 'Word', 'Punctuation', 'Possibilities'])
    c.writeheader()
    def action(stein_text, en_tref, he_tref, v):
        nonlocal ref_mapping
        base_ref = en_tref.replace('Steinsaltz on ', '')
        base_text = Ref(base_ref).text(lang='he', vtitle=vtitle_wo_vowels).text
        word_punct_pairs = ref_mapping[base_ref]
        possibilities = extract_steinsaltz_possibilities(base_text, stein_text, word_punct_pairs)
        for poss, (w, punct) in zip(possibilities, word_punct_pairs):
            c.writerow({
                "Ref": base_ref,
                "Word": w,
                "Punctuation": punct,
                "Possibilities": poss
            })

    for title in titles:
        version = VersionSet({"title": f"Steinsaltz on {title}", "language": "he"}).array()[0]
        version.walk_thru_contents(action)
    
    fout.close()

if __name__ == "__main__":
    create_dataset()
    # add_steinsaltz_possibilities()