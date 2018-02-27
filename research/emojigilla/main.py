# -*- coding: utf-8 -*-
from sefaria.model import *
from sefaria.utils.hebrew import strip_cantillation
from sources.functions import post_text
import bleach
import re

prefixes = [u"",u"בכ",u"וב",u"וה",u"וכ",u"ול",u"ומ",u"וש",u"כב",u"ככ",u"כל",u"כמ",u"כש",u"לכ",u"מב",u"מה",u"מכ",u"מל",u"מש",u"שב",u"שה",u"שכ",u"של",u"שמ",u"ב",u"כ",u"ל",u"מ",u"ש",u"ה",u"ו"];
emoji_map = {
    u"אחשורוש": u"👑",
    u"אסתר": u"👰",
    u"מרדכי": u"👳",
    u"המן": u"👺",
    u"זרש": u"👹",
    u"ושתי": u"🙅‍️️",
    u"חרבונה": u"😎",
}

bigtan_vteresh_str = u"בִּגְתָ֨ן וָתֶ֜רֶשׁ"
bigtan_vteresh_emoji = u"👬"


def tokenizer(base_str, clean=False):
    base_str = base_str.strip()
    if clean:
        base_str = base_str.replace(u"׀", u"$$$")
        base_str = bleach.clean(base_str, tags=[], strip=True)
        base_str = strip_cantillation(base_str, strip_vowels=True)
    base_str = re.sub(ur'־',u' *־* ',base_str)
    word_list = re.split(ur"\s+", base_str)
    return word_list

def rebuild_tokenized_text(word_list):
    s = u" ".join(word_list)
    s = s.replace(u' *־* ', ur'־')
    s = s.replace(u'$$$', u'׀')
    return s

def replace_names(s, ref):
    words_to_replace = []
    for name, replacer in emoji_map.items():
        for p in prefixes:
            cleaned_pasuk = tokenizer(s, True)
            for iw, w in enumerate(cleaned_pasuk):
                if w == p+name:
                    words_to_replace += [{"name": name, "prefix": p, "word_num": iw}]
    tokenized_pasuk = tokenizer(s, False)
    for to_replace in words_to_replace:
        p = to_replace["prefix"]
        tokenized_pasuk[to_replace["word_num"]] = u"{}{}".format(u"{}-".format(p) if len(p) > 0 else u"", emoji_map[to_replace["name"]])  # u"[[{}]]".format(to_replace["form"])
    new_pasuk = rebuild_tokenized_text(tokenized_pasuk)
    if ref == u"2:21":
        new_pasuk = new_pasuk.replace(bigtan_vteresh_str, bigtan_vteresh_emoji)
    return new_pasuk


ref = "Esther"
versionTitle = "Megillat Esther - Purim Edition!!"
versionSource = "https://www.sefaria.org"
language = "he"
oldVersionTitle = "Tanach with Ta'amei Hamikra"

ja = Ref(ref).text(language, oldVersionTitle).ja().array()
for iperek, perek in enumerate(ja):
    print "Emojifying Perek {}".format(iperek)
    for ipasuk, pasuk in enumerate(perek):
        ja[iperek][ipasuk] = replace_names(pasuk, u"{}:{}".format(iperek+1,ipasuk+1))

post = True
if post:
    resp = post_text(ref, {
        "versionTitle": versionTitle,
        "versionSource": versionSource,
        "language": language,
        "text": ja,
    })
    print resp

