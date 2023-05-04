import django
django.setup()
import urllib
import json
from sources import functions
from sefaria.model.schema import *
from sefaria.model import *
import re
from parsing_utilities.util import getGematria as gematria

server = 'http://draft.sandbox.sefaria.org'
#server = 'http://localhost:8000'

functions.add_term('Beit Meir', 'בית מאיר', server=server)

record = SchemaNode()
record.add_primary_titles("Beit Meir on Shulchan Arukh, Even HaEzer", 'בית מאיר על שולחן ערוך אבן העזר')

node = JaggedArrayNode()
node.add_primary_titles('Introduction', 'הקדמה')
node.add_structure(['Pararaph'])
record.append(node)

node = JaggedArrayNode()
node.key = 'default'
node.default = True
node.add_structure(['Siman', 'Pararaph'])
record.append(node)

node = JaggedArrayNode()
node.add_primary_titles("Seder HaGet", 'סדר הגט')
node.add_structure(['Pararaph'])
record.append(node)

node = JaggedArrayNode()
node.add_primary_titles("Seder Halitzah", 'סדר חליצה')
node.add_structure(['Pararaph'])
record.append(node)

node = JaggedArrayNode()
node.add_primary_titles("Tzal'ot HaBayit", 'צלעות הבית')
node.add_structure(['Siman', 'Pararaph'])
record.append(node)

record.validate()

index_dict = {
    'collective_title': 'Beit Meir',
    'title': "Beit Meir on Shulchan Arukh, Even HaEzer",
    'categories': ["Halakhah", "Shulchan Arukh", "Commentary"],
    'schema': record.serialize(),
    'dependence' : 'Commentary',
    'base_text_titles': ["Shulchan Arukh, Even HaEzer"]
}

functions.post_index(index_dict, server = server)

with open('beitmeir.txt', encoding = 'utf-8') as file:
    data = file.readlines()

introduction = []
textsim = []
simanim = []
get = []
halitza = []
tzalot = []
main = False
links = []
par = 1
preSiman = 0
first = False

for line in data:
    line = line.replace('\n', '').strip()

    if line == '':
        continue

    elif 'בית מאיר אבן העזר ' in line:
        first = not first
        if first:
            continue
        seif = ''
        par = 1
        if 'הקדמה' in line:
            siman = ''
        elif 'העזר סימן' in line:
            if  main:
                simanim.append(textsim)
                textsim = []
            siman = gematria(line.split()[-1])
            par = 1
            main = True
            if siman - preSiman != 1:
                for n in range(1, siman - preSiman):
                    simanim.append([])
            preSiman = siman
        elif 'הגט' in line:
            siman = "Seder HaGet"
            simanim.append(textsim)
        elif 'חליצה' in line:
            siman = "Seder Halitzah"
        elif 'צלעות הבית' in line:
            siman = 'tzalot'
            if main:
                main = False
                print(tzalot)
            else:
                tzalot.append(textsim)
            textsim = []
        else:
            print('error', line)
        continue

    elif line.split()[0] == 'סעיף' and len(line.split()) == 2:
        seif = gematria(line.split()[-1])
        continue

    else:
        if siman == '':
            introduction.append(line)
        elif siman == 'Seder HaGet':
            get.append(line)
        elif siman == 'Seder Halitzah':
            halitza.append(line)
        else:
            textsim.append(line)

        if seif != '':
            if type(siman) == str:
                ref1 = 'Shulchan Arukh, Even HaEzer, {} {}'.format(siman, seif)
                ref2 = 'Beit Meir on Shulchan Arukh, Even HaEzer, {} {}'.format(siman, par)
            else:
                ref1 = 'Shulchan Arukh, Even HaEzer {}:{}'.format(siman, seif)
                ref2 = 'Beit Meir on Shulchan Arukh, Even HaEzer {}:{}'.format(siman, par)
            ref = Ref(ref1).text('he').text
            if ref == '' or ref == []:
                print('no such seif', siman, seif)
            else:
                links.append({
                "refs": [ref1, ref2],
                "type": "Commentary",
                "auto": True,
                "generated_by": 'beit meir'
                })
        par += 1

tzalot.append(textsim)


text = [introduction, simanim, get, halitza, tzalot]
conts = [', Introduction', '', ', Seder HaGet', ', Seder Halitzah', ", Tzal'ot HaBayit"]
for i, j in zip(text, conts):
    text_version = {
        'versionTitle': "Apei Ravrevei: Shulchan Aruch Even HaEzer, Lemberg, 1886",
        'versionSource': "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002097680",
        'language': 'he',
        'text': i
    }
    functions.post_text('Beit Meir on Shulchan Arukh, Even HaEzer{}'.format(j), text_version, server = server)

functions.post_link(links, server = server)
