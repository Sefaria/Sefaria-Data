import json
import re
import django
django.setup()
from rif_utils import tags_map, path, commentaries, main_mefaresh, maor_godel
from tags_fix_and_check import tags_by_criteria, gem_to_num, save_tags
from sefaria.utils.talmud import section_to_daf
from data_utilities.util import getGematria
from sefaria.model import *
from sefaria.system.exceptions import InputError
from data_utilities.dibur_hamatchil_matcher import match_ref

def find_dh(section):
    dh = re.sub('\[[^\]]*\]|<\/?b>', '', section).split('.')[0]
    return ' '.join(dh.split()[2:10])

def ravad_gittin_links(ravad):
    links = []
    for m, page in enumerate(ravad):
        for n, sec in enumerate(page):
            sec = sec.replace('<b>', '')
            if sec.startswith('['):
                ravad_ref = f"{commentaries['9']['c_title']} Gittin {section_to_daf(m+1)}:{n+1}"
                gemara_ref = re.findall(r'^\[([^\]]*)\]', sec)
                if gemara_ref: gemara_ref = gemara_ref[0]
                else: continue
                if gemara_ref != 'שם':
                    ref = Ref(f'גיטין {gemara_ref}')
                gemara_match = match_ref(ref.text('he'), Ref(ravad_ref).text('he'), base_tokenizer=lambda x: x.split(), dh_extract_method=find_dh)["matches"][0]
                if gemara_match:
                    links.append({"refs": [ravad_ref, gemara_match.tref],
                    "type": "Commentary",
                    "auto": True,
                    "generated_by": 'rif inline commentaries'})
    return links

def find_tag_in_bach(masechet, comment):
    letter_tag = tags_map[masechet]['bach_letter'] + r'\(.\)'
    tag = re.findall(letter_tag, comment)
    if tag:
        return gem_to_num(getGematria(tag[0]))
    else:
        print(f'no tag in bach {masechet}: {comment}')

def sort_tags(tags, masechet, page):
    tags_list = list(tags)
    if (masechet, page) in [('Eruvin', 1), ('Kiddushin', 35)]: #in these page maor and milchemt tags numbered before sg tags
        tags_list = sorted(tags_list, key=lambda x: '6' if x[0]=='3' else x)
    elif (masechet, page) in [('Yevamot', 48)]:
        tags_list = sorted(tags_list, key=lambda x: '6' if x[0]=='4' else x)
    return tags_list

def bach_order(masechet, tags, page, ravad=False):
    #this function uses also for ravad on pesachim
    old = 0
    gap = 0
    orders = []
    with open(path+f'/commentaries/json/bach_{masechet}.json') as fp:
        data = json.load(fp)
    tags_list = sort_tags(tags, masechet, page)
    for tag in tags_list:
        new = gem_to_num(getGematria(tags[tag]['original']))
        if old + 1 == new + gap:
            pass
        elif old == new + gap:
            try:
                if find_tag_in_bach(masechet, data[page][old]) == old: #notice first of old is 1 and the data index from 0
                    gap += 1 #bach has double letter, else there're two refs to the same bach
            except IndexError:
                pass #2 refs to the last comment
        elif old + 1 < new + gap:
            for n in range(44):
                try:
                    if find_tag_in_bach(masechet, data[page][old+n]) == new:
                        gap = old + n + 1 - new
                        break
                except IndexError:
                    print(f'not finding comment with gimatric number {new} in bach {masechet} p. {page}. tag: {tag}')
                    break
        elif old - 21 == new + gap:
            gap += 22
        elif masechet == 'Menachot' and new == 1 and old == 2:
            gap = 22
        elif ravad:
            gap = old + 1 - new
        else:
            print(f'{new} comes after {old} in {masechet} p. {page}')
        old = new + gap
        orders.append(old)
    return orders

