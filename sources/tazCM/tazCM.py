import django
django.setup()
import urllib
import json
from sources import functions
from sefaria.model.schema import *
from sefaria.model import *
import csv

schema = JaggedArrayNode()
schema.add_primary_titles("Turei Zahav on Shulchan Arukh, Choshen Mishpat", "טורי זהב על שולחן ערוך חושן משפט")
schema.add_structure(["Siman", "Paragraph"])
schema.validate()

index_dict = {
    'collective_title': 'Turei Zahav',
    'title': "Turei Zahav on Shulchan Arukh, Choshen Mishpat",
    'categories': ["Halakhah", "Shulchan Arukh", "Commentary", "Turei Zahav"],
    'schema': schema.serialize(),
    'dependence' : 'Commentary',
    'base_text_titles': ["Shulchan Arukh, Choshen Mishpat"]
}
#server = 'http://draft.sandbox.sefaria.org'
server = 'http://localhost:8000'
functions.post_index(index_dict, server = server)


text = []
links = []
with open('taz cm.csv', newline='', encoding='utf-8') as file:
    dictin = csv.DictReader(file)

    preSiman = 0
    simantext = []

    for row in dictin:
        if 'Zahav' not in row['Index Title']:
            pass
        else:
            siman = row['Index Title'].split()[-1].split(':')[0]
            if siman == preSiman:
                simantext.append(row['Turei Zahav on Shulchan Arukh, Choshen Mishpat'])
            else:
                text.append(simantext)
                if int(siman) - int(preSiman) != 1:
                    for n in range(0, int(siman) - int(preSiman) - 1):
                        text.append([])
                simantext = [row['Turei Zahav on Shulchan Arukh, Choshen Mishpat']]
                preSiman = siman

            if row['link'] == '':
                continue
            if Ref(row['link']).text('he').text == [] or Ref(row['link']).text('he').text == '':
                print('link to null, ', row['link'])
            elif 'Beit' in row['link']:
                links.append({
                "refs": [row['link'] + ':1', row['Index Title']],
                "type": "Commentary",
                "auto": True,
                "generated_by": 'taz cm'
                })
                links.append({
                "refs": [row['link'].replace('Beit Yosef', 'Tur'), row['Index Title']],
                "type": "Commentary",
                "auto": True,
                "generated_by": 'taz cm'
                })
            else:
                links.append({
                "refs": [row['link'], row['Index Title']],
                "type": "Commentary",
                "auto": True,
                "generated_by": 'taz cm'
                })


    text.append(simantext)
    text = text[1:]

text_version = {
    'versionTitle': "Shulhan Arukh, Hoshen ha-Mishpat, Lemberg, 1898",
    'versionSource': "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002097680",
    'language': 'he',
    'text': text
}

functions.post_text('Turei Zahav on Shulchan Arukh, Choshen Mishpat', text_version, server = server)
functions.post_link(links, server = server)
