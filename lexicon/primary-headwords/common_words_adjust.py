# -*- coding: utf-8 -*-

import django
django.setup()
import unicodecsv as csv
from sefaria.system.database import db
from sefaria.model import *

def create_Word_form(word_form_str, headword, lexicon, primaryH):
    wordform_obj = WordForm({
        "form": word_form_str,
        "c_form": word_form_str,
        "generated_by": "adjust_most_common_talmud_words",
        "lookups": [
            {
                "headword": headword,
                "parent_lexicon": lexicon
            }
        ]
    })
    if primaryH:
        wordform_obj.lookups[0]["primary"] = True
    return wordform_obj.save()

with open("most_common_words_and_lexicon_entries_revised.csv") as csvfile:
    reader = csv.DictReader(csvfile)
    word_form_str = ""
    for i, row in enumerate(reader, 2):
        headword, lexicon = [row[k] for k in ('Headword', 'Lexicon')]
        primaryH, addH, deleteH = [bool(row[k]) for k in ('Primary', 'For Addition', 'For Deletion')]
        if len(row["Common Word"]):
            word_form_str = row["Common Word"]
        print("{}) {}-{}-{} [p{}, a{}, d{}]".format(i, word_form_str, headword, lexicon, primaryH, addH, deleteH))
        query = { "$or": [{"c_form": word_form_str}, {"form": word_form_str}],
                  "lookups": { "$elemMatch": { "headword": headword, "parent_lexicon": lexicon } } }
        if addH or primaryH:
            print("{}-{}-{} being added ({} {})".format(word_form_str, headword, lexicon, "New" if addH else "", "Primary" if primaryH else ""))
            form = create_Word_form(word_form_str, headword, lexicon, primaryH)
        elif deleteH:
            print("{}-{}-{} being deleted:".format(word_form_str, headword, lexicon))
            wfset = WordFormSet(query)
            for wf in wfset:
                len_lookups = len(wf.lookups)
                wf.lookups = [x for x in wf.lookups if x["headword"] != headword or x["parent_lexicon"] != lexicon]
                len_lookups_adj = len(wf.lookups)
                print("*     Original lookups: {} | Lookups removed {}".format(len_lookups, len_lookups-len_lookups_adj))
                if len_lookups_adj > 0:
                    print("*     saving word form")
                    try:
                        wf.save()
                    except:
                        pass
                else:
                    print("*     deleting word form")
                    try:
                        wf.delete()
                    except:
                        pass


