import csv
import re
import django
django.setup()
from sefaria.model import *
from sefaria.system.exceptions import InputError
from data_utilities.dibur_hamatchil_matcher import match_ref

def text_with_seg_numbers(ref):
    if type(ref) == str:
        ref = Ref(ref)
    return re.sub('<.*?>', '', ' '.join([f'{r.normal().split(":")[-1]} {r.text("he", vtitle="Wikisource Talmud Bavli").text}' for r in ref.all_segment_refs() if {r.text("he", vtitle="Wikisource Talmud Bavli").text}]))

def dh_extract_method(comment):
    comment = re.sub('<.*?>', '', comment)
    if '.' in comment and len(comment.split('.')[0]) < 21:
        dh = ' '.join(comment.split('.')[0].split()[:7])
    else:
        dh = ' '.join(comment.split()[2:6])
    return dh

def make_report(index, fname, add_new_links=False):
    if type(index) == str:
        index = library.get_index(index)
    base = index.base_text_titles[0]
    report = []
    for sec in index.all_section_refs():
        section = []
        for seg in sec.all_segment_refs():
            segrow = {'ref': seg.normal(), 'text': seg.text('he').text}
            linkset = seg.linkset()
            linkset = [l for l in linkset if l.type in ['Commentary', 'commentary']]
            if linkset:
                segrow['base ref'] = [r for r in linkset[0].refs if r != segrow['ref']][0]
            else:
                segrow['add/remove'] = 'add'

                if add_new_links:
                    base_tc = Ref(f'{base} {seg.normal().split()[-1].split(":")[0]}').text('he',                                                                                       vtitle='Wikisource Talmud Bavli')
                    base_tokenizer = lambda x: x.split()
                    matches = match_ref(base_tc, seg.text('he'), base_tokenizer, dh_extract_method=dh_extract_method)
                    if matches['matches'][0]:
                        segrow['base ref'] = matches['matches'][0].normal()
                        segrow['base text'] = matches['matches'][0].text('he', vtitle='Wikisource Talmud Bavli').text

            section.append(segrow)

        prev = f'{base} {sec.normal().split()[-1].split(":")[0]}:1'
        for r, row in enumerate(section):
            if 'base ref' in row:
                prev = Ref(row['base ref']).all_segment_refs()[-1]
                row['base text'] = text_with_seg_numbers(row['base ref'])
                row['range length'] = len(Ref(row['base ref']).all_segment_refs())
            else:
                next = 99
                for row2 in section[r+1:]:
                    if 'base ref' in row2:
                        next = Ref(row2['base ref']).all_segment_refs()[0].normal().split()[-1]
                        break
                try:
                    row['base text'] = text_with_seg_numbers(f'{prev}-{next}')
                    row['range length'] = len(Ref(f'{prev}-{next}').all_segment_refs())
                except InputError:
                    row['base text'] = 'reversed order'
                    print(f'{prev}-{next}')
        report += section
    with open(f'{fname}.csv', 'w', encoding='utf-8', newline='') as fp:
        w = csv.DictWriter(fp, fieldnames=['ref', 'text', 'base ref', 'base text', 'range length', 'add/remove'])
        w.writeheader()
        for r in report:
            w.writerow(r)


if __name__ == '__main__':
    path = ['Talmud','Bavli','Rishonim on Talmud','Ritva']
    inds = IndexSet({'categories': {'$all': path}})
    for ind in inds:
        make_report(ind, ind.title, add_new_links=True)

