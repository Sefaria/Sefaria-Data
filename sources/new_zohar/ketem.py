import csv
import re
import django
django.setup()
from sefaria.model import *
from sefaria.utils.hebrew import gematria
from sefaria.utils.talmud import section_to_daf, daf_to_section
from linking_utilities.dibur_hamatchil_matcher import match_ref


def handle_page(page_string):
    page_regex = '[א-ת]{1,3} ע"[אב]'
    page = re.findall(page_regex, page_string)
    if not page:
        print('problem with page', page_string)
        return page_string, ''
    page = page[0]
    remain = re.sub(page_regex, '', page_string).strip()
    return remain, page

def make_node_addresses(node):
    if 'addresses' in node:
        return node['addresses']
    skipped = node.get('skipped_addresses', [])
    addresses = []
    i = daf_to_section(node['startingAddress'])
    for _ in node['refs']:
        while i in skipped:
            i += 1
        addresses.append(i)
        i += 1
    return addresses

PARASHOT = []
def make_ref(parasha, stream, rpage, node=None):
    if 'הקדמת' in parasha or not parasha:
        return
    global PARASHOT
    if parasha not in PARASHOT:
        PARASHOT.append(parasha)
    if node==None:
        node = library.get_index('Zohar').alt_structs['Daf']['nodes'][0]['nodes'][len(PARASHOT)-1]
    if parasha == 'השמטות':
        return node['nodes'][gematria(stream)]['wholeRef']
    else:
        if not stream:
            if 'nodes' in node:
                node = node['nodes'][0]
        else:
            node = [n for n in node['nodes'] if 'titles' in n and n['titles'][1]['text'] == stream]
            if not node:
                print(f'cannot find {parasha} {stream}')
                return
            node = node[0]
        page = gematria(rpage.split()[0]) * 2 + gematria(rpage.split()[1]) - 72
        for ref, address in zip(node['refs'], make_node_addresses(node)):
            if address == page:
                return ref
        if parasha == 'פרשת משפטים' and not stream:
            return make_ref('saba', stream, rpage, node=library.get_index('Zohar').alt_structs['Daf']['nodes'][1]['nodes'][5]['nodes'][1])
        elif parasha == 'saba':
            return make_ref('', stream, rpage, node=library.get_index('Zohar').alt_structs['Daf']['nodes'][1]['nodes'][5]['nodes'][2])
        elif parasha == 'פרשת שלח לך' and not stream:
            return make_ref('metivta', stream, rpage, node=library.get_index('Zohar').alt_structs['Daf']['nodes'][2]['nodes'][14]['nodes'][1])
        else:
            print('cannot find page', parasha, stream, rpage, node)
            return f'cannot find page: {parasha}, {stream}, {rpage}'

def make_data_for_match():
    data = {}
    parasha = page = stream = ''
    with open('ketem.csv') as fp:
        for row in csv.DictReader(fp):
            if row['parasha']:
                parasha = row['parasha']
                parasha = re.sub('@\d\d', '', parasha)
                stream = ''
            if row['page']:
                page = row['page']
                stream, page = handle_page(page)
            ref = make_ref(parasha, stream, page)
            segments = []
            concat = False
            for i, segment in enumerate(row['text'].split('.')):
                if concat:
                    segments[-1] += f'. {segment}'
                    concat = False
                    continue
                segments.append(segment)
                if (i == 0 and len(segment) < 80) or len(segment) < 30:
                    concat = True
            segments = [[x, '', parasha, stream, page] for x in segments ]
            segments[0][1] = 'first'
            segments[-1][1] = 'last'
            if len(segments) == 1:
                segments[0][1] = 'first last'
            if ref in data:
                data[ref] += segments
            else:
                data[ref] = segments
    return data

def parse():
    data = make_data_for_match()
    parsed = []
    for ref in data:
        if ref:
            matches = match_ref(Ref(ref).text('he', vtitle='Vocalized Zohar, Israel 2013'), [x[0] for x in data[ref]], tokenizer,
                                dh_extract_method=lambda x: ' '.join(tokenizer(x)[:7]), place_consecutively=True)['matches']
        else:
            matches = [None for _ in data[ref]]
        for comm, match in zip(data[ref], matches):
            if match or 'first' in comm[1]:
                base_text = ''
                if match:
                    base_text = match.text('he').text
                    match = match.normal()
                parsed.append({'parasha': comm[2], 'stream': comm[3], 'page': comm[4], 'text': comm[0].strip(), 'ref': match, 'base text': base_text})
            else:
                parsed[-1]['text'] += f' {comm[0]}'
            if 'last' not in comm[1]:
                parsed[-1]['text'] += '.'
    with open('parsed.csv', 'w') as fp:
        w = csv.DictWriter(fp, fieldnames=['parasha', 'stream', 'page', 'text', 'ref', 'base text'])
        w.writeheader()
        for row in parsed:
            w.writerow(row)


with open('abbr.csv') as fp:
    ABBR = sorted(list(csv.DictReader(fp)), key=lambda x: len(x['abbr']), reverse=True)
def tokenizer(string):
    for ab in ABBR:
        rab = ab['abbr'].replace('"', '(?:"|\'\')')
        string = re.sub(f'(^| ){rab}', rf"\1{ab['full']}", string)
    string = re.sub('<i .*?/i>', '', string)
    string = re.sub('<[^>]*>', '', string)
    string = re.sub('\([^\)]*\)', '', string)
    string = re.sub('\[[^\]]*\]', '', string)
    string = re.sub("'\"", ' ', string)
    string = re.sub('[^א-ת ]', '', string)
    return string.split()

if __name__ == '__main__':
    parse()
