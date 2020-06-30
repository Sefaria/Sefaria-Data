import re
import csv
import os
import django
django.setup()
from sefaria.model import *
from rif_utils import tags_map, netlen, path
from sefaria.utils.talmud import daf_to_section

lengthes = {}
with open('masechet_leng.csv', encoding='utf-8', newline='') as file:
    lengthes = {row['masechet']: row['last'] for row in csv.DictReader(file)}

def check_pages(data: list, masechet: str) -> str:
    #checking number of pages against prod
    pages_in_file = daf_to_section(data[-1]['page.section'].split(':')[0])
    pages = daf_to_section(lengthes[masechet])
    if pages_in_file != pages:
        return '{} pages in rif but {} in data'.format(pages, pages_in_file)

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

for masechet in list(tags_map):
    file_data = []
    for root, dirs, files in os.walk(os.getcwd()+'/rif_csv'):
        for file in files:
            if masechet in file:
                with open(path+'/rif_csv/'+file, encoding='utf-8', newline='') as file:
                    file_data = list(csv.DictReader(file))

    new = []
    if check_pages(file_data, masechet) != None:
        new.append({'page.section': check_pages(file_data, masechet)})

    for row in file_data:
        line = row['content']
        #if check_tag_balance(line, masechet) != []:
            #row['tag balance'] = ';'.join(check_tag_balance(line, masechet))
        if check_len(line):
            row['length'] = check_len(line)
        new.append(row)

    with open(path+'/csv_reports/report_{}.csv'.format(masechet), 'w', encoding='utf-8', newline='') as fp:
        awriter = csv.DictWriter(fp, fieldnames=['page.section', 'content', 'length'])
        awriter.writeheader()
        for item in new:
            awriter.writerow(item)
