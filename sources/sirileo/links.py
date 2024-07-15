import csv
import os
import re
from docx import Document
import django
django.setup()
from sefaria.model import *
from linking_utilities.dibur_hamatchil_matcher import match_ref

def read_docx(file_path):
    doc = Document(f'data/{file_path}')
    full_text = []
    for para in doc.paragraphs:
        if para.text.startswith('$'):
            full_text[-1] += para.text
        else:
            full_text.append(para.text)
    return full_text

def get_pereks(masechet_data):
    perek = []
    for line in masechet_data:
        if re.search('^@\d+מסכת', line) or not line.strip():
            continue
        if re.search('^@\d+פרק', line):
            if perek:
                if len(perek) == 1: #TODO and '@88' in perek[0]: #there're 2 masechtot with paragraph before the beginning of the commentary
                    perek = []
                    continue
                if re.search('פרק (?:א|ראשון)', line):
                    print(perek)
                yield perek
            perek = []
        else:
            perek.append(line)
    yield perek

def dh_extract_method(comment):
    try:
        return re.findall('^@\d+([^@]*)@+', comment)[0]
    except:
        return ''

def match_mishna(mishna, masechet, perek):
    base_tref = f'Jerusalem Talmud {masechet} {perek}'
    chapter_refs = Ref(base_tref).all_subrefs()
    mishna_trefs = [f'{r.normal()}:1' for r in chapter_refs]
    base_texts = [Ref(r).text('he', 'Venice Edition') for r in mishna_trefs]
    matches = match_ref(base_texts, [m['text'] for m in mishna], lambda x: x.split(), chunks_list=True, dh_extract_method=dh_extract_method)['matches']
    for line in mishna:
        line['base text ref'] = matches.pop(0) or ''
    add_from_context(mishna, f'{base_tref}:1:1')

def match_gemara(chunk, masechet, perek, mishnayot):
    base_tref = f'Jerusalem Talmud {masechet} {perek}'
    chapter_refs = Ref(base_tref).all_subrefs()
    chapter_refs = [r for r in chapter_refs if r.normal().split(':')[-1] in mishnayot]
    refs = [r for ref in chapter_refs for r in ref.all_segment_refs()[1:]]
    base_texts = [r.text('he', 'Venice Edition') for r in refs]
    if not base_texts:
        print('no base text', perek, mishnayot, base_texts)
        return
    matches = match_ref(base_texts, [m['text'] for m in chunk], lambda x: x.split(), chunks_list=True, dh_extract_method=dh_extract_method)['matches']
    for line in chunk:
        line['base text ref'] = matches.pop(0) or ''
    add_from_context(chunk, f'{base_tref}:{sorted(mishnayot)[0]}:2')

def add_from_context(chunk, prev=''):
    next = ''
    for i, com in enumerate(chunk):
        if com['base text ref']:
            prev = com['base text ref']
            next = ''
        else:
            if not next:
                for c in chunk[i+1:]:
                    if c['base text ref']:
                        next = c['base text ref']
                        break
            if prev == next:
                com['base text ref'] = prev
        com['base text'] = com['base text ref'].text('he', 'Venice Edition').text if com['base text ref'] else None

def get_gemara_chunk(perek):
    relevant_mishnayot = set()
    chunk = []
    for line in perek:
        if line['mishna']:
            if chunk:
                yield chunk, relevant_mishnayot
                relevant_mishnayot = set()
                chunk = []
            if line['base text ref']:
                relevant_mishnayot.add(line['base text ref'].normal().split(':')[-2])
        else:
            chunk.append(line)
    yield chunk, relevant_mishnayot


if __name__ == '__main__':
    parsed = []
    for file in os.listdir('data'):
        if 'docx' not in file:
            continue
        masechet = re.sub('ירושלמי|ר_ש|מסכת|סירי?ל[^ ]*|מוכן|\.docx', '', file)
        masechet = ' '.join(masechet.split())
        masechet = Ref(masechet).normal().replace('Mishnah ', '')

        print(masechet)
        data = read_docx(file)
        for p, perek in enumerate(get_pereks(data), 1):
            print(f'perek {p}')
            mg = [x for x in perek if re.search('@22', x)]
            mg = [1 if 'גמ' in x else 0 for x in mg]
            if any(x+y!=1 for x,y in zip(mg, mg[1:])):
                print(mg)

            perek_dict = []
            mishna = True
            for line in perek:
                if '@22' in line:
                    if 'גמ' in line:
                        mishna = False
                    else:
                        mishna = True
                    continue
                perek_dict.append({'masechet': masechet, 'text': line, 'mishna': mishna})

            mishnayot = [line for line in perek_dict if line['mishna']]
            match_mishna(mishnayot, masechet, p)

            for chunk, mishnayot in get_gemara_chunk(perek_dict):
                match_gemara(chunk, masechet, p, mishnayot)

            parsed += perek_dict

    with open('csv/sirileo.csv', 'w') as fp:
        w = csv.DictWriter(fp, fieldnames=['masechet', 'text', 'base text ref', 'base text'])
        w.writeheader()
        for line in parsed:
            line.pop('mishna')
            w.writerow(line)

        print('succes of', 100 * len([x for x in parsed if x.get('base text ref')]) / len(parsed))
