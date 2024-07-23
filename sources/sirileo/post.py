import re

import django
django.setup()
from sefaria.model import *
import csv
from sources.functions import post_index, post_text, post_link, add_term, add_category
from  functools import reduce
from copy import copy

def assign(array, index, filler_type):
    array += [filler_type() for _ in range(len(array), index+1)]
    if not array[index]:
        array[index] = filler_type()

def deep_assign(array, indexes):
    for i in range(len(indexes)):
        array_to_assign = reduce(lambda x, y: x[y], indexes[:i], array)
        filler_type = list
        assign(array_to_assign, indexes[i], filler_type)

def deep_append_ref_indexes(array, indexes, element):
    indexes = [i-1 for i in indexes]
    deep_assign(array, indexes)
    array_to_append = reduce(lambda x, y: x[y], indexes, array)
    array_to_append.append(element)

with open('sirileo.csv') as fp:
    data = list(csv.DictReader(fp))

masses = {row['masechet'] for row in data}
com = name = 'Sirilio'
base_name = 'Jerusalem Talmud'
for mas in masses:
    if mas not in ['Berakhot','Maaser Sheni','Peah','Sheviit','Terumot']: continue
    print(mas)
    title = f'{name} on {base_name} {mas}'
    text = []
    links = []
    rows = [row for row in data if row['masechet'] == mas]
    for row in rows:
        base_ref = row['base text ref']
        sections = Ref(base_ref).sections[:]
        row_text = row['text']
        do_link = '@99' not in row_text
        row_text = row_text.replace('@11', '<b>').replace('@33', '</b>').replace(' </b>', '</b> ')
        row_text = re.sub('[@\d]', '', row_text)
        deep_append_ref_indexes(text, sections, ' '.join(row_text.split()))
        sections.append(len(reduce(lambda x, y: x[y], [s-1 for s in sections], text)))
        if do_link:
            links.append({
                'refs': [base_ref, f'{title} {":".join([str(s) for s in  sections])}'],
                'auto': True,
                'dependence': 'commentary',
                'generated_by': 'sirileo linker'
            })

    server = 'http://localhost:8000'
    server = 'https://new-shmuel.cauldron.sefaria.org'
    he_com = 'פירוש שלמה סיריליו'
    ter = name + ' on Jerusalem Talmud'
    he_ter = he_com + ' על תלמוד ירושלמי'
    # add_term(ter, he_ter, server=server)
    # add_term(name, he_com, server=server)
    categories = ["Talmud", "Yerushalmi", "Commentary", ter]
    # add_category(categories[-1], categories, server=server)
    base_title = f'Jerusalem Talmud {mas}'
    he_bt = library.get_index(base_title).get_title('he')
    record = JaggedArrayNode()
    record.add_primary_titles(title, f'{he_com} על {he_bt}')
    record.add_structure(['Chapter', 'Halakhah', 'Segment', 'Comment'])
    record.addressTypes = ['Perek', 'Halakhah', 'Integer', 'Integer']
    record.toc_zoom = 2
    record.validate()
    index_dict = {'collective_title': com,
                  'title': title,
                  'categories': categories,
                  'schema': record.serialize(),
                  'dependence': 'Commentary',
                  'base_text_titles': [base_title],
                  'base_text_mapping': 'many_to_one'
                  }
    post_index(index_dict, server=server)
    text_version = {
        'versionTitle': 'Jerusalem, 1934-1967',
        'versionSource': "https://www.nli.org.il/he/books/NNL_ALEPH990020935830205171/NLI",
        'language': 'he',
        'text': text
    }
    post_text(title, text_version, server=server, index_count='on')
    # post_link(links, server, False, False)

