#encoding=utf-8
import django
django.setup()
from sefaria.model import *
import codecs
from data_utilities.dibur_hamatchil_matcher import *
from sources.functions import UnicodeReader
with codecs.open("results - results.csv", encoding='utf-8') as f:
    lines = list(f)
    f2 = codecs.open("new.csv", 'w', encoding='utf-8')
    for row in lines:
        ref, ten_words, blank, full_text = row.split(",")
        if ref.find(":") == -1: #just a daf
            ref = "Yevamot "+ref
            base_text = TextChunk(Ref(ref), lang='he')
            match_results = match_ref(base_text, [full_text], lambda x: x.split(), dh_extract_method=lambda x: " ".join(x.split()[0:5]))["matches"][0]
            print match_results
            match_results = match_results.normal() if match_results else "None"
            f2.write(u"{},{}\n".format(match_results, full_text))
        else:
            f2.write(u"{},{}\n".format(ref, full_text))

