# -*- coding: utf-8 -*-

# Uses Google Cloud Translate API & Library
# Service account credetials specified in separate file, and put into the environment with, e.g:
# export GOOGLE_APPLICATION_CREDENTIALS="/Users/levisrael/sefaria/Sefaria-Data/research/tag_normalization/Translation Project-5c384ce3ed5a.json"


import unicodecsv as csv
from collections import defaultdict
from google.cloud import translate
from sefaria.system.database import db
from sefaria.utils.hebrew import strip_nikkud, is_hebrew

translate_client = translate.Client()

untranslated_en_tags = []

original_tag_counter = defaultdict(int)
db_sheet_list = db.sheets.find({"status": "public"}, {"tags": 1})
sheet_list = [s for s in db_sheet_list]
for sheet in sheet_list:
    for tag in sheet.get("tags", []):
        original_tag_counter[tag] += 1

sorted_tags = sorted(original_tag_counter, key=original_tag_counter.get, reverse=True)
sorted_en_tags = [t for t in sorted_tags if not is_hebrew(t)]
sorted_he_tags = [t for t in sorted_tags if is_hebrew(t)]

translated_hebrew_tags = defaultdict(list)
for en_tag in sorted_en_tags:
    translation = translate_client.translate(en_tag, target_language='iw', source_language='en')
    he_tag = strip_nikkud(translation['translatedText'])
    if en_tag == he_tag:
        print u"Couldn't translate {}".format(en_tag)
        untranslated_en_tags += [en_tag]
        continue
    print u"{}:{}".format(he_tag, en_tag)
    translated_hebrew_tags[he_tag] += [en_tag]

overall_counts = {he_tag: sum([original_tag_counter[en_tag] for en_tag in translated_hebrew_tags[he_tag]]) for he_tag in translated_hebrew_tags}
ordered_translated_he_terms = sorted(overall_counts, key=overall_counts.get, reverse=True)

with open("translated_and_grouped_tags.csv", "w") as csvout:
    csvout = csv.writer(csvout)
    for he_term in ordered_translated_he_terms:
        csvout.writerow([he_term, overall_counts[he_term]] + translated_hebrew_tags[he_term])

with open("original_hebrew_tags.csv", "w") as csvout:
    csvout = csv.writer(csvout)
    for he_term in sorted_he_tags:
        csvout.writerow([he_term, original_tag_counter[he_term]])

with open("untranslated_english_tags.csv", "w") as csvout:
    csvout = csv.writer(csvout)
    for en_term in untranslated_en_tags:
        csvout.writerow([en_term, original_tag_counter[en_term]])

print "Number of Original English Tags: {}".format(len(sorted_en_tags))
print "Number of Untranslatable English Tags: {}".format(len(untranslated_en_tags))
print "Number of Translated Hebrew Tags: {}".format(len(translated_hebrew_tags))
print "(Number of Original Hebrew Tags: {})".format(len(sorted_he_tags))
