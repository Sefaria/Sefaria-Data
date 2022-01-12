import django
django.setup()
from sefaria.model import *
from sources.functions import add_term, add_category, post_index, post_text
import csv
from functools import reduce
import copy

ohr = 'Ohr LaYesharim'
hohr = 'אור לישרים'
jt = ' on Jerusalem Talmud'
hjt = ' על תלמוד ירושלמי'
categories = ["Talmud", "Yerushalmi", "Modern Commentary on Talmud", ohr+jt]
server = 'http://localhost:9000'
#server = 'https://shorashim.cauldron.sefaria.org'

def assign(array, inds, element):
    for i in range(len(inds)):
        to_add = reduce(lambda a, b: [a], inds[i+1:], '')
        try:
            reduce(lambda a, b: a[b], inds[:i+1], array)
        except IndexError:
            sub = reduce(lambda a, b: a[b], inds[:i], array)
            sub += [copy.deepcopy(to_add) for _ in range(1 + inds[i] - len(sub))]
    reduce(lambda a, b: a[b], inds[:-1], array)[inds[-1]] = element
    return array

def create_index(mas):
    record = SchemaNode()
    he_bt = library.get_index(f'Jerusalem Talmud {mas}').get_title('he')
    record.add_primary_titles(f'{ohr}{jt} {mas}', f'{hohr} על {he_bt}')
    intro = JaggedArrayNode()
    intro.add_primary_titles('Introduction', 'הקדמה')
    intro.addressTypes = ['Integer']
    intro.sectionNames = ['Segment']
    intro.depth = 1
    default = JaggedArrayNode()
    default.default = True
    default.key = 'default'
    default.add_structure(['Chapter', 'Halakhah', 'Segment'])
    default.addressTypes = ['Perek', 'Halakhah', 'Integer']
    record.append(intro)
    record.append(default)
    record.validate()
    index_dict = {'collective_title': ohr,
                  'title': f'{ohr}{jt} {mas}',
                  'categories': categories,
                  'schema': record.serialize(),
                  'dependence': 'Commentary',
                  'base_text_titles': [f'Jerusalem Talmud {mas}'],
                  'base_text_mapping': 'one_to_one'
                  }
    post_index(index_dict, server=server)

def create_text(mas):
    fname = f'data/Jerusalem Talmud {mas} - Ohr LaYesharim alignment - Guggenheimer.csv'
    text = []
    for row in csv.DictReader(open(fname, encoding='utf-8', newline='')):
        if not row['Index Title'].startswith('Jerusalem Talmud'):
            continue
        inds = row['Index Title'].split()[-1].split(':')
        inds = [int(x) - 1 for x in inds]
        assign(text, inds, row[f''])
    text_version = {
        'versionTitle': 'Machon HaYerushalmi, Rabbi Yehoshua Buch',
        'versionSource': "",
        'language': 'he',
        'text': text}
    post_text(f'{ohr}{jt} {mas}', text_version, server=server, index_count='on')

add_term(ohr, hohr, server=server)
add_term(ohr+jt, hohr+hjt, server=server)
add_category(ohr+jt, categories, server=server)
mases = ['Taanit', 'Sukkah', 'Shekalim', 'Sanhedrin', 'Rosh Hashanah', 'Peah', 'Moed Katan', 'Megillah', 'Chagigah', 'Berakhot', 'Beitzah']
for mas in mases:
    create_index(mas)
    create_text(mas)
