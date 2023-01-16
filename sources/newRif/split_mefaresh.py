import re
from functools import partial
from linking_utilities.parallel_matcher import ParallelMatcher
from sources.functions import getGematria
from rif_gemara_matcher_masoret import base_tokenizer
from rif_utils import path, tags_map

def fix_word_index(text: str, x: int, base_tokenizer):
    y = x
    z = len(base_tokenizer(' '.join(text.split()[:y]))) - x
    while z < 0:
        y -= z
        z = len(base_tokenizer(' '.join(text.split()[:y]))) - x
    return y

def check_sequence(shut):
    pre_daf, pre_amud = 0, 2
    for page in re.findall(r'\n[^\n]*(דף [א-פ][א-ט]{0,1} עמוד [אב])\n\n[^\n]*\1\n', shut):
        daf, amud = re.findall('דף ([א-פ][א-ט]{0,1}) עמוד ([אב])', page)[0]
        daf, amud = getGematria(daf), getGematria(amud)
        if (daf != pre_daf + 1 and amud == 1) or (daf != pre_daf and amud == 2):
            print('daf sequence {} after {}'.format(daf, pre_daf))
        if amud * pre_amud != 2:
            print('page sequence in {} {}'.format(daf, amud))
        pre_daf, pre_amud = daf, amud

def find_match(data, shut, masechet):
    newdata = ''
    matcher = ParallelMatcher(partial(base_tokenizer, masechet=masechet), verbose=False)
    shut = re.split(r'\n[^\n]*דף [א-פ][א-ט]{0,1} עמוד [אב]\n\n[^\n]* דף [א-פ][א-ט]{0,1} עמוד [אב]\n', shut)[1:]
    for n in range(len(shut)-1):
        text_to_find = ' '.join(shut[n].split()[-15:] + shut[n+1].split()[:15])
        text_search_in = data[:11000]
        match_list = matcher.match([(text_search_in, 'data'), (text_to_find, 'shut')], return_obj=True)
        try:
            best_match = [match for match in match_list if match.score == max([item.score for item in match_list])]
            match_location = best_match[0].a.location if best_match[0].a.mesechta == 'data' else best_match[0].b.location
            if match_location == (1730, 1771): #ad hocs
                best_match = [match_list[1]]
                print('ad hoc ketubot')
            elif match_location == (798, 813):
                best_match = [match_list[2]]
                print('ad hoc gittin')
            elif match_location == (193, 201):
                best_match = [match_list[2]]
                print('ad hoc sanhedrin')
            elif match_location == (66, 78):
                best_match = [match_list[2]]
                print('ad hoc chulin')
            match_location = best_match[0].a.location if best_match[0].a.mesechta == 'data' else best_match[0].b.location
        except IndexError:
            print('no match', text_to_find, 'in', text_search_in[:100])
            break
        match_location = [fix_word_index(text_search_in, a, partial(base_tokenizer, masechet=masechet)) for a in match_location]
        #now finding just the start of the second page
        matched_text = ' '.join(text_search_in.split()[match_location[0]:match_location[0]+35]) #+35 just for confidence
        start_shut = ' '.join(shut[n+1].split()[:15])
        start_match_list = matcher.match([(matched_text, 'data'), (start_shut, 'shut')], return_obj=True)
        try:
            start_match_location = start_match_list[0].a.location if start_match_list[0].a.mesechta == 'data' else start_match_list[0].b.location
            location = match_location[0] + start_match_location[0]
            newdata += ' '.join(data.split()[:location]) + ' @@ '
            data = ' '.join(data.split()[location:])
        except IndexError:
            print('no match2', matched_text, start_match_list, start_shut, len(text_search_in), text_search_in[:100], match_location, best_match[0].score)
            break
    if len(data) > 11000:
        print('extra in last page')
    newdata += data
    return newdata

for masechet in tags_map:
    try:
        with open(path+'/Mefaresh/shut/{}.txt'.format(masechet), encoding='utf-8') as fp:
            shut = fp.read()
    except:
        continue
    print(masechet)
    mefresh = [mef for mef in ['Ran', 'Nimmukei Yosef', 'Rabbenu Yehonatan of Lunel'] if tags_map[masechet][mef] == 'Digitized'][0]
    with open(path+'/Mefaresh/{}_{}.txt'.format(mefresh, masechet), encoding='utf-8') as fp:
        data = fp.read()
    check_sequence(shut)
    data = find_match(data, shut, masechet)
    with open(path+'/Mefaresh/splited/{}.txt'.format(masechet), 'w', encoding='utf-8') as fp:
        fp.write(data)
