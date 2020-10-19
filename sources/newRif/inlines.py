import json
import re
import django
django.setup()
from rif_utils import tags_map, path, commentaries, main_mefaresh
from tags_fix_and_check import tags_by_criteria, gem_to_num
from sefaria.utils.talmud import section_to_daf
from data_utilities.util import getGematria
from sefaria.model import *
from sefaria.system.exceptions import InputError

for masechet in tags_map:
    if masechet == 'Nedarim': continue
    print(masechet)
    links = []
    with open(path+'/tags/rif_{}.json'.format(masechet)) as fp:
        rif = json.load(fp)
    with open(path+'/tags/mefaresh_{}.json'.format(masechet)) as fp:
        Mmefaresh = json.load(fp)
    with open(path+f'/tags/sg_{masechet}.json') as fp:
        sg = json.load(fp)
    for mefaresh in [1,5,7,8,9]:
        c_title = commentaries[str(mefaresh)]['c_title']
        print(c_title)
        if mefaresh == 9:
            try:
                with open(path+f'/commentaries/json/ravad_{masechet}.json') as fp:
                    ravad = json.load(fp)
            except FileNotFoundError:
                continue

        for page in range(len(rif)):
            tags = tags_by_criteria(masechet, key=lambda x: int(x[1:4])==page, value=lambda x: x['referred text']==mefaresh)
            for tag in tags:
                if tag[0] == '1':
                    data = rif
                    btext = 'Rif'
                elif tag[0] == '2':
                    data = Mmefaresh
                    btext = main_mefaresh(masechet) + ' on Rif'
                elif tag[0] == '3':
                    data = sg
                    btext = 'Shiltei Hagiborim on Rif'
                else:
                    print('problem with first digit', tag)
                    continue

                section = int(tag[4:6])
                label = re.sub(r'[\(\)\[\]@\d ]', '', tags[tag]['original'])
                order = gem_to_num(getGematria(label))
                if mefaresh == 9:
                    with_tag = []
                    for n, par in enumerate(ravad[page]):
                        if par.startswith(label+'] '):
                            with_tag.append(n)
                    if len(with_tag) == 1:
                        order = with_tag[0] + 1
                        ravad[page][order-1] = ravad[page][order-1].replace(label+'] ', '')
                    else:
                        print(f'tag {tag} with {len(with_tag)} relevant tags in ravad')
                        continue

                if int(tag[4:]) > 8999 and tag in data[page][-1]:
                    section = len(data[page]) - 1
                elif tag in data[page][section]:
                    bpage = page
                elif tag in data[page-1][-1]: #when the tag belongs to continous dh from prev. page
                    bpage = page - 1
                    section = len(data[page-1]) - 1
                elif tag in data[page-2][-1]:
                    bpage = page - 2
                    section = len(data[page-2]) - 1
                else:
                    print('tag isnt in the expected place', tag)
                    continue

                data[bpage][section] = data[bpage][section].replace(f'${tag}', f'<i data-commentator="{c_title}" data-label="{label}" data-order="{order}"></i>', 1)
                data[bpage][section] = re.sub('(</i>) +', r'\1', data[bpage][section])
                ref = f'{c_title} {masechet} {section_to_daf(page+1)}:{order}'
                try:
                    if Ref(ref).text('he').text: #did post before
                        links.append({'refs': [f'{btext} {masechet} {section_to_daf(bpage+1)}:{section+1}', ref],
                        'type': 'commentary',
                        'inline_reference': {'data-commentator': c_title, 'data-order': order, 'data-label': label},
                        'generated_by': 'rif inline commentaries'})
                    else:
                        print(f'{tag} ref to null {ref}')
                except InputError: #when running before post
                    links.append({'refs': [f'{btext} {masechet} {section_to_daf(bpage+1)}:{section+1}', ref],
                    'type': 'commentary',
                    'inline_reference': {'data-commentator': c_title, 'data-order': order, 'data-label': label},
                    'generated_by': 'rif inline commentaries'})

        if mefaresh == 9:
            with open(path+'/tags/topost/ravad_{}.json'.format(masechet), 'w') as fp:
                json.dump(ravad, fp)

    with open(path+'/tags/topost/rif_{}.json'.format(masechet), 'w') as fp:
        json.dump(rif, fp)
    with open(path+'/tags/topost/mefaresh_{}.json'.format(masechet), 'w') as fp:
        json.dump(Mmefaresh, fp)
    with open(path+'/tags/topost/SG_{}.json'.format(masechet), 'w') as fp:
        json.dump(sg, fp)
    with open(path+'/tags/topost/inline_links_{}.json'.format(masechet), 'w') as fp:
        json.dump(links, fp)
