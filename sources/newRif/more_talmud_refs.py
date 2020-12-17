import django
django.setup()
from sefaria.model import *
from research.mesorat_hashas_sefaria.mesorat_hashas import ParallelMatcher
from rif_utils import path, tags_map, unite_ref_pages, hebrewplus
from sefaria.utils.talmud import daf_to_section
import re
import json
import csv
from rif_gemara_matcher_masoret import open_rashei_tevot
from scoremanager import ScoreManager

A=0
Y, N = 0, 0
REPORTY, REPORTN = [], []

def base_tokenizer(string):
    string = re.sub('<i class="footnote">[^<]*<\/i>|\*|<[^>]*>', '', string)
    string = hebrewplus(string, '"')
    return open_rashei_tevot(string).split()

def find_talmud(item, prev, next, include_prev=False):
    global Y, N
    #print(prev, next)
    prev_daf, next_daf = daf_to_section(prev.split()[-1].split(':')[0]), daf_to_section(next.split()[-1].split(':')[0])
    if prev_daf > next_daf:
         N += 1
         return []
    prev, next = Ref(prev).context_ref(), Ref(next).context_ref()
    if prev.book != next.book:
        N += 1
        return []
    if prev != next:
        next = next.prev_section_ref()
        if not include_prev and prev != next:
            prev = prev.next_section_ref()
    if prev == next:
        talmud_ref = prev.tref
    else:
        talmud_ref = f'{prev.tref}-{next.tref.split()[-1]}'
    rif_ref = item.tref
    score_manager = ScoreManager("words_dict.json")
    matcher = ParallelMatcher(base_tokenizer, verbose=False, calculate_score=score_manager.get_score)
    links = []

    #print(talmud_ref, rif_ref)
    match_list = matcher.match([talmud_ref, rif_ref], return_obj=True, vtitle_list=['Wikisource Talmud Bavli', None])
    if match_list:
        max_score = max([item.score for item in match_list])
        match_list = [item for item in match_list if item.score == max_score]
        match_list = [item.a.ref if 'Rif' not in item.a.mesechta else item.b.ref for item in match_list]
        if len(match_list) > 1:
            match_list = unite_ref_pages(match_list)
        for item in match_list:
            if type(item) != str:
                item = item.tref
            links.append([{
            "refs": [rif_ref, item],
            "type": "Commentary",
            "auto": True,
            "generated_by": 'rif gemara matcher'
            }])
            REPORTY.append({'rif_ref': rif_ref, 'rif text': Ref(rif_ref).text('he').text, 'gemara ref': item, 'gemara text': Ref(item).text('he').text})
        Y+=1
    else:
        N+=1
        REPORTN.append({'ref': rif_ref, 'text': Ref(rif_ref).text('he').text, 'talmud_ref': talmud_ref})
    return links

def index_missings(index):
    #returns list of trefs and Refs - Ref is a Ref without lmud link, tres is talmud link
    refs_missings = []
    all_refs = [segment for segment in index.all_segment_refs() if segment.text('he').text]
    for segment in all_refs:
        links = [link for link in segment.linkset() if link.generated_by == 'rif gemara matcher']
        if links:
            tref = links[-1].refs[1]
            if Ref(tref).is_bavli():
                refs_missings.append(tref)
        else:
            refs_missings.append(segment)
    return refs_missings

def create_links(masechet):
    links = []
    index = library.get_index(f'Rif {masechet}')
    index.versionState().refresh()
    refs_missings = index_missings(index)
    talmud = library.get_index(masechet)
    prev = talmud.all_section_refs()[0].tref
    for n, item in enumerate(refs_missings):
        if isinstance(item, str):
            prev = item
        elif isinstance(item, Ref):
            for x in refs_missings[n:]:
                if isinstance(x, str):
                    next = x
                    break
                next = talmud.all_section_refs()[-1].tref
            links += find_talmud(item, prev, next)
    return links

def execute(masechtot=tags_map):
    global A
    for masechet in masechtot:
        print(masechet)
        links = create_links(masechet)
        A+=len(links)
        with open(path+'/gemara_links/more_{}.json'.format(masechet), 'w') as fp:
            json.dump(links, fp)

if __name__ == '__main__':
    execute()
    print(Y, N, Y/(N+Y))
    with open(path+'/reporty.csv', 'w', encoding='utf-8', newline='') as file:
        awriter = csv.DictWriter(file, fieldnames=['rif_ref', 'rif text', 'gemara ref', 'gemara text'])
        awriter.writeheader()
        for item in REPORTY: awriter.writerow(item)
    with open(path+'/reportn.csv', 'w', encoding='utf-8', newline='') as file:
        awriter = csv.DictWriter(file, fieldnames=['ref', 'text', 'talmud_ref'])
        awriter.writeheader()
        for item in REPORTN: awriter.writerow(item)
    print(A)
