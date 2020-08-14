import django
django.setup()
import urllib
import json
from sources import functions
from sefaria.model.schema import *
from sefaria.model import *
import csv

server = 'http://draft.sandbox.sefaria.org'
functions.add_term('Kessef HaKodashim', "כסף הקדשים", server=server)

schema = JaggedArrayNode()
schema.add_primary_titles("Kessef HaKodashim on Shulchan Arukh, Choshen Mishpat", "כסף הקדשים על שולחן ערוך חושן משפט")
schema.add_structure(["Siman", "Paragraph"])
schema.validate()

index_dict = {
    'collective_title': 'Kessef HaKodashim',
    'title': "Kessef HaKodashim on Shulchan Arukh, Choshen Mishpat",
    'categories': ["Halakhah", "Shulchan Arukh", "Commentary"],
    'schema': schema.serialize(),
    'dependence' : 'Commentary',
    'base_text_titles': ["Shulchan Arukh, Choshen Mishpat"]
}

functions.post_index(index_dict, server = server)


text = []
links = []
with open('kesef kodashim.csv', newline='', encoding='utf-8') as file:
    dictin = csv.DictReader(file)

    preSiman = 0
    simantext = []

    for row in dictin:
        if 'Kessef' not in row['Index Title']:
            pass
        else:
            siman = row['Index Title'].split()[-1].split(':')[0]
            if siman == preSiman:
                simantext.append(row['Kessef HaKodashim on Shulchan Arukh, Choshen Mishpat'])
            else:
                text.append(simantext)
                if int(siman) - int(preSiman) != 1:
                    for n in range(0, int(siman) - int(preSiman) - 1):
                        text.append([])
                simantext = [row['Kessef HaKodashim on Shulchan Arukh, Choshen Mishpat']]
                preSiman = siman

            if row['link'] == '':
                continue
            if any(word in row['link'] for word in ['Siftei', 'Ketzot']):
                row['link'] += ':1'
            if Ref(row['link']).text('he').text == '' or Ref(row['link']).text('he').text == []:
                print('link to null, ', row['link'])
            else:
                links.append({
                "refs": [row['link'], row['Index Title']],
                "type": "Commentary",
                "auto": True,
                "generated_by": 'kessef hakodashim'
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
                            "generated_by": 'kessef hakodashim'
                            })
                            n += 1
                    if n != 1:
                        print(n, ' links for ', row['Index Title'])

    text.append(simantext)
    text = text[1:]

text_version = {
    'versionTitle': "Shulhan Arukh, Hoshen ha-Mishpat, Lemberg, 1898",
    'versionSource': "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002097680",
    'language': 'he',
    'text': text
}

functions.post_text('Kessef HaKodashim on Shulchan Arukh, Choshen Mishpat', text_version, server = server)
functions.post_link(links, server = server)
