import django
django.setup()
import urllib
import json
from sources import functions
from sefaria.model.schema import *
from sefaria.model import *
from data_utilities.util import getGematria as gematria
import copy

def dhtolink(siman, par, dh, plink):
    dh += ' '
    if siman == 297 and par == 3:
        link = "Shulchan Arukh, Yoreh De'ah 297:41"
    elif siman == 227:
        link = "Shulchan Arukh, Yoreh De'ah 227:3"
    elif siman == 260:
        link = "Shulchan Arukh, Yoreh De'ah 260:1"
    elif 'סע"ב' in dh:
        link = "Shulchan Arukh, Yoreh De'ah 91:2"
    elif any(word in dh for word in ['סעיף', "סעי'"]):
        if 'סעיף יו"ד' in dh:
            link = "Shulchan Arukh, Yoreh De'ah {}:{}".format(siman, 10)
        elif 'סעי"ב' in dh:
            link = "Shulchan Arukh, Yoreh De'ah {}:{}".format(siman, 12)
        elif 'בבאה"ט' in dh:
            link = "Ba'er Hetev on Shulchan Arukh, Yoreh De'ah {}:12".format(siman)
        else:
            start = 5 + dh.index('סעי')
            end = dh.index(' ', start)
            seif = gematria(dh[start:end])
            link = "Shulchan Arukh, Yoreh De'ah {}:{}".format(siman, seif)
    elif siman == 23:
        link = "Shulchan Arukh, Yoreh De'ah 23:1"
    elif dh == 'pri ':
        link = "Pri Megadim on Yoreh De'ah, Siftei Da'at 13:3:1"
    elif 'ש"ך' in dh:
        if 'שם בש"ך' in dh and siman == 242:
            link = "Siftei Kohen on Shulchan Arukh, Yoreh De'ah {}:{}:1".format(siman, 68)
        elif 'דיני ספק ספיקא בש"ך' in dh:
            link = "Siftei Kohen on Shulchan Arukh, Yoreh De'ah 110:63:2"
        elif 'ס"ק' in dh:
            start = 4 + dh.index('ס"ק')
            end = dh.index(' ', start)
            seif = gematria(dh[start:end])
            link = "Siftei Kohen on Shulchan Arukh, Yoreh De'ah {}:{}:1".format(siman, seif)
        else:
            print('error. shach withno seif', siman, dh)
            return '', []
    elif 'ט"ז' in dh and 'סט"ז' not in dh:
        if 'בפתיחה' in dh:
            seif = 1
        elif 'סק"ב' in dh:
            seif = 2
        elif 'ס"ק' in dh:
            start = 4 + dh.index('ס"ק')
            end = dh.index(' ', start)
            seif = gematria(dh[start:end])
        else:
            print('error. taz withno seif', siman, dh)
            return '', []
        link = "Turei Zahav on Shulchan Arukh, Yoreh De'ah {}:{}".format(siman, seif)
    elif any('ס' in word and '"' in word and 'ק' not in word for word in dh.split()):
        for word in dh.split():
            if 'ס' in word and '"' in word:
                seif = gematria(word) - 60
                link = "Shulchan Arukh, Yoreh De'ah {}:{}".format(siman, seif)
    elif any(word in dh for word in ['ש"ע', 'בהג"ה']):
        if plink[:4] == 'Shul':
            link = plink
        else:
            print('error. sa withno seif', siman, dh)
            return '', []
    elif 'שם' in dh:
        if plink != '':
            link = plink
        else:
            print('error. ibid to null', siman, dh)
            return '', []
    else:
        print('error. no ref', siman, dh)
        return '', []

    if Ref(link).text('he').text == '' or Ref(link).text('he').text == []:
        print('error. ref doesnt exist', siman, dh)
        return '', []

    linkdict = {
    "refs": ["Yad Avraham on Shulchan Arukh, Yoreh De'ah {}:{}".format(siman, par), link],
    "type": "Commentary",
    "auto": True,
    "generated_by": 'yad avraham'
    }
    links = [copy.deepcopy(linkdict)]

    if link[:4] != 'Shul':
        if dh == 'pri ':
            link = "Siftei Kohen on Shulchan Arukh, Yoreh De'ah 13:3:1"
            linkdict['refs'][1] = link
            links.append(copy.deepcopy(linkdict))
        for item in Ref(link).linkset():
            if item.generated_by == 'Shulchan Arukh Parser' or item.generated_by == 'Torat_Emet_uploader':
                for ref in item.refs:
                    if ref[:4] == 'Shul':
                        linkdict['refs'][1] = ref
                        links.append(linkdict)

    return link, links


