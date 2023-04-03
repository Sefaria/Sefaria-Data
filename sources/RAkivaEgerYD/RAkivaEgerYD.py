import django
django.setup()
import urllib
import json
from sources import functions
from sefaria.model.schema import *
from sefaria.model import *
import csv
import re
from parsing_utilities.util import getGematria as gematria
import copy

def tags(text):
    for pair in [['@11', '@33'], ['@44', '@55'], ['@66', '@77']]:
        text = re.sub(pair[0] + '(.*?)' + pair[1], r'<b>\1</b>', text)
    for word in ['@11', '@33', '@44', '@55', '@66', '@77', '@22', '@88', '@00']:
        text = text.replace(word, '')
    return text

def sk(text):
    if 'ססק"' in text:
        return gematria(text) - 220
    elif  'ס"ק' in text or any('סק' in word and '"' in word for word in text.split()):
        if 'בסוף' in text:
            return gematria(text) - 308
        elif 'סוף' in text:
            return gematria(text) - 306
        else:
            return gematria(text) - 160
    else:
        return -1

schema = JaggedArrayNode()
schema.add_primary_titles("Rabbi Akiva Eiger on Shulchan Arukh, Yoreh De'ah", "הגהות רבי עקיבא איגר על שלחן ערוך יורה דעה")
schema.add_structure(["Siman", "Paragraph"])
schema.validate()

index_dict = {
    'collective_title': 'Rabbi Akiva Eiger',
    'title': "Rabbi Akiva Eiger on Shulchan Arukh, Yoreh De'ah",
    'categories': ["Halakhah", "Shulchan Arukh", "Commentary", "Rabbi Akiva Eiger"],
    'schema': schema.serialize(),
    'dependence' : 'Commentary',
    'base_text_titles': ["Shulchan Arukh, Yoreh De'ah"]
}
server = 'http://draft.sandbox.sefaria.org'
functions.post_index(index_dict, server)

text = []
links = []
nekudot = False
link3 = ''
lonk = ''
with open('rae on sa yd.csv', newline='', encoding='utf-8') as file:
    dictin = csv.DictReader(file)

    preSiman = '1'
    simantext = []
    par = 0

    for row in dictin:
        if row['text'] == '':
            continue
        siman = row['siman']
        if siman == preSiman:
            simantext.append(tags(row['text']))
            par += 1
        else:
            text.append(simantext)
            if int(siman) - int(preSiman) != 1:
                for n in range(0, int(siman) - int(preSiman) - 1):
                    text.append([])
            simantext = [tags(row['text'])]
            preSiman = siman
            par = 1
            link = ''

        if  row['responsa'] == '':
            print(row['text'])
        if row['responsa'][0] != '(':
            link = "Shulchan Arukh, Yoreh De'ah {}:{}".format(str(siman), str(row['seif']))
        else:
            dh = row['responsa'].split(')')[0][1:]
            if 'סעיף' in dh:
                link = "Shulchan Arukh, Yoreh De'ah {}:{}".format(str(siman), str(row['seif']))
            elif dh.split()[0] == 'ש"ך':
                if dh == 'ש"ך':
                    link = "Siftei Kohen on Shulchan Arukh, Yoreh De'ah" + ' ' + row['responsa'].split(' ', 1)[1]
                    link = link.replace(' ,', ',')
                else:
                    seif = sk(dh.split(' ', 1)[1])
                    if seif < 0:
                        print(siman, ' no seif katan ', dh, seif)
                        continue
                    else:
                        link = "Siftei Kohen on Shulchan Arukh, Yoreh De'ah {}:{}:1".format(str(siman), str(seif))
            elif  dh.split()[0] == 'ט"ז':
                seif = sk(dh.split(' ', 1)[1])
                if seif < 0:
                    print(siman, ' no seif katan ', dh)
                    continue
                else:
                    link = "Turei Zahav on Shulchan Arukh, Yoreh De'ah {}:{}".format(siman, seif)
            elif any(word in dh for word in['באר הגולה', 'באה"ג']):
                if 'מ"ו' in dh:
                    seif = 46
                elif 'בהגהת' in dh:
                    seif = 123
                else:
                    seif = gematria(dh.split()[-1])
                link = "Be'er HaGolah on Shulchan Arukh, Yoreh De'ah {}:{}".format(siman, seif)
            elif any(word in dh for word in ['בנקודות', 'בנקה"כ']):
                seif = sk(dh.replace('בנקה"כ', '').replace('בנקודות הכסף', ''))
                if seif < 0:
                    link = "Turei Zahav on Shulchan Arukh, Yoreh De'ah 117:4"
                    link3 =  "Nekudat HaKesef on Shulchan Arukh, Yoreh De'ah 117:2"
                    nekudot = True
                else:
                    link = "Turei Zahav on Shulchan Arukh, Yoreh De'ah {}:{}".format(siman, seif)
                    nekudot = True
            elif any(dh == word for word in['שם', 'בא"ד', 'בהג"ה', 'שם בהג"ה', 'שם בסופו', 'שם בסה"ד', 'שם בהגה"ה', 'בא"ד בסוף', 'בא"ד בסופו']):
                pass
            elif dh[:3] == 'שם ':
                seif = sk(dh.split(' ', 1)[1])
                if seif < 0:
                    print(siman, ' no seif katan or seif ', dh)
                    continue
                else:
                    link = link.split(':', 1)[0] + ':' + str(seif)
                    if link[:3] == 'Sif':
                        link += ':1'
            elif any('ס' in word and '"' in word for word in dh.split()):
                link = "Shulchan Arukh, Yoreh De'ah {}:{}".format(str(siman), str(row['seif']))
            else:
                print(siman, ' unknown ref ', dh)
                continue

            if link == '':
                print(dh, siman, par)
            if Ref(link).text('he').text == '' or Ref(link).text('he').text == []:
                print('link to null, ', link)
            else:
                address = "Rabbi Akiva Eiger on Shulchan Arukh, Yoreh De'ah {}:{}".format(str(siman), str(par))
                linkdict = ({
                "refs": [link, address],
                "type": "Commentary",
                "auto": True,
                "generated_by": 'R Akiva Eiger'
                })
                links.append(copy.deepcopy(linkdict))
                if link[:4] != 'Shul':
                    linkdict['refs'][0] = "Shulchan Arukh, Yoreh De'ah {}:{}".format(str(siman), row['seif'])
                    links.append(copy.deepcopy(linkdict))
                if nekudot:
                    if link3 == '':
                        refLinks = Ref(link).linkset()
                        for item in refLinks:
                            for ref in item.refs:
                                if 'Nekudat' in ref:
                                    link3 = ref
                    linkdict['refs'][0] = link3
                    links.append(copy.deepcopy(linkdict))
                    nekudot = False
                    link3 = ''



    text.append(simantext)

text_version = {
    'versionTitle': "Ashlei Ravrevei: Shulchan Aruch Yoreh Deah, Lemberg, 1888",
    'versionSource': "http://primo.nli.org.il/primo-explore/fulldisplay?vid=NLI&docid=NNL_ALEPH002097765&context=L",
    'language': 'he',
    'text': text
}

functions.post_text("Rabbi Akiva Eiger on Shulchan Arukh, Yoreh De'ah", text_version, server = server)
functions.post_link(links, server)
