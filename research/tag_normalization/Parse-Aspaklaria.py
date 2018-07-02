# -*- coding: utf-8 -*-

import os
import re
import unicodecsv as csv
from google.cloud import translate

translate_client = translate.Client()

dirs = [d for d in os.walk(u"/Users/levisrael/sefaria/Aspaklaria/www.aspaklaria.info")]
fnames = [fname for (dirpath, dirnames, filenames) in dirs[1:] for fname in filenames[1:]]
clean_names = [re.sub("\s+", " ", f.replace(".html","").strip()) for f in fnames]

with open("Aspaklaria-Headwords.csv", "w") as csvout:
    csvout = csv.writer(csvout)
    for tag in clean_names:
        translation = translate_client.translate(
            tag,
            target_language='en', source_language='iw')
        csvout.writerow([tag, translation['translatedText']])
