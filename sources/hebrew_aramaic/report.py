import re
import os
from lxml import etree
from collections import defaultdict
import django
django.setup()
from sefaria.utils.hebrew import has_cantillation

def get_text_excluding_tag(element, exclude=None):
    if exclude is None:
        exclude = ['head-word', 'xref', 'binyan-form', 'binyan-name']
    text = ''
    if element.tag not in exclude:
        if element.text:
            text += f' {element.text}'
        for child in element:
            text += f' {get_text_excluding_tag(child, exclude=exclude)}'
        if element.tail:
            text += f' {element.tail}'
    return text

def str_element(element):
    return etree.tostring(element, pretty_print=True, encoding='utf-8').decode()

def parse_file(file):
    # tree = etree.parse(f'{path}/{file}')
    # root = tree.getroot()
    with open(f'{path}/{file}') as fp:
        data = fp.read()
    data = re.sub('<!--(</?xref[^>]*>)-->', r'\1', data)
    if re.search('<!--(?!Exact).', data):
        print('comments:', re.findall('<!--(?!Exact).{,10}', data))
    data = re.sub('<!--Exact location not found', '', data)
    root = etree.fromstring(data)
    return root


path = 'data'
if __name__ == '__main__':
    binyanim = ["אפ'", "אתפ'", "הופ'", "הפ'", "התפ'", "נפ'", "נתפ'", 'פַעל', 'פיעל']
    errors = defaultdict(lambda: [])
    for file in sorted(os.listdir(path), key=lambda x: int(re.findall('^\d+', x)[0])):
        print(file)
        root = parse_file(file)
        entry_tags = root.findall('.//entry')
        for entry in entry_tags:
            _id = str_element(entry)[:120].replace('\n', ' ')
            hws = entry.findall('head-word')
            if not hws:
                errors['no headword'].append(_id)
            else:
                hw = entry.findtext('head-word')
            if hws and re.search('|'.join(binyanim), hw):
                errors['binyan in headword'].append(_id)
            if all(c.tag == 'head-word' for c in entry.getchildren()):
                errors['nothing but headword'].append(_id)
            elif hws:
                next_element = hws[0].getnext()
                definition = next_element.find('.//definition')
                if definition is not None:
                    text = get_text_excluding_tag(definition)
                    if text.strip():
                        text = text.split()[0]
                        first_element_word = get_text_excluding_tag(next_element, []).split()[0]
                        if text == first_element_word and has_cantillation(text, True):
                            errors['nikkud in first definition'].append(_id)
            text = get_text_excluding_tag(entry)
            if text.count('|') > 1:
                errors['more than one pipe'].append(_id)

    with open('errors in krupnik data.txt', 'w') as fp:
        for k, v in errors.items():
            fp.write(f'{k}\n\t' + "\n\t".join(v) + '\n\n')
