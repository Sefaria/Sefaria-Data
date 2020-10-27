import requests
import django
import json
import csv
import re
django.setup()
from os.path import isfile
from sefaria.model import *
from sources import functions
from sefaria.utils.talmud import daf_to_section, section_to_daf
from rif_utils import tags_map, path, get_hebrew_masechet, main_mefaresh, commentaries, maor_tags, maor_godel
from tags_fix_and_check import tags_by_criteria

TS = 0
LS = 0

def housekeep(string):
    string = re.sub(r'\s', ' ', string)
    string = re.sub(' +', ' ', string)
    string = re.sub(r' ([\)\]:\.])', r'\1 ', string)
    string = re.sub(r'([\(\[]) ', r' \1', string)
    string = re.sub('(<sup.*?/i>) ', r' \1', string)
    string = re.sub(' +', ' ', string)
    return string

def post_rif(masechtot=list(tags_map), index=True, text='csv', links=True, server = 'http://localhost:8000'):
    global TS
    global LS
    for masechet in masechtot:
        title = 'Rif ' + masechet
        if index:
            with open(f'{path}/alts/{masechet}.json') as fp:
                alts = json.load(fp)
            ind = requests.get("https://www.sefaria.org/api/v2/raw/index/Rif_" + masechet).json()
            #ind['schema'] = schema.serialize()
            ind['alt_structs'] = alts
            functions.post_index(ind, server = server)
        if links:
            with open(path+'/gemara_links/{}.json'.format(masechet)) as fp:
                data = json.load(fp)
            data = [link for lis in data for link in lis]
            functions.post_link(data, server = server)
            LS+=len(data)
        if text:
            if text == 'csv':
                with open(f'{path}/rif_gemara_refs/rif_{masechet}.csv', encoding='utf-8', newline='') as fp:
                    data = list(csv.DictReader(fp))
                    ja = []
                    last_page = daf_to_section(data[-1]['page.section'].split(':')[0])
                    for n in range(last_page):
                        ja.append([housekeep(row['content']) for row in data if row['page.section'].split(':')[0] == section_to_daf(n+1)])
            else:
                with open(path+'/tags/topost/rif_{}.json'.format(masechet)) as fp:
                    ja = json.load(fp)
            text_version = {
                'versionTitle': 'Vilna Edition',
                'versionSource': "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001300957",
                'language': 'he',
                'text': ja
            }
            functions.post_text(title, text_version, server=server, skip_links=True)
            TS+=1

def post_mefaresh(masechtot=list(tags_map), index=True, text='first', links=True, category=True, server = 'http://localhost:8000'):
    global TS
    global LS
    categories = ["Talmud", "Bavli", "Commentary", "Rif", "Commentary"]
    if category: functions.add_category("Commentary", categories, server=server)
    for masechet in masechtot:
        categories = ["Talmud", "Bavli", "Commentary", "Rif", "Commentary"]
        mefaresh = [mef for mef in ['Ran', 'Nimmukei Yosef', 'Rabbenu Yehonatan of Lunel', 'Rabbenu Yonah'] if tags_map[masechet][mef] == 'Digitized' or tags_map[masechet][mef] == 'shut'][0]
        hmefarshim = {'Ran': 'ר"ן', 'Nimmukei Yosef': 'נימוקי יוסף', 'Rabbenu Yehonatan of Lunel': "רבינו יהונתן מלוניל", 'Rabbenu Yonah': 'רבינו יונה'}
        hmasechet = get_hebrew_masechet(masechet)
        hmefaresh = hmefarshim[mefaresh]
        c_title = '{} on Rif'.format(mefaresh)
        hc_title = '{} על רי"ף'.format(hmefaresh)
        title = '{} {}'.format(c_title, masechet)
        htitle = '{} {}'.format(hc_title, hmasechet)
        if index:
            functions.add_term(c_title, hc_title, server=server)
            if mefaresh == 'Ran' or mefaresh == 'Nimmukei Yosef':
                categories.append(c_title)
                if category: functions.add_category(c_title, categories, server=server)
            record = JaggedArrayNode()
            record.add_primary_titles(title, htitle)
            record.add_structure(['Daf', 'Comment'])
            record.addressTypes = ['Talmud', 'Integer']
            record.validate()
            index_dict = {'collective_title': c_title,
                'title': title,
                'categories': categories,
                'schema': record.serialize(),
                'dependence' : 'Commentary',
                'base_text_titles': ['Rif '+masechet]
            }
            functions.post_index(index_dict, server = server)

        if text:
            if text == 'first':
                with open(path+'/Mefaresh/json/{}.json'.format(masechet)) as fp:
                    data = json.load(fp)
            else:
                with open(path+'/tags/topost/mefaresh_{}.json'.format(masechet)) as fp:
                    data = json.load(fp)
            text_version = {
                'versionTitle': 'Vilna Edition',
                'versionSource': "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001300957",
                'language': 'he',
                'text': data
            }
            functions.post_text(title, text_version, server=server, skip_links=True)
            TS+=1

        if links:
            with open(path+'/Mefaresh/json/{}_links.json'.format(masechet)) as fp:
                data = json.load(fp)
            functions.post_link(data, server = server)
            LS+=len(data)

