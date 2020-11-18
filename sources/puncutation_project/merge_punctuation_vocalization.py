# encoding=utf-8

import re
import sys
import django
django.setup()
from sefaria.model import *

PUNC_VTITLE = "William Davidson Edition - Aramaic Punctuated"
VOC_VTITLE = "William Davidson Edition - Vocalized Aramaic"
MERGED_VTITLE = "William Davidson Edition - Vocalized Punctuated Aramaic"


def get_punctuation_regex():
    punc_list = ['?!', '?', '!', ':', '.', ',']
    return re.compile(rf'(")?({"|".join(re.escape(p) for p in punc_list)})$')


"""
Here's what we do:
For `standard` punctuation - first create a new string without dashes from the punctuated segment.
Now, look for easy punctuation in a word and add to the end of the equivalent word in the vocalized version.
Then we'll look for opening quotes and stick them at the beginning.
Last, we'll get the indices of the dash, and insert them to the correct location
"""


def merge_segment(punctuated: str, vocalized: str) -> str:
    punc_no_dash = punctuated.replace('—', '')
    vocal_split, punc_no_dash_split = vocalized.split(), punc_no_dash.split()

    assert len(vocal_split) == len(punc_no_dash.split())

    punc_regex = get_punctuation_regex()
    for i, word in enumerate(punc_no_dash_split):
        punc_mark = punc_regex.search(word)
        if punc_mark:
            quote = '"' if punc_mark.group(1) else ''
            vocal_split[i] = f'{vocal_split[i]}{quote}{punc_mark.group(2)}'
        if re.match(r'^"', word):
            vocal_split[i] = f'"{vocal_split[i]}'
        if re.search(r'"$', word):
            vocal_split[i] = f'{vocal_split[i]}"'

    dash_indices = [i for i, x in enumerate(punctuated.split()) if x == '—']
    for i in dash_indices:
        vocal_split.insert(i, '—')
    return ' '.join(vocal_split)


if __name__ == '__main__':
    try:
        book_title = sys.argv[1]
    except IndexError:
        print("Please add name of Tractate")
        sys.exit(0)
    base_ref = Ref(book_title)
    segments = base_ref.all_segment_refs()
    for segment in segments:
        punc, voc = segment.text('he', PUNC_VTITLE).text, segment.text('he', VOC_VTITLE).text
        try:
            merged = merge_segment(punc, voc)
        except AssertionError:
            print(f'mismatched length at {segment.normal()}')
            merged = voc
        merged_tc = segment.text('he', MERGED_VTITLE)
        merged_tc.text = merged
        merged_tc.save()
