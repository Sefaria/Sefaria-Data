import requests
import django
import json
import csv
import re
django.setup()
from sefaria.model import *
from sources import functions
from sefaria.utils.talmud import daf_to_section, section_to_daf
from rif_utils import tags_map, path, get_hebrew_masechet

#server = 'http://localhost:8000'
server = 'https://glazner.cauldron.sefaria.org'

def housekeep(string):
    string = re.sub(r'\s', ' ', string)
    string = re.sub(' +', ' ', string)
    string = re.sub(r' ([\)\]:\.])', r'\1 ', string)
    string = re.sub(r'([\(\[]) ', r' \1', string)
    string = re.sub('(<sup.*?/i>) ', r' \1', string)
    string = re.sub(' +', ' ', string)
    return string

def post_rif(masechtot=list(tags_map), index=True, text=True, links=True, server = 'http://localhost:8000'):
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
        if text:
            with open(f'{path}/rif_gemara_refs/rif_{masechet}.csv', encoding='utf-8', newline='') as fp:
                data = list(csv.DictReader(fp))
                ja = []
                last_page = daf_to_section(data[-1]['page.section'].split(':')[0])
                for n in range(last_page):
                    ja.append([housekeep(row['content']) for row in data if row['page.section'].split(':')[0] == section_to_daf(n+1)])
            text_version = {
                'versionTitle': 'Vilna Edition',
                'versionSource': "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001300957",
                'language': 'he',
                'text': ja
            }
            functions.post_text(title, text_version, server=server)

def post_mefaresh(masechtot=list(tags_map), index=True, text=True, links=True, server = 'http://localhost:8000'):
    for masechet in masechtot:
        mefaresh = [mef for mef in ['Ran', 'Nimmukei Yosef', 'Rabbenu Yehonatan of Lunel', 'Rabbenu Yonah'] if tags_map[masechet][mef] == 'Digitized' or tags_map[masechet][mef] == 'shut'][0]
        hmefarshim = {'Ran': 'ר"ן', 'Nimmukei Yosef': 'נימוקי יוסף', 'Rabbenu Yehonatan of Lunel': "רבינו יהונתן מלוניל", 'Rabbenu Yonah': 'רבינו יונה'}
        hmasechet = get_hebrew_masechet(masechet)
        hmefaresh = hmefarshim[mefaresh]
        c_title = '{} on Rif'.format(mefaresh)
        hc_title = '{} על רי"ף'.format(hmefaresh)
        title = '{} {}'.format(c_title, masechet)
        htitle = '{} {}'.format(hc_title, hmasechet)
        if index:
            categories = ["Talmud", "Bavli", "Commentary", "Rif", "Commentary"]
            functions.add_category("Commentary", categories, server=server)
            functions.add_term(c_title, hc_title, server=server)
            if mefaresh == 'Ran' or mefaresh == 'Nimmukei Yosef':
                categories.append(c_title)
                functions.add_category(c_title, categories, server=server)
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
            with open(path+'/Mefaresh/json/{}.json'.format(masechet)) as fp:
                data = json.load(fp)
            text_version = {
                'versionTitle': 'Vilna Edition',
                'versionSource': "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001300957",
                'language': 'he',
                'text': data
            }
            functions.post_text(title, text_version, server=server)

        if links:
            with open(path+'/Mefaresh/json/{}_links.json'.format(masechet)) as fp:
                data = json.load(fp)
            functions.post_link(data, server = server)

if __name__ == '__main__':
    #post_rif(delete=False)
    post_mefaresh(text=True)
