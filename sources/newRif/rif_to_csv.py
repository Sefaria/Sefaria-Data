import csv
import re
from rif_utils import segmented_rif_files, path
from sefaria.utils.talmud import section_to_daf

empties = {'Pesachim': ['18b'], 'Nedarim': ['4a'], 'Avodah Zarah': ['36a'], 'Menachot': ['10b'], 'Chullin': ['43b', '44a']}

def txt_to_csv(data: str, masechet: str) -> list:
    data = [page for page in re.split(r'@20.*?\n', data) if page != '']
    csv_dicts = []
    n = 0
    for page in data:
        try:
            while section_to_daf(n+1) in empties[masechet]:
                n += 1
        except KeyError:
            pass
        page = [section for section in page.split('\n') if section.replace('\ufeff', '').strip() != '']
        for m, section in enumerate(page):
            csv_dicts.append({'page.section': '{}:{}'.format(section_to_daf(n+1), m+1),
                'content': section})
        n += 1
    return csv_dicts

for en_masechet, heb_masechet, file_data in segmented_rif_files:
    with open(path+'/rif_csv/rif_{}.csv'.format(en_masechet), 'w', encoding='utf-8', newline = '') as file:
        awriter = csv.DictWriter(file, fieldnames=['page.section', 'content'])
        awriter.writeheader()
        for item in txt_to_csv(file_data, en_masechet): awriter.writerow(item)