def execute(masechtot=tags_map):
    for masechet in masechtot:
        if masechet == 'Nedarim': continue
        print(masechet)
        links = []
        with open(path+'/tags/rif_{}.json'.format(masechet)) as fp:
            rif = json.load(fp)
        with open(path+'/tags/mefaresh_{}.json'.format(masechet)) as fp:
            Mmefaresh = json.load(fp)
        with open(path+f'/tags/sg_{masechet}.json') as fp:
            sg = json.load(fp)
        with open(path+f'/tags/maor_{masechet}.json') as fp:
            maor = json.load(fp)
        with open(path+f'/tags/milchemet_{masechet}.json') as fp:
            milchemet = json.load(fp)
        with open(path+f'/tags/ansh_{masechet}.json') as fp:
            ansh = json.load(fp)
        for mefaresh in [1,2,3,4,5,7,8,9,10]:
            c_title = commentaries[str(mefaresh)]['c_title']
            if mefaresh == 9:
                try:
                    with open(path+f'/commentaries/json/ravad_{masechet}.json') as fp:
                        ravad = json.load(fp)
                except FileNotFoundError:
                    continue
            print(c_title)

            for page in range(len(rif)):
                tags = tags_by_criteria(masechet, key=lambda x: int(x[1:4])==page, value=lambda x: x['referred text']==mefaresh)
                if mefaresh == 3:
                    orders = bach_order(masechet, tags, page)
                elif mefaresh == 10 and masechet == 'Pesachim':
                    orders = bach_order(masechet, tags, page, ravad=True)
                tags_list = sort_tags(tags, masechet, page)
                for tag in tags_list:
                    if tag[0] == '1':
                        data = rif
                        btext = 'Rif'
                    elif tag[0] == '2':
                        data = Mmefaresh
                        btext = main_mefaresh(masechet) + ' on Rif'
                    elif tag[0] == '3':
                        data = sg
                        btext = 'Shiltei HaGiborim on Rif'
                    elif tag[0] == '4':
                        data = maor
                        btext = f'HaMaor {maor_godel(masechet)[0]} on'
                    elif tag[0] == '5':
                        data = milchemet
                        btext = 'Milchemet Hashem on'
                    elif tag[0] == '6':
                        data = ansh
                        btext = commentaries['2']['c_title']
                    else:
                        print('problem with first digit', tag)
                        continue

                    section = int(tag[4:6])
                    label = re.sub(r'[^א-ת]', '', tags[tag]['original'])
                    order = gem_to_num(getGematria(label))
                    if mefaresh == 9:
                        with_tag = []
                        for n, par in enumerate(ravad[page]):
                            if par.replace('<b>', '').startswith(label+'] '):
                                with_tag.append(n)
                        if len(with_tag) == 1:
                            order = with_tag[0] + 1
                            ravad[page][order-1] = ravad[page][order-1].replace(label+'] ', '', 1)
                        else:
                            print(f'tag {tag} with {len(with_tag)} relevant tags in ravad')
                            print(ravad[page],page)
                            continue

                    if mefaresh == 3 or (mefaresh == 10 and masechet == 'Pesachim'): #bach has double letters
                        order = orders.pop(0)

                    if int(tag[4:]) > 8999:
                        if page < len(data) and data[page] and tag in data[page][-1]:
                            section = len(data[page]) - 1
                        else:
                            n = 1
                            while n <= page:
                                if data[page-n] and tag in data[page-n][-1]:
                                    section = len(data[page-n]) - 1
                                    bpage = page - n
                                    break
                                n += 1
                        if n > page:
                            print('tag isnt in the expected place', tag)
                            continue
                    elif len(data[page]) > section and tag in data[page][section]:
                        bpage = page
                    elif masechet == 'Chullin' and tag == '20850100' and tag in data[84][5]:
                        bpage = 84
                        section = 5
                    else:
                        for n in range(1, 4):#when the tag belongs to continous dh from prev. page. max known is 3
                            if tag in data[page-n][-1]:
                                bpage = page - n
                                section = len(data[bpage]) - 1
                                break
                            if n == 3:
                                if len(data[page]) >= section and tag in data[page][section-1]:
                                    bpage = page
                                    section = section - 1
                                elif len(data[page]) >= section and tag in data[page][section-2]:
                                    bpage = page
                                    section = section - 2
                                else:
                                    print('tag isnt in the expected place', tag)

                    data[bpage][section] = data[bpage][section].replace(f'${tag}', f'<i data-commentator="{c_title.replace(" on Rif", "")}" data-label="{label}" data-order="{order}"></i>', 1)
                    data[bpage][section] = re.sub('(</i>) +', r'\1', data[bpage][section])
                    ref = f'{c_title} {masechet} {section_to_daf(page+1)}:{order}'
                    try:
                        if Ref(ref).text('he').text: #did post before
                            links.append({'refs': [f'{btext} {masechet} {section_to_daf(bpage+1)}:{section+1}', ref],
                            'type': 'commentary',
                            'inline_reference': {'data-commentator': c_title.replace(" on Rif", ""), 'data-order': order, 'data-label': label},
                            'generated_by': 'rif inline commentaries'})
                            tags[tag]['used'] = True
                        else:
                            print(f'{tag} ref to null {ref}')
                    except InputError: #when running before post
                        links.append({'refs': [f'{btext} {masechet} {section_to_daf(bpage+1)}:{section+1}', ref],
                        'type': 'commentary',
                        'inline_reference': {'data-commentator': c_title.replace(" on Rif", ""), 'data-order': order, 'data-label': label},
                        'generated_by': 'rif inline commentaries'})
                        print('error', ref)
                save_tags(tags, masechet)

            if mefaresh == 9:
                with open(path+'/tags/topost/ravad_{}.json'.format(masechet), 'w') as fp:
                    json.dump(ravad, fp)
                if masechet == 'Gittin':
                    links += ravad_gittin_links(ravad)

        with open(path+'/tags/topost/rif_{}.json'.format(masechet), 'w') as fp:
            json.dump(rif, fp)
        with open(path+'/tags/topost/mefaresh_{}.json'.format(masechet), 'w') as fp:
            json.dump(Mmefaresh, fp)
        with open(path+'/tags/topost/SG_{}.json'.format(masechet), 'w') as fp:
            json.dump(sg, fp)
        with open(path+'/tags/topost/inline_links_{}.json'.format(masechet), 'w') as fp:
            json.dump(links, fp)
        with open(path+'/tags/topost/maor_{}.json'.format(masechet), 'w') as fp:
            json.dump(maor, fp)
        with open(path+'/tags/topost/milchemet_{}.json'.format(masechet), 'w') as fp:
            json.dump(milchemet, fp)
        with open(path+'/tags/topost/ansh_{}.json'.format(masechet), 'w') as fp:
            json.dump(ansh, fp)

if __name__ == '__main__':
    execute(['Bava Batra'])
