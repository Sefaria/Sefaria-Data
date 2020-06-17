import re
import django
django.setup()
from sefaria.model import *
from rif_utils import tags_map, netlen, segmented_rif_files, path

def check_pages(data: str, masechet: str) -> str:
    #checking number of pages against prod
    if len(Ref('Rif ' + masechet).text('he').text) != data.count('@20'):
        return '{} pages in rif but {} @20s in data'.format(len(Ref('Rif '+masechet).text('he').text), data.count('@20'))

def check_tag_balance(section: str, masechet: str) -> str:
    #checking balance of dependent tags in section
    problems = []
    begin_tag = r'(?:{}|{}|{})'.format(*[tags_map[masechet][tag] for tag in ['gemara_refs', 'notes', 'tanakh_refs']])
    if len(re.findall(begin_tag, section)) != section.count(tags_map[masechet]['end_tag']):
        problems.append('{} begin tags and {} end tags'.format(len(re.findall(begin_tag, section)), section.count(tags_map[masechet]['end_tag'])))
    if section.count('@44') != section.count('@55'):
        problems.append('{} bold tags and {} unbold tags'.format(section.count('@44'), section.count('@55')))
    return problems

def check_len(section: str) -> str:
    #check if section is too long
    if netlen(section) > 125:
        return 'sectoin has {} words'.format(netlen(section))

for en_masechet, heb_masechet, file in segmented_rif_files:
    file_data = file.read()
    report = []
    page = 'א.'
    sec = 1

    if check_pages(file_data, en_masechet) != None:
        report.append(check_pages(file_data, en_masechet))
    for line in file_data.split('\n'):
        if '@20' in line:
            page = line[3:]
            sec = 1
            continue

        if check_tag_balance(line, en_masechet) != []:
            report.append('page {} paragraph {}: {}'.format(page, sec, ';'.join(check_tag_balance(line, en_masechet))))
        if check_len(line):
            report.append('page {} paragraph {}: {}'.format(page, sec, check_len(line)))
        sec += 1

    with open(path+'/first_reports/report_{}.txt'.format(en_masechet), 'w') as fp:
        fp.write('\n'.join(report))
