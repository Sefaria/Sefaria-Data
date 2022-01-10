import os

import django
django.setup()
from sefaria.model import *
import csv
import re
from functools import reduce
import copy
from parse_com import get_details
from sources.functions import add_term, add_category, post_text, post_index

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

def text_from_file(filename, data=None, breaks=True):
    text_array = []
    if not data:
        data = list(csv.DictReader(open(filename, encoding='utf-8', newline='')))
    old_indexes = []

    if breaks:
        newdata = []
        for row in data:
            for seg in row['comment'].split('<br>'):
                newdata.append({'base text ref': row['base text ref'], 'comment': seg, 'commentary': row['commentary']})
        data = newdata

    for row in data:
        row['base text ref'] = row['base text ref'].replace('JTmock', 'Jerusalem Talmud')
        text = ' '.join(row['comment'].split())
        if '{' in text or '}' in text:
            print('{} in text}', row['base text ref'])
            text = re.sub(r'\{([^\}]*)\}', r'<small>[\1]</small>', text)
        if text.count(':') > 1:
            print('many : in text', row['base text ref'])
        if '.' in text:
            dh = text.split('.')[0]
            if len(dh.split()) < 20:
                if re.search('^@22(?:מתני|גמ)', dh):
                    dh = ' '.join(dh.split()[1:])
                text = text.replace(f'{dh}.', f'<b>{dh}.</b>', 1)
        text = re.sub('[^"\'\.,:\(\)\[\]\- א-ת\/><smalb]', '', text)
        text = ' '.join(text.split())
        text = re.sub(' \.', '\.', text)
        text = re.sub("^(מתני'|גמ')\)", r'\1', text)
        if row['commentary'] == 'עמודי ירושלים תנינא':
            text = f'<small>[כ"י]</small> {text}'
        indexes = [int(x)-1 for x in row['base text ref'].split()[-1].split('-')[0].split(':')]
        last = 0 if indexes != old_indexes else last + 1
        old_indexes = indexes[:]
        indexes += [last]
        try:
            if text_array[indexes[0]][indexes[1]][indexes[2]][indexes[3]]:
                text_array[indexes[0]][indexes[1]][indexes[2]].append(text)
            else:
                text_array[indexes[0]][indexes[1]][indexes[2]][indexes[3]] = text
        except IndexError:
            assign(text_array, indexes, text)
    return text_array

def post(mas, com, server, data=None):
    coms_details = get_details()
    he_com = [key for key in coms_details if coms_details[key]['en']==com][0]
    ter = com + ' on Jerusalem Talmud'
    he_ter = he_com + ' על תלמוד ירושלמי'
    add_term(ter, he_ter, server=server)
    add_term(com, he_com, server=server)

    categories = ["Talmud", "Yerushalmi", "Commentary"]
    add_category('Commentary', categories, server=server)
    categories.append(ter)
    add_category(ter, categories, server=server)
    base_title = f'Jerusalem Talmud {mas}'
    categories.append(library.get_index(base_title).categories[-1])
    add_category(categories[-1], categories, server=server)

    title = f'{com} on {base_title}'
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

    file = f'ready to parse/{com.lower()}/{mas} - {mas}.csv'
    text = text_from_file(file, data=data)
    text_version = {
        'versionTitle': 'Piotrków, 1898-1900',
        'versionSource': "https://www.nli.org.il/he/books/NNL_ALEPH001886777/NLI",
        'language': 'he',
        'text': text
    }
    #post_text(title, text_version, server=server, index_count='on')

if __name__ == '__main__':
    server = 'http://localhost:9000'
    server = 'https://jt4.cauldron.sefaria.org'
    for file in os.listdir(f'ready to parse'):
        if '~' in file:
            continue
        com = file.split('.')[0]
        data = list(csv.DictReader(open(f'ready to parse/{com}.csv', encoding='utf-8', newline='')))
        mases = {row['masechet'] for row in data}
        for mas in mases:
            print(mas)
            mas_data = [row for row in data if row['masechet'] == mas]
            post(mas, com, server, data=mas_data)
    '''for file in os.listdir(f'ready to parse/{com.lower()}'):
        if '~' in file:
            continue
        mas = file.split(' -')[0]
        print(mas)
        post(mas, com, server)'''
