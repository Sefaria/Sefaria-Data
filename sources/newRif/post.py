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
from rif_utils import tags_map, path, get_hebrew_masechet, main_mefaresh, commentaries, maor_tags, maor_godel, hebrewplus
from tags_fix_and_check import tags_by_criteria
import time

TS = 0
LS = 0
REPORT = set()
REFS = []

def housekeep(string, btext, masechet='', regex=''):
    if masechet == 'Nedraim':
        for tag in re.findall('\$\d{8}', string):
            string = string.replace(tag, '')
    elif masechet:
        for tag in re.findall('\$\d{8}', string):
            original = tags_by_criteria(masechet)[tag.replace('$', '')]['original']
            string = string.replace(tag, original)
    if regex:
        string = re.sub(regex, '', string)
    string = re.sub('°\)|\*\)|\d[ab]|<b><big><\/big><\/b>', '', string)
    string = hebrewplus(string, '\(\[\)\]:\.,<>a-zA-Z-\/\*"\'⚬=0-9')
    string = re.sub('(?<!\")\d(?!\")', '', string)
    string = re.sub(r'\s', ' ', string)
    string = string.strip()
    string = re.sub(' +', ' ', string)
    string = re.sub(' ([\)\]:\.,])', r'\1 ', string)
    string = re.sub('([\(\[]) ', r' \1', string)
    string = re.sub('(<\/i>)\)', r'\1', string)
    string = string.strip()
    string = re.sub(' +', ' ', string)
    string = re.sub('(?: |^)(<sup.*?\/i>)(?: |$)', r' \1', string)
    string = re.sub('(?: |^)(<[^א-ת]*>)(?: |$)', r' \1', string)
    string = re.sub('\((\(.*\))\)', r'\1', string)
    asts = re.findall('\*(?!<\/sup>).{0,10}', string)
    if asts:
        for ast in asts:
            REPORT.add(f'* in {btext}: {ast}')
    string = re.sub('\*(?!<\/sup>)', '', string)
    brokenparen = re.findall('\((?![^\)\(]*\)).{0,10}', string)
    brokenparen += re.findall('\)(?![^\)\(]*\().{0,10}', string[::-1])
    if brokenparen and string.count('(') != string.count(')'):
        for br in brokenparen:
            REPORT.add(f'broken parens in {btext}: {br}')
    brokenbrac = re.findall('\[(?![^\]\[]*\]).{0,10}', string)
    brokenbrac += re.findall('\](?![^\]\[]*\[).{0,10}', string[::-1])
    if brokenbrac and string.count('[') != string.count(']'):
        for br in brokenbrac:
            REPORT.add(f'broken brackets in {btext}: {br}')
    return string

def hk_ja(ja, btext, masechet='', regex=''):
    new_ja = []
    for n, item in enumerate(ja):
        if type(item) is list:
            new_ja.append(hk_ja(item, f'{btext} {n}', masechet, regex))
        elif type(item) is str:
            new_ja.append(housekeep(item, f'{btext} {n}', masechet, regex))
    return new_ja

def post_rif(masechtot=list(tags_map), index=True, text='csv', links=True, server = 'http://localhost:8000', clean=False):
    global TS
    global LS
    global REFS
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
            try:
                with open(path+'/gemara_links/more_{}.json'.format(masechet)) as fp:
                    data += json.load(fp)
            except FileNotFoundError:
                pass
            data = [link for lis in data for link in lis]
            REFS += [link['refs'] for link in data]
            functions.post_link(data, server = server)
            LS+=len(data)
        if text:
            if text == 'csv':
                with open(f'{path}/rif_gemara_refs/rif_{masechet}.csv', encoding='utf-8', newline='') as fp:
                    data = list(csv.DictReader(fp))
                    ja = []
                    last_page = daf_to_section(data[-1]['page.section'].split(':')[0])
                    for n in range(last_page):
                        ja.append([row['content'] for row in data if row['page.section'].split(':')[0] == section_to_daf(n+1)])
            else:
                with open(path+'/tags/topost/rif_{}.json'.format(masechet)) as fp:
                    ja = json.load(fp)
                if clean:
                    ja = hk_ja(ja, btext=f' rif {masechet}', masechet=masechet)
            text_version = {
                'versionTitle': 'Vilna Edition',
                'versionSource': "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001300957",
                'language': 'he',
                'text': ja
            }
            functions.post_text(title, text_version, server=server, skip_links=True)
            TS+=1

def post_mefaresh(masechtot=list(tags_map), index=True, text='first', links=True, category=True, server = 'http://localhost:8000', clean=False):
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
        c_title = '{}'.format(mefaresh)
        hc_title = '{}'.format(hmefaresh)
        title = '{} on Rif {}'.format(c_title, masechet)
        htitle = '{} על רי"ף {}'.format(hc_title, hmasechet)
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
                if clean:
                    data = hk_ja(data, btext=f'mefaresh {masechet}', masechet=masechet)
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

