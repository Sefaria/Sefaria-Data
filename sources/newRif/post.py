import django
django.setup()
import json
from sefaria.model import *
from sources import functions
from rif_utils import tags_map, path, get_hebrew_masechet

server = 'http://localhost:8000'
#server = 'https://glazner.cauldron.sefaria.org'


def post_mefaresh(masechtot=list(tags_map), index=True, text=True, links=True):
    for masechet in masechtot:
        categories = ["Talmud", "Bavli", "Commentary", "Rif", "Commentary"]
        functions.add_category("Commentary", categories, server=server)
        mefaresh = [mef for mef in ['Ran', 'Nimmukei Yosef', 'Rabbi Yehonatan of Lunel', 'Talmidei Rabenu Yonah'] if tags_map[masechet][mef] == 'Digitized' or tags_map[masechet][mef] == 'shut'][0]
        hmefarshim = {'Ran': 'ר"ן', 'Nimmukei Yosef': 'נימוקי יוסף', 'Rabbi Yehonatan of Lunel': "ר' יהונתן מלוניל", 'Talmidei Rabenu Yonah': 'תלמידי רבינו יונה'}
        hmasechet = get_hebrew_masechet(masechet)
        hmefaresh = hmefarshim[mefaresh]
        c_title = '{} on Rif'.format(mefaresh)
        hc_title = '{} על רי"ף'.format(hmefaresh)
        title = '{} {}'.format(c_title, masechet)
        htitle = '{} {}'.format(hc_title, hmasechet)

        if index:
            functions.add_term(mefaresh, hmefaresh, server=server)
            if mefaresh == 'Ran' or mefaresh == 'Nimmukei Yosef':
                categories.append(mefaresh)
                functions.add_category(mefaresh, categories, server=server)
            record = SchemaNode()
            record.add_primary_titles(title, htitle)
            node = JaggedArrayNode()
            node.key = 'default'
            node.default = True
            node.add_structure(['Daf', 'Comment'])
            node.addressTypes = ["Talmud", "Integer"]
            record.append(node)
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
    post_mefaresh()