def post_mefareshim(masechtot=list(tags_map), mefarshim=[1,3,5,7,8,9], index=True, text=True, links=True, server = 'http://localhost:8000'):
    global TS
    global LS
    for num in mefarshim:
        categories = ["Talmud", "Bavli", "Commentary", "Rif", "Commentary"]
        mefaresh  = commentaries[str(num)]['title']
        hmefaresh = commentaries[str(num)]['h_title']
        fmefaresh = commentaries[str(num)]['f_name']
        c_title = commentaries[str(num)]['c_title']
        hc_title = '{} על רי"ף'.format(hmefaresh)
        functions.add_term(c_title, hc_title, server=server)
        if num not in [7, 8]:
            categories.append(c_title)
            functions.add_category(c_title, categories, server=server)

        for masechet in masechtot:
            if num in [1, 9]:
                try:
                    with open(path+f'/tags/topost/{fmefaresh}_{masechet}.json') as fp:
                        data = json.load(fp)
                except FileNotFoundError:
                    continue
                print(mefaresh, masechet)
            else:
                try:
                    with open(path+f'/commentaries/json/{fmefaresh}_{masechet}.json') as fp:
                        data = json.load(fp)
                except FileNotFoundError:
                    continue
                print(mefaresh, masechet)
            hmasechet = get_hebrew_masechet(masechet)
            title = '{} {}'.format(c_title, masechet)
            htitle = '{} {}'.format(hc_title, hmasechet)

            if index:
                record = JaggedArrayNode()
                record.add_primary_titles(title, htitle)
                record.add_structure(['Daf', 'Comment'])
                record.addressTypes = ['Talmud', 'Integer']
                record.validate()
                index_dict = {'collective_title': c_title,
                    'title': title,
                    'categories': categories,
                    'schema': record.serialize(),
                    'dependence': 'Commentary',
                    'base_text_titles': ['Rif '+masechet]
                }
                if (fmefaresh == 'SG' and masechet in ['Gittin', 'Kiddushin', 'Chullin']) or fmefaresh not in ['SG', 'R_Efrayim', 'ravad']:
                    Mmefaresh = main_mefaresh(masechet)
                    index_dict['base_text_titles'].append(f'{Mmefaresh} on Rif {masechet}')
                if tags_by_criteria(masechet, key=lambda x: x[0]=='3', value=lambda x: x['referred text']==num):
                    index_dict['base_text_titles'].append(f"{commentaries['1']['title']} on Rif {masechet}")
                if tags_by_criteria(masechet, key=lambda x: x[0]=='4', value=lambda x: x['referred text']==num):
                    index_dict['base_text_titles'].append(f"HaMaor {maor_godel(masechet)[0]} on {masechet}")
                if tags_by_criteria(masechet, key=lambda x: x[0]=='5', value=lambda x: x['referred text']==num):
                    index_dict['base_text_titles'].append(f"Milchemet Hashem on {masechet}")
                functions.post_index(index_dict, server = server)

            if text:
                text_version = {
                    'versionTitle': 'Vilna Edition',
                    'versionSource': "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001300957",
                    'language': 'he',
                    'text': data
                }
                functions.post_text(title, text_version, server=server, skip_links=True)
                TS+=1

            if links:
                with open(path+'/tags/topost/inline_links_{}.json'.format(masechet)) as fp:
                    data = json.load(fp)
                functions.post_link(data, server = server)
                LS+=len(data)

