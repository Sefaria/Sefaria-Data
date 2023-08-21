import django
django.setup()
from sefaria.model import *
import re

def link_misnah(title):
    pass

def link_bavli(title):
    print(title)
    for page in Ref(title).all_subrefs():
        base = 'gmara'
        for comment in page.all_segment_refs():
            text = comment.text('he').text
            if '<b>' not in text:
                dh = text.split('.')[0]
                if len(dh) > 30:
                    dh = re.split(" וכו['׳] ", text)[0]
                    if len(dh) > 30:
                        continue
            else:
                dh = text.split('</b>')[0].replace('<b>', '')
            if  re.search('ד["״]ה', dh):
                base = '' #find commentrator
            elif re.search('^(?:שם|בא[״"]ד|בסה"ד)', dh):
                pass #in gmara find segment, other link to the same base segment
            elif base != 'gmara':
                continue


for title in library.get_indices_by_collective_title("Haggahot Ya'avetz"):
    index = library.get_index(title)
    index.versionState().refresh()
    base = library.get_index(index.base_text_titles[0])
    if 'Seder' not in base.categories[-1]:
        continue
    if 'Mishnah' in base.categories:
        link_misnah(title)
    elif 'Bavli' in base.categories:
        link_bavli(title)