def post_mefareshim(masechtot=list(tags_map), mefarshim=[1,2,3,4,5,6,7,8,9,10,11,12], index=True, text=True, links=True, server = 'http://localhost:8000', clean=False):
    global TS
    global LS
    if index or text:
        for num in mefarshim:
            if num == 6: continue
            categories = ["Talmud", "Bavli", "Commentary", "Rif", "Commentary"]
            mefaresh  = commentaries[str(num)]['title']
            hmefaresh = commentaries[str(num)]['h_title']
            fmefaresh = commentaries[str(num)]['f_name']
            c_title = commentaries[str(num)]['c_title']
            if num == 10:
                hc_title = 'כתוב שם'
            elif num == 11:
                hc_title = 'העתקת פירוש הרי"ף'
            elif num == 12:
                hc_title = 'ספר הזכות על השגות הראב"ד'
            else:
                hc_title = '{} על רי"ף'.format(hmefaresh)
            functions.add_term(mefaresh, hmefaresh, server=server)
            if num not in [7, 8]:
                categories.append(mefaresh)
                functions.add_category(mefaresh, categories, server=server)

            for masechet in masechtot:
                if num == 6: continue
                if num in [1, 2, 9]:
                    try:
                        with open(path+f'/tags/topost/{fmefaresh}_{masechet}.json') as fp:
                            data = json.load(fp)
                    except FileNotFoundError:
                        continue
                else:
                    try:
                        if num == 12:
                            if masechet in[ 'Yoma', 'Kiddushin']: continue
                            file = path+f'/commentaries/json/z{masechet[0].lower()}.json'
                        elif num == 11:
                            if masechet == 'Ketubot':
                                file = path+f'/commentaries/json/td.json'
                            elif masechet == 'Shevuot':
                                file = path+f'/commentaries/json/tds.json'
                            else:
                                continue
                        else:
                            file = path+f'/commentaries/json/{fmefaresh}_{masechet}.json'
                        with open(file) as fp:
                            data = json.load(fp)
                    except FileNotFoundError:
                        print('no file', mefaresh, masechet)
                        continue
                if masechet == 'Pesachim' and num == 10:
                    regex = ''
                else:
                    regex = '\d(?:\(.\)|\[.\])|(?:^| ).\]'
                if clean:
                    data = hk_ja(data, btext=f'{mefaresh} {masechet}', masechet=masechet, regex=regex)

                hmasechet = get_hebrew_masechet(masechet)
                title = '{} {}'.format(c_title, masechet)
                htitle = '{} {}'.format(hc_title, hmasechet)

                if index:
                    record = JaggedArrayNode()
                    record.add_primary_titles(title, htitle)
                    record.add_structure(['Daf', 'Comment'])
                    record.addressTypes = ['Talmud', 'Integer']
                    record.validate()
                    index_dict = {'collective_title': mefaresh,
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
                    if tags_by_criteria(masechet, key=lambda x: x[0]=='6', value=lambda x: x['referred text']==num):
                        index_dict['base_text_titles'].append(f"{commentaries['2']['c_title']} {masechet}")
                    if num == 10:
                        index_dict['base_text_titles'] = [f"HaMaor {maor_godel(masechet)[0]} on {masechet}"]
                    elif num == 12 and masechet == 'Gittin':
                        index_dict['base_text_titles'].append(f"{commentaries['9']['c_title']} {masechet}")
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
        if set(mefarshim) | {6, 9, 11, 12} != {6, 9, 11, 12}:
            for masechet in masechtot:
                with open(path+'/tags/topost/inline_links_{}.json'.format(masechet)) as fp:
                    data = json.load(fp)
                functions.post_link(data, server = server)
                LS+=len(data)
        if 6 in mefarshim:
            print(6)
            for masechet in masechtot:
                with open(path+'/tags/topost/em_links_{}.json'.format(masechet)) as fp:
                    data = json.load(fp)
                functions.post_link(data, server = server)
                LS+=len(data)
        if 11 in mefarshim:
            print(11)
            for masechet in masechtot:
                if masechet in ['Ketubot', 'Shevuot']:
                    if masechet == 'Ketubot':
                        with open(path+'/commentaries/json/links_td.json'.format(masechet)) as fp:
                            data = json.load(fp)
                    elif masechet == 'Shevuot':
                        with open(path+'/commentaries/json/links_tds.json'.format(masechet)) as fp:
                            data = json.load(fp)
                    functions.post_link(data, server = server)
                    LS+=len(data)
        if 12 in mefarshim:
            print(12)
            for t in ['zg', 'zy', 'zk']:
                with open(f'{path}/commentaries/json/links_{t}.json'.format(masechet)) as fp:
                    data = json.load(fp)
                functions.post_link(data, server = server)
                LS+=len(data)
        if 9 in mefarshim:
            print(9)
            for masechet in masechtot:
                if masechet in ['Makkot', 'Shevuot']:
                    with open(f'{path}/commentaries/json/links_ravad_{masechet}.json'.format(masechet)) as fp:
                        data = json.load(fp)
                    functions.post_link(data, server = server)
                    LS+=len(data)

def post_maor(masechtot=list(maor_tags)+['intro'], mefarshim=['maor', 'milchemet'], index=True, text=True, links=True, server = 'http://localhost:8000', clean=False):
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
                        if clean:
                            data = hk_ja(data, btext=f'{title}', masechet=masechet)
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
        for masechet in masechtot:
            if masechet != 'intro':
                with open(path+f'/commentaries/json/maor_links_{masechet}.json') as fp:
                    data = json.load(fp)
                functions.post_link(data, server = server)
                LS+=len(data)

if __name__ == '__main__':
    #server = 'http://localhost:8000'
    server = 'https://glazner.cauldron.sefaria.org'
    #post_rif(text=True,clean=True,server=server,index=False,links=False)#,masechtot=['Bava Batra'])
    #post_mefaresh(text=True,clean=True,server=server,index=False,links=False)#,masechtot=masechtot)
    #post_maor(clean=True,server=server,index=False,text=True)#,links=False)
    post_mefareshim(clean=True,server=server,index=True,text=True,links=True,mefarshim=[12])#,masechtot=['Bava Batra'])
    print(f'{TS} texts {LS} links')
    #print(REPORT)
    REFS=set(REFS)
    print(len(REFS))
