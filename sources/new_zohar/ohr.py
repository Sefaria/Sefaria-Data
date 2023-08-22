import csv
import re
import django
django.setup()
from sefaria.model import *
from linking_utilities.dibur_hamatchil_matcher import match_ref
from ketem import make_ref, tokenizer

def find_node(parasha):
    parasha = re.sub('פרשת ', '', parasha)
    nodes = [node for i in range(3) for node in library.get_index('Zohar').alt_structs['Daf']['nodes'][i]['nodes']]
    for node in nodes:
        if node['titles'][1]['text'] == parasha:
            return node

def dh_extract_method(comm):
    comm = re.sub('@\d\d', '', comm)
    dh = re.split("\.| ו[כג]ו'", comm, 1)[0]
    stop_regex = " פי' | פירוש "
    dh = re.split(stop_regex, dh)[0]
    pre_regex = " כ' | כתב "
    if len(re.split(pre_regex, dh)) > 1 and len(re.split(pre_regex, dh)[0].split()) < 3:
        dh = re.split(pre_regex, dh)[1]
    dh = ' '.join(tokenizer(dh))
    dh = re.sub('^גי?ליון', '', dh)
    return ' '.join(dh.split()[:7])

def parse_parasha(row):
    return re.sub('@\d\d', '', row['parasha']).strip()

def parse_stream(row):
    stream = row['stream']
    stream = re.split(' [למ]פרשת', stream)[0]
    stream = re.sub('@\d\d|\.| בס"ד| פ\' יתרו', '', stream)
    stream = stream.replace('רע"מ', 'רעיא מהימנא')
    if stream == 'גוף':
        stream = ''
    if 'רח"ו' in stream:
        stream = ''
    return stream

def parse_page(row):
    return re.search('דף (.{1,3} ע"[אב])', row['page']).group(1)

def parse():
    page = 0
    e = []
    with open('ohr.csv') as fp:
        data = list(csv.DictReader(fp))
    for row in data:
        if row['parasha']:
            parasha = parse_parasha(row)
            stream = ''
            print(parasha)
        if row['stream'] :
            stream = parse_stream(row)
        if row['page']:
            page = parse_page(row)
        # print(parasha, stream, page)
        ref = make_ref(parasha, stream, page, find_node(parasha))
        if type(ref) == str and ref.startswith('cannot') and ref not in e:
            e.append(ref)
        elif type(ref) == str:
            matches = match_ref(Ref(ref).text('he', vtitle='Vocalized Zohar, Israel 2013'), [row['text']],
                      tokenizer, dh_extract_method=dh_extract_method)['matches']
            if matches and matches[0]:
                row['base ref'] = matches[0].normal()
                row['base text'] = matches[0].text('he').text

    print('\n'.join(e))
    with open('ohr with links.csv', 'w') as fp:
        writer = csv.DictWriter(fp, fieldnames=['parasha', 'stream', 'page', 'text', 'base ref', 'base text'])
        writer.writeheader()
        for row in data:
            writer.writerow(row)

def round2():
    with open('ohr with links.csv') as fp:
        data = list(csv.DictReader(fp))
    new = []
    page = 0
    for row in data:
        if row['parasha']:
            parasha = parse_parasha(row)
            stream = ''
            print(parasha)
        if row['stream']:
            stream = parse_stream(row)
        if row['page']:
            page = parse_page(row)
        if row['parasha'] or row['stream'] or row['page']:
            new.append([])
            row['parasha'] = parasha
            row['stream'] = stream
            row['page'] = page
        new[-1].append(row)
    for block in new:
        parasha = block[0]['parasha']
        stream = block[0]['stream']
        page = block[0]['page']
        block_ref = make_ref(parasha, stream, page, find_node(parasha))
        if 'cannot find' in block_ref:
            print('cannot find', len(block_ref), parasha, stream, page)
            continue
        start = Ref(block_ref).all_segment_refs()[0].normal()
        end = ''
        for r, row in enumerate(block):
            if row['base ref']:
                start = row['base ref']
                end = ''
            else:
                if not end:
                    for nrow in block[r:]:
                        if nrow['base ref']:
                            end = nrow['base ref']
                            break
                        end = Ref(block_ref).all_segment_refs()[-1].normal()
                if start == end:
                    row['base ref'] = start
                else:
                    ref = f'{start}-{end.split()[-1]}'
                    try:
                        Ref(ref)
                    except:
                        continue
                    matches = match_ref(Ref(ref).text('he', vtitle='Vocalized Zohar, Israel 2013'), [row['text']],
                                        tokenizer, dh_extract_method=dh_extract_method, char_threshold=0.4)['matches']
                    if matches and matches[0]:
                        start = row['base ref'] = matches[0].normal()
                    if row['base ref']:
                        row['base text'] = Ref(row['base ref']).text('he', vtitle='Vocalized Zohar, Israel 2013').text
                    row['dh'] = dh_extract_method(row['text'])
    with open('ohr with links r2.csv', 'w') as fp:
        writer = csv.DictWriter(fp, fieldnames=['parasha', 'stream', 'page', 'text', 'dh', 'base ref', 'base text'])
        writer.writeheader()
        for row in data:
            writer.writerow(row)


if __name__ == '__main__':
    # parse()
    round2()
