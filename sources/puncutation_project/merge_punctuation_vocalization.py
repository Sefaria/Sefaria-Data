# encoding=utf-8

import re
import sys
import django
import argparse
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
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--tractate', type=str, help='tractate on which to add punctuation')
    parser.add_argument('--punctloc', type=str, default=None, help='file location where to find punctuation output. if not specified, defaults to `PUNCT_VTITLE`')
    parser.add_argument('-c', '--csv', type=str, default=None, help='output punctuated talmud as csv rather than a new version')
    args = parser.parse_args()
    base_ref = Ref(args.book_title)
    csv_dir = args.csv
    export_as_csv = csv_dir is not None
    segments = base_ref.all_segment_refs()
    rows = []
    for segment in segments:
        punc, voc = segment.text('he', PUNC_VTITLE).text, segment.text('he', VOC_VTITLE).text
        try:
            merged = merge_segment(punc, voc)
        except AssertionError:
            print(f'mismatched length at {segment.normal()}')
            merged = voc
        if export_as_csv:
            rows += [{
                "Ref": segment.normal(),
                "Text": merged
            }]
        else:
            merged_tc = segment.text('he', MERGED_VTITLE)
            merged_tc.text = merged
            merged_tc.save()
    if export_as_csv:
        with open(csv_dir, 'w') as fout:
            c = csv.DictWriter(fout, ['Ref', 'Text'])
            c.writeheader()
            c.writerows(rows)