def post_maor(masechtot=list(maor_tags)+['intro'], mefarshim=['maor', 'milchemet'], index=True, text=True, links=True, server = 'http://localhost:8000'):
    global TS
    global LS
    titles = {'maor': {'en': 'HaMaor', 'he': 'המאור'}, 'milchemet': {'en': 'Milchemet Hashem', 'he': "מלחמת השם"}}
    for mefaresh in mefarshim:
        c_title = titles[mefaresh]['en']
        hc_title = titles[mefaresh]['he']
        if index:
            functions.add_term(c_title, hc_title, server=server)
            categories = ["Talmud", "Bavli", "Commentary", "Rif", "Commentary", c_title]
            functions.add_category(c_title, categories, server=server)
        for masechet in masechtot:
            if not isfile(f'{path}/commentaries/json/{mefaresh}_{masechet}.json'):
                continue
            if masechet == 'intro':
                title, htitle = f'Introdution to {c_title}', f'הקדמת {hc_title}'
            else:
                godel, hgodel = maor_godel(masechet)
                title, htitle = c_title, hc_title
                if mefaresh == 'maor':
                    title += f' {godel}'
                    htitle += f' {hgodel}'
                title = f'{title} on {masechet}'
                htitle = f'{htitle} על {get_hebrew_masechet(masechet)}'
            if index:
                record = JaggedArrayNode()
                record.add_primary_titles(title, htitle)
                if masechet in ['intro', 'Sotah', 'Chagigah']:
                    record.add_structure(['Comment'])
                else:
                    record.add_structure(['Daf', 'Comment'])
                    record.addressTypes = ['Talmud', 'Integer']
                record.validate()
                index_dict = {'collective_title': c_title,
                    'title': title,
                    'categories': categories,
                    'schema': record.serialize(),
                    'dependence': 'Commentary',
                    'base_text_titles': [masechet, 'Rif '+masechet]
                }
                if masechet == 'intro':
                    index_dict.pop('base_text_titles')
                elif mefaresh == 'milchemet':
                    index_dict['base_text_titles'].append(f'HaMaor {godel} on {masechet}')
                elif masechet in ['Sotah', 'Chagigah']:
                    index_dict['base_text_titles'].pop()
                functions.post_index(index_dict, server = server)
            if text:
                if text == 'first' or masechet in ['Sotah', 'Chagigah', 'intro']:
                    with open(f'{path}/commentaries/json/{mefaresh}_{masechet}.json') as fp:
                        data = json.load(fp)
                else:
                    try:
                        with open(f'{path}/tags/topost/{mefaresh}_{masechet}.json') as fp:
                            data = json.load(fp)
                    except FileNotFoundError:
                        print(f'no file {mefaresh} {masechet}')
                        continue
                text_version = {
                    'versionTitle': 'Vilna Edition',
                    'versionSource': "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001300957",
                    'language': 'he',
                    'text': data
                }
                functions.post_text(title, text_version, server=server, skip_links=True)
                TS+=1
        if links:
            if masechet != 'intro':
                with open(path+f'/commentaries/json/maor_links_{masechet}.json') as fp:
                    data = json.load(fp)
                functions.post_link(data, server = server)
                LS+=len(data)

if __name__ == '__main__':
    server = 'http://localhost:8000'
    #server = 'https://glazner.cauldron.sefaria.org'
    post_rif(index=False,text=True,server=server)
    post_mefaresh(index=False,text=True,category=False,server=server)
    post_mefareshim(index=False,server=server)
    post_maor(index=False)
    print(f'{TS} texts {LS} links')
