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

#
if __name__ == '__main__':
#     import csv
#     from collections import defaultdict, Counter
#     diff = {}
#     parser = argparse.ArgumentParser()
#     parser.add_argument('-t', '--tractate', type=str, help='tractate on which to add punctuation')
#     parser.add_argument('--punctloc', type=str, default=None, help='file location where to find punctuation output. if not specified, defaults to `PUNCT_VTITLE`')
#     parser.add_argument('-c', '--csv', type=str, default=None, help='output punctuated talmud as csv rather than a new version')
#     args = parser.parse_args()
#     mismatches = defaultdict(list)
#     skip = True
#     for tractate in 'Niddah, Bekhorot, Arakhin, Sanhedrin, Menachot, Makkot, Tamid, Bava Metzia, Chullin, Zevachim, Horayot, Temurah, Shevuot, Keritot, Avodah Zarah, Bava Kamma'.split(", "):
#         base_ref = Ref(tractate)
#         csv_dir = args.csv
#         export_as_csv = True
#         segments = base_ref.all_segment_refs()
#         rows = []
#         for segment in segments:
#             punc, voc = segment.text('he', PUNC_VTITLE).text, segment.text('he', VOC_VTITLE).text
#             try:
#                 merged = merge_segment(punc, voc)
#             except AssertionError:
#                 mismatches[tractate].append(f'mismatched length at {segment.normal()}')
#                 merged = voc
#             if export_as_csv:
#                 rows += [{
#                     "Ref": segment.normal(),
#                     "Text": merged
#                 }]
#             else:
#                 merged_tc = segment.text('he', MERGED_VTITLE)
#                 merged_tc.text = merged
#                 merged_tc.save()
#         if export_as_csv:
#             with open(tractate+'.csv', 'w') as fout:
#                 c = csv.DictWriter(fout, ['Ref', 'Text'])
#                 c.writeheader()
#                 c.writerows(rows)
#
# with open('mismatches.csv', 'w') as f:
#     writer = csv.writer(f)
#     for k in mismatches:
#         for row in mismatches[k]:
#             writer.writerow([k, row])

    import csv
    import bleach
    bold_overrides = {}
    for f in ['bold_overrides - overrides.csv', 'overrides - Tamid2.csv']:
        with open(f, 'r') as open_f:
            reader = csv.reader(open_f)
            rows = list(reader)
            for r in rows:
                bold_overrides[r[0]] = r[1]
    from sefaria.helper.normalization import NormalizerComposer
    n = NormalizerComposer(["punctuation"])
    for tractate in 'Niddah, Bekhorot, Arakhin, Sanhedrin, Menachot, Makkot, Tamid, Bava Metzia, Chullin, Zevachim, Horayot, Temurah, Shevuot, Keritot, Avodah Zarah, Bava Kamma'.split(", "):
        base_ref = Ref(tractate)
        export_as_csv = True
        segments = base_ref.all_segment_refs()
        merged = {}
        new_rows = []
        print(tractate)
        with open(f"{tractate}.csv", 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)
            wout_punc = []
            for r, row in enumerate(rows):
                try:
                    ref = Ref(row[0])
                    rows[r][1] = bold_overrides.get(ref.normal(), row[1])
                    wout_punc.append([ref.normal(), n.normalize(rows[r][1]).replace("  ", " ")])
                    tc = TextChunk(ref, lang='he', vtitle="William Davidson Edition - Vocalized Aramaic")
                    tc.text = wout_punc[-1][1]
                    if tc.text != tc._original_text:
                        tc.save()
                except:
                    continue
            with open(f"{tractate}_vocalized+punctuation.csv", 'w') as f:
                writer = csv.writer(f)
                writer.writerows(rows)
            v = Version().load({"title": tractate, "versionTitle": "William Davidson Edition - Vocalized Aramaic"})
            v.versionSource = "https://korenpub.co.il/collections/the-noe-edition-koren-talmud-bavli-1"
            v.versionNotes = "Aramaic from The William Davidson digital edition of the <a href='https://www.korenpub.com/koren_en_usd/koren/talmud/koren-talmud-bavli-no.html'>Koren Noé Talmud</a>, with commentary by <a href='/adin-even-israel-steinsaltz'>Rabbi Adin Even-Israel Steinsaltz</a>. Nikud (vocalization) by Dicta - the Israeli Center for Text Analysis"
            v.save()
                # ., ":?!— and replacing double spaces with single spaces



    # from sefaria.helper.normalization import NormalizerComposer
    # n = NormalizerComposer(["punctuation", "brackets", "cantillation", "maqaf"])
    # from sefaria.utils.hebrew import strip_nikkud, strip_cantillation, sanitize
    # from tqdm import tqdm
    # diff = {}
    # clean = lambda x: sanitize(strip_nikkud(strip_cantillation(x)).replace('\'', '').replace('׳', ''), punctuation=False)
    # bold_issues = []
    # for tractate in 'Niddah, Bekhorot, Arakhin, Sanhedrin, Menachot, Makkot, Tamid, Bava Metzia, Chullin, Zevachim, Horayot, Temurah, Shevuot, Keritot, Avodah Zarah, Bava Kamma'.split(", "):
    #     base_ref = Ref(tractate)
    #     export_as_csv = True
    #     segments = base_ref.all_segment_refs()
    #     merged = {}
    #     new_rows = []
    #     with open(f"{tractate}.csv", 'r') as f:
    #         reader = csv.reader(f)
    #         rows = list(reader)
    #         for r, row in enumerate(rows):
    #             try:
    #                 ref = Ref(row[0])
    #             except:
    #                 continue
    #             wiki = TextChunk(ref, lang='he', vtitle='Wikisource Talmud Bavli').text
    #             temp = n.normalize(clean(row[1]))
    #             finds = re.findall("<big>(.*?)</big>", wiki)
    #             try:
    #                 for x in finds:
    #                     x = n.normalize(clean(bleach.clean(x, strip=True, tags=[])))
    #                     first_word = x.split(" ")[0]
    #                     len_words = x.count(" ")
    #                     pos = temp.split().index(first_word)
    #                     merged[ref.normal()] = ""
    #                     just_found = False
    #                     for i, w in enumerate(row[1].split()):
    #                         if i == pos:
    #                             merged[ref.normal()] += f"<strong><big>{w}"
    #                             if len_words == 0:
    #                                 merged[ref.normal()] += "</big></strong>"
    #                             else:
    #                                 just_found = True
    #                         elif len_words > 0:
    #                             merged[ref.normal()] += w
    #                             len_words -= 1
    #                         elif just_found and len_words == 0:
    #                             merged[ref.normal()] += f"{w}</big></strong>"
    #                             just_found = False
    #                         else:
    #                             merged[ref.normal()] += w
    #                         if i < len(row[1].split()):
    #                             merged[ref.normal()] += " "
    #                     if just_found and len_words == 0:
    #                         merged[ref.normal()] += f"</big></strong>"
    #                         just_found = False
    #                 error = False
    #             except Exception as e:
    #                 bold_issues.append([ref.normal(), row[1], wiki])
    #                 error = True
    #             if error or len(finds) == 0:
    #                 merged[ref.normal()] = row[1]
    #             new_rows += [{
    #                                     "Ref": ref.normal(),
    #                                     "Text": merged[ref.normal()]
    #                                 }]
    #
    #     for segment in tqdm(segments):
    #         txt = TextChunk(Ref(segment.tref), lang='he', vtitle="William Davidson Edition - Aramaic").text
    #         num_words = txt.count(" ")
    #         if abs(num_words - merged[segment.tref].count(" ")) > 5:
    #             diff[segment] = [merged[segment.tref], txt, num_words - merged[segment.tref].count(" ")]
    #     with open(tractate+'2.csv', 'w') as fout:
    #         c = csv.DictWriter(fout, ['Ref', 'Text'])
    #         c.writeheader()
    #         c.writerows(new_rows)
    # with open('num_words.csv', 'w') as f:
    #     writer = csv.writer(f)
    #     writer.writerow(["Vocalized Punctuation", "William Davidson Edition - Aramaic", "Difference in word count"])
    #     for k in diff:
    #         writer.writerow([k, diff[k][0], diff[k][1], diff[k][2]])
    # with open('bold_issues.csv', 'w') as f:
    #     writer = csv.writer(f)
    #     writer.writerow(["Ref", "Vocalized Punctuation", "Wikisource"])
    #     for k in bold_issues:
    #         writer.writerow([k[0], k[1], k[2]])
