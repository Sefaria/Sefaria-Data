# -*- coding: utf-8 -*-
from sefaria.model import *
from sefaria.utils.hebrew import strip_cantillation
from sources.functions import post_text
import bleach
import re, codecs, csv
import base64

prefixes = ["", "בכ", "וב", "וה", "וכ", "ול", "ומ", "וש", "כב", "ככ", "כל", "כמ", "כש", "לכ", "מב",
            "מה", "מכ", "מל", "מש", "שב", "שה", "שכ", "של", "שמ", "ב", "כ", "ל", "מ", "ש", "ה", "ו"]
emoji_map = {}

words_to_emojis = []


def lookup_shoresh(w, ref):
    # in both - cant
    # only second - cant
    # only first - nikud
    # remove all non-Hebrew non-nikud characters (including cantillation and sof-pasuk)
    w = re.sub(r"[A-Za-z׃׀־]", "", w)
    lexicon = "BDB Augmented Strong"
    wf = WordForm().load({"form": w, "refs": re.compile("^" + ref + "$")})
    if wf:
        return [x["headword"] for x in [x for x in wf.lookups if x["lexicon"] == lexicon]]

def lookup_shoresh(w, ref):
    # in both - cant
    # only second - cant
    # only first - nikud
    #remove all non-Hebrew non-nikud characters (including cantillation and sof-pasuk)
    w = strip_cantillation(w, strip_vowels=False)
    w = re.sub(r"[A-Za-z׃׀־]", "", w)
    lexicon = "BDB Augmented Strong"
    try:
        wf = WordForm().load({"form": w, "refs": re.compile("^" + ref + "$")})
    except Exception:
        return None
    if wf:
        return [x["headword"] for x in [x for x in wf.lookups if x["lexicon"] == lexicon]]

def tokenizer(base_str, clean=False):
    base_str = base_str.strip()
    if clean:
        base_str = base_str.replace("׀", "$$$")
        base_str = bleach.clean(base_str, tags=[], strip=True)
        base_str = strip_cantillation(base_str, strip_vowels=False)
    base_str = re.sub(r'־', ' *־* ', base_str)
    word_list = re.split(r"\s+", base_str)
    return word_list


def rebuild_tokenized_text(word_list):
    s = " ".join(word_list)
    s = s.replace(' *־* ', r'־')
    s = s.replace('$$$', '׀')
    return s


def replace_with_base64(s, ref):
    words_to_replace = []
    cleaned_pasuk = tokenizer(s, True)
    for iw, word in enumerate(cleaned_pasuk):
        prefix = ''
        shoresh = lookup_shoresh(word, ref)
        if shoresh:
            shoresh = shoresh[0]
        else:
            print(word)
        if any(word_to_emoji == shoresh for word_to_emoji in words_to_emojis):
            nikudless_word = strip_cantillation(word, True)[:-1]
            nikudless_shoresh = strip_cantillation(shoresh, True)[:-1]
            if len(nikudless_shoresh) > len(nikudless_word):
                nikudless_shoresh = nikudless_shoresh[:len(nikudless_word)]
            if nikudless_word != nikudless_shoresh:
                prefix_index = nikudless_word.find(nikudless_shoresh)
                if prefix_index != -1 and any(p == nikudless_word[:prefix_index] for p in prefixes):
                    nikud_prefix_index = word.find(shoresh[0], prefix_index)
                    prefix = word[:nikud_prefix_index]
            words_to_replace += [{"name": word, "shoresh": shoresh, "prefix": prefix, "word_num": iw}]
    tokenized_pasuk = tokenizer(s, False)
    for to_replace in words_to_replace:
        p = to_replace["prefix"]
        tokenized_pasuk[to_replace[
            "word_num"]] = '<span class="purim-emoji">' \
                           '{}<img  src="data:image/png;base64,{}" /> </span>'.format(
            "{}-".format(p) if len(p) > 0 else "", emoji_map[to_replace["shoresh"]])
    new_pasuk = rebuild_tokenized_text(tokenized_pasuk)
    if new_pasuk[-1] != '׃':
        new_pasuk += '׃'
    return new_pasuk


with codecs.open("EmojiGilla Dictionary.csv", 'rb') as csvfile:
    csv_reader = csv.reader(csvfile, delimiter=',')
    for line in csv_reader:
        hebrew_word = line[0].strip()
        perek = line[3].strip()
        pasuk = line[4].strip()
        ref = "Esther {}:{}".format(perek, pasuk)
        shoresh = lookup_shoresh(hebrew_word, ref)[0]
        words_to_emojis.append(shoresh)
        with open("./emojis/" + shoresh + '.png', 'r') as word_img:
            image_read = word_img.read()
            emoji_map[shoresh] = base64.encodestring(image_read)

ref = "Esther"
versionTitle = "Megillat Esther - Purim Edition!!"
versionSource = "https://www.sefaria.org"
language = "he"
oldVersionTitle = "Tanach with Nikkud"

ja = Ref(ref).text(language, oldVersionTitle).ja().array()
for iperek, perek in enumerate(ja):
    print("Emojifying Perek {}".format(iperek))
    for ipasuk, pasuk in enumerate(perek):
        ja[iperek][ipasuk] = replace_with_base64(pasuk, "Esther {}:{}".format(iperek + 1, ipasuk + 1))

post = True
if post:
    print("Posting")
    resp = post_text(ref, {
        "versionTitle": versionTitle,
        "versionSource": versionSource,
        "language": language,
        "text": ja,
    }, server='https://www.sefaria.org', weak_network=True)
    print(resp)
