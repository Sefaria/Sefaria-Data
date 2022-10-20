# -*- coding: utf-8 -*-

import django

django.setup()

import roman
import statistics
import re
import csv
from sefaria.model import *


def clean_text(german_text):
    german_text = str(german_text)
    text_array = re.sub(r"\[|\]|\{|\}", "", german_text)
    return text_array


def get_german_text(talmud_ref):
    german_text = talmud_ref.text('en', vtitle='Talmud Bavli. German trans. by Lazarus Goldschmidt, 1929 [de]')
    german_text = german_text.text
    german_text = clean_text(german_text)
    return german_text


mishnah_refs = [
    "Mishnah Shabbat 3:4",
    "Mishnah Shabbat 11:2",
    "Mishnah Shabbat 18:2",
    "Mishnah Eruvin 1:10",
    "Mishnah Pesachim 4:4",
    "Mishnah Pesachim 7:2",
    "Mishnah Pesachim 7:3",
    "Mishnah Pesachim 10:9",
    "Mishnah Yoma 1:3",
    "Mishnah Yoma 3:1",
    "Mishnah Yoma 3:4",
    "Mishnah Yoma 3:5",
    "Mishnah Yoma 5:6",
    "Mishnah Sukkah 1:10",
    "Mishnah Sukkah 3:11",
    "Mishnah Sukkah 5:2",
    "Mishnah Sukkah 5:3",
    "Mishnah Sukkah 5:4",
    "Mishnah Sukkah 5:8",
    "Mishnah Beitzah 4:7",
    "Mishnah Beitzah 5:7",
    "Mishnah Taanit 1:2",
    "Mishnah Moed Katan 1:8",
    "Mishnah Moed Katan 3:2",
    "Mishnah Moed Katan 3:6",
    "Mishnah Moed Katan 3:8",
    "Mishnah Yevamot 3:2",
    "Mishnah Yevamot 3:3",
    "Mishnah Yevamot 3:6",
    "Mishnah Yevamot 3:7",
    "Mishnah Yevamot 6:2",
    "Mishnah Yevamot 8:2",
    "Mishnah Yevamot 9:6",
    "Mishnah Yevamot 12:2",
    "Mishnah Yevamot 13:5",
    "Mishnah Yevamot 13:13",
    "Mishnah Nedarim 2:2",
    "Mishnah Nedarim 8:4",
    "Mishnah Nazir 6:8",
    "Mishnah Sotah 9:2",
    "Mishnah Gittin 4:2",
    "Mishnah Gittin 8:3",
    "Mishnah Gittin 8:10",
    "Mishnah Gittin 9:8",
    "Mishnah Kiddushin 4:14",
    "Mishnah Bava Kamma 4:9",
    "Mishnah Bava Metzia 4:12",
    "Mishnah Bava Metzia 7:10",
    "Mishnah Bava Metzia 10:5",
    "Mishnah Bava Batra 8:8",
    "Mishnah Bava Batra 10:2",
    "Mishnah Sanhedrin 7:11",
    "Mishnah Makkot 1:3",
    "Mishnah Makkot 1:5",
    "Mishnah Makkot 2:7",
    "Mishnah Makkot 3:11",
    "Mishnah Shevuot 3:3",
    "Mishnah Avodah Zarah 4:4",
    "Mishnah Zevachim 9:7",
    "Mishnah Zevachim 13:5",
    "Mishnah Zevachim 14:5",
    "Mishnah Menachot 1:3",
    "Mishnah Menachot 1:4",
    "Mishnah Menachot 10:5",
    "Mishnah Menachot 10:9",
    "Mishnah Chullin 2:3",
    "Mishnah Chullin 6:6",
    "Mishnah Bekhorot 4:4",
    "Mishnah Bekhorot 7:2",
    "Mishnah Bekhorot 7:5",
    "Mishnah Bekhorot 8:6",
    "Mishnah Arakhin 8:7",
    "Mishnah Arakhin 9:4",
    "Mishnah Temurah 6:5",
    "Mishnah Keritot 1:2",
    "Mishnah Keritot 4:2",
    "Mishnah Keritot 5:3",
    "Mishnah Meilah 4:3",
    "Mishnah Tamid 3:9"
]

print("german_mishnah|link_mishnah_ref|talmud_ref|german_text")
for each_ref in mishnah_refs:
    # pass ref obj
    ls = LinkSet(Ref(each_ref))
    for link in ls:
        if link.type == 'mishnah in talmud':
            refs = link.refs
            mishnah_ref, talmud_ref = refs if "Mishnah" in refs[0] else reversed(refs)
            german_text = get_german_text(Ref(talmud_ref))
            if german_text:
                print(f"{each_ref}|{mishnah_ref}|{talmud_ref}|{german_text}")
            else:
                print(f"{each_ref}|{mishnah_ref}|{talmud_ref}|{german_text}")

