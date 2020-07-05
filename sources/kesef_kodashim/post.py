import django
django.setup()
import urllib
import json
from sources import functions
from sefaria.model.schema import *
from sefaria.model import *
import csv

schema = JaggedArrayNode()
schema.add_primary_titles("Kesef Kodashim on Shulchan Arukh, Choshen Mishpat", "כסף קדשים על שולחן ערוך חושן משפט")
schema.add_structure(["Siman", "Paragraph"])
schema.validate()

index_dict = {
    'title': "Kesef Kodashim on Shulchan Arukh, Choshen Mishpat",
    'categories': ["Halakhah", "Shulchan Arukh", "Commentary"],
    'schema': schema.serialize(),
    'dependence' : 'Commentary'
}

functions.post_index(index_dict)


text = []
links = []
with open('kesef kodashim.csv', newline='', encoding='utf-8') as file:
    dictin = csv.DictReader(file)

    preSiman = 0
    simantext = []

    for row in dictin:
        if 'Kesef' not in row['Index Title']:
            pass
        else:
            siman = row['Index Title'].split()[-1].split(':')[0]
            if siman == preSiman:
                simantext.append(row['Kesef Kodashim on Shulchan Arukh, Choshen Mishpat'])
            else:
                text.append(simantext)
                if int(siman) - int(preSiman) != 1:
                    for n in range(0, int(siman) - int(preSiman) - 1):
                        text.append([])
                simantext = [row['Kesef Kodashim on Shulchan Arukh, Choshen Mishpat']]
                preSiman = siman

            if row['link'] == '':
                continue
            if any(word in row['link']   for word in ['Siftei', 'Ketzot']):
                row['link'] += ':1'
            if Ref(row['link']).text('he').text == '' or Ref(row['link']).text('he').text == []:
                print('link to null, ', row['link'])
            else:
                links.append({
                "refs": [row['link'], row['Index Title']],
                "type": "Commentary",
                "auto": True,
                "generated_by": 'kesef kodashim'
                })
                if row['link'][:4] != 'Shul':
                    reflinks = Ref(row['link']).linkset()
                    n = 0
                    for item in reflinks:
                        if (item.generated_by == 'Shulchan Arukh Parser' or item.generated_by == 'taz cm') and item.refs[0][:4] == 'Shul' and item.type == 'commentary':
                            links.append({
                            "refs": [item.refs[0], row['Index Title']],
                            "type": "Commentary",
                            "auto": True,
                            "generated_by": 'kesef kodashim'
                            })
                            n += 1
                    if n != 1:
                        print(n, ' links for ', row['Index Title'])

    text.append(simantext)
    text = text[1:]

text_version = {
    'versionTitle': "Apei Ravrevei: Shulchan Aruch Even HaEzer, Lemberg, 1886",
    'versionSource': "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002097680",
    'language': 'he',
    'text': text
}

functions.post_text('Kesef Kodashim on Shulchan Arukh, Choshen Mishpat', text_version)
functions.post_link(links)