server = 'http://draft.sandbox.sefaria.org'
#server = 'http://localhost:8000'

functions.add_term('Yad Avraham', 'יד אברהם', server=server)

record = SchemaNode()
record.add_primary_titles("Yad Avraham on Shulchan Arukh, Yoreh De'ah", 'יד אברהם על שולחן ערוך יורה דעה')

node = JaggedArrayNode()
node.key = 'default'
node.default = True
node.add_structure(['Siman', 'Pararaph'])
record.append(node)
record.validate()

index_dict = {
    'collective_title': 'Yad Avraham',
    'title': "Yad Avraham on Shulchan Arukh, Yoreh De'ah",
    'categories': ["Halakhah", "Shulchan Arukh", "Commentary"],
    'schema': record.serialize(),
    'dependence' : 'Commentary',
    'base_text_titles': ["Shulchan Arukh, Yoreh De'ah"]
}

functions.post_index(index_dict, server = server)

with open('yadavraham1', encoding='utf-8') as file:
    data=file.readlines()

oldsiman = 0
text = []
content = ''
links = []
simantext = []
link = ''

for line in data:
    line = line.replace('\n', '').strip()

    if line == '':
        continue

    if line[:3] == '@22':
        if content != '':
            simantext.append(content)
            text.append(simantext)
            link, newlinks = dhtolink(siman, par, dh, link)
            links += newlinks
        siman = gematria(line.split()[-1])
        if siman - oldsiman != 1:
            for n in range (0, siman - oldsiman -1):
                text.append([])
        oldsiman = siman
        content = line.replace('@22', '') + ' '
        if siman == 23:
            content = content[:-1]
        par = 1
        first = True
        link = ''
        simantext = []
        dh = ''

    elif line[:3] == '@11':
        if '*בפמ"ג' in line:
            simantext.append(content)
            link, newlinks = dhtolink(siman, par, dh, link)
            links += newlinks
            par += 1
            content = line.replace('@11*', '<b>').replace('@33', '</b>')
            dh = 'pri'
        elif '*שאלה' in line:
            simantext.append(content)
            link, newlinks = dhtolink(siman, par, dh, link)
            links += newlinks
            par += 1
            content = '<b>' + line[4:] + '</b>'
            dh = ''
        elif ')' in line.split('@33')[0]:
            if first:
                first = False
            else:
                simantext.append(content)
                link, newlinks = dhtolink(siman, par, dh, link)
                links += newlinks
                par += 1
                content = ''
            dh = line.split(')')[0]
            content = '<b>' + content + line.replace('@11', '').replace('@33', '</b>')
        else:
            content += '<br>' + line.replace('@11', '<b>').replace('@33', '</b>')

    else:
        print('no tag. 1', line)


for n in range(2,5):
    with open('yadavraham{}'.format(n), encoding='utf-8') as file:
        data=file.readlines()

    for line in data:
        line = line.replace('\n', '').strip()

        if line == '':
            continue

        if '@22' in line:
            simantext.append(content)
            link, newlinks = dhtolink(siman, par, dh, link)
            links += newlinks
            par += 1
            if any(word in line for word in ['סימן', "סי'"]):
                text.append(simantext)
                siman = gematria(line.split()[1])
                if siman - oldsiman != 1:
                    for n in range (0, siman - oldsiman -1):
                        text.append([])
                oldsiman = siman
                par = 1
                link = ''
                simantext = []
            dh = line
            content = '<b>' + line[3:] + ' '
            if line == '@22':
                content = content[:-1]
            first = True

        elif '@11' in line:
            if first:
                content += line[3:].replace('@33', '</b>').replace('@44', '<b>').replace('@55', '</b>').replace(' </b>', '</b> ')
                first = False
            else:
                simantext.append(content)
                link, newlinks = dhtolink(siman, par, dh, link)
                links += newlinks
                par += 1
                dh = ''
                content = '<b>' + line[3:].replace('@33', '</b>').replace('@44', '<b>').replace('@55', '</b>').replace(' </b>', '</b> ')

        elif line[:3] == '@44':
            content += '<br>' + line.replace('@44', '<b>').replace('@55', '</b>').replace(' </b>', '</b> ')

        else:
            print('no tag.', n, line)

simantext.append(content)
text.append(simantext)
link, newlinks = dhtolink(siman, par, dh, link)
links += newlinks

text_version = {
    'versionTitle': "Ashlei Ravrevei: Shulchan Aruch Yoreh Deah, Lemberg, 1888",
    'versionSource': "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002097765",
    'language': 'he',
    'text': text
}

functions.post_text("Yad Avraham on Shulchan Arukh, Yoreh De'ah", text_version, server = server)
functions.post_link(links, server = server)
