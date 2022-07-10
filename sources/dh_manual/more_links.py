import csv
import re
import django
django.setup()
from sefaria.model import *
from data_utilities.dibur_hamatchil_matcher import match_ref

def dh_extract_method(comment):
    comment = re.sub('<.*?>', '', comment)
    if '.' in comment and len(comment.split('.')[0]) < 21:
        dh = ' '.join(comment.split('.')[0].split()[:7])
    else:
        dh = ' '.join(comment.split()[2:6])
    return dh

def find_more_links(index, return_all=False):
    if type(index) == str:
        index = library.get_index(index)
    base = index.base_text_titles[0]
    report = []
    all = []
    for seg in index.all_segment_refs():
        linkset = seg.linkset()
        linkset = [l for l in linkset if l.type in ['Commentary', 'commentary']]
        if not linkset:
            segrow = {'ref': seg.normal(), 'text': seg.text('he').text}
            base_tc = Ref(f'{base} {seg.normal().split()[-1].split(":")[0]}').text('he', vtitle='Wikisource Talmud Bavli')
            base_tokenizer = lambda x: x.split()
            matches = match_ref(base_tc, seg.text('he'), base_tokenizer, dh_extract_method=dh_extract_method)
            if matches['matches'][0]:
                segrow['base ref'] = matches['matches'][0].normal()
                segrow['base text'] = matches['matches'][0].text('he', vtitle='Wikisource Talmud Bavli').text
            report.append(segrow)
    with open(f'{index.title}.csv', 'w', encoding='utf-8', newline='') as fp:
        w = csv.DictWriter(fp, fieldnames=['ref', 'text', 'base ref', 'base text'])
        w.writeheader()
        for r in report:
            w.writerow(r)

if __name__ == '__main__':
    for mas in ['Nedarim', 'Eruvin', 'Avodah Zarah']:
        find_more_links(f'Ritva on {mas}')


