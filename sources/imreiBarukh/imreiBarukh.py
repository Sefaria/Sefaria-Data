import re
import django
django.setup()
import urllib
import json
from sources import functions
from sefaria.model.schema import *
from sefaria.model import *
from parsing_utilities.util import getGematria as gematria
import copy

taz = [3, 1, 13, 13,  3, 5, 3, 1, 10, 10, 14, 10, 1]
smigo = [6, 6, 9, 10, 15, 17, 22, 25]
nmigo = [1, 1, 1, 1, 14]

def deleteMany(string, todel):
    for item in todel:
        string = string.replace(item, '')
    return string

def getsiman(line):
    if '$' in line:
        return int(line[1:])
    else:
        return gematria(line)

def getdh(line, n):
    dh = ''
    if n == 1:
        dh = deleteMany(line, ['@11', '(")'])
    elif n == 4:
        dh = line[3:line.index('@33')]
    if dh == '':
        if '(")' in line:
            dh = line[3:line.index('(")')]
        elif '. נ"ב' in line:
            dh = line[3:line.index('. נ"ב')]
        if dh == '':
            print('error, no dh', n, line)
            dh = line
    return dh

def getOt(dh, n, sa = False):
    if dh[:6] == 'המשפט ':
        dh = dh[6:]
    if dh.strip() == '':
        print('no sk', n, dh)
        return '$'
    elif any('הנ"ל' in word for word in dh.split()[0:2]):
        return '$'
    elif dh[:3] == 'ס"ק':
        ot = deleteMany(dh[3:].split()[0], ['"', "'", ')', ']', '('])
        if ot != functions.numToHeb(gematria(ot)):
            print('ot isnt gematria, returning first ot gematria', n, dh)
            return gematria(ot[0])
        return gematria(ot)
    elif dh[:2] == 'סק':
        ot = deleteMany(dh[2:].split()[0], ['"', "'", ')', ']'])
        if ot != functions.numToHeb(gematria(ot)):
            print('ot isnt gematria', n, dh)
        return gematria(ot)
    else:
        ot = deleteMany(dh.split()[0], ['"', "'", ')', ']', '.'])
        if sa:
            for word in ['סעיף', "סעי'"]:
                if word in dh:
                    dh += ' '
                    start = len(word) + 1 + dh.index(word)
                    end = dh.index(' ', start)
                    ot = deleteMany(dh[start:end], ['"', "'", ')', ']'])
                    if ot != functions.numToHeb(gematria(ot)):
                        print('ot isnt gematria', n, dh)
                    return gematria(ot)
            if any(word[0] == 'ס' and '"' in word for word in dh.split()):
                for word in dh.split():
                    if word[0] == 'ס' and '"' in word:
                        ot = deleteMany(word[1:], ['"', "'", ')', ']'])
                        if ot != functions.numToHeb(gematria(ot)):
                            print('ot isnt gematria', n, dh)
                        return gematria(ot)
            for word in ["ס'", "סי'"]:
                if word in dh:
                    dh += ' '
                    start = len(word) + 1 + dh.index(word)
                    end = dh.index(' ', start)
                    ot = deleteMany(dh[start:end], ['"', "'", ')', ']'])
                    if ot != functions.numToHeb(gematria(ot)):
                        print('ot isnt gematria', n, dh)
                    return gematria(ot)
        if ot == functions.numToHeb(gematria(ot)):
            return gematria(ot)
        if 'סעיף קטן' in dh:
            return 2
        if 'סק"ט' in dh:
            return 9
        if 'וכן המנהג' in dh:
            return 7
        if 'י"ו' in dh:
            return 16
        if "סימן ד')" in dh:
            return 4
    print('returning gematria of first letter', n, dh, ot)
    return gematria(dh[0])

def secondarylink(link):
    for item in Ref(link).linkset():
        if item.generated_by == 'Shulchan Arukh Parser':
            for ref in item.refs:
                if ref[:4] == 'Shul':
                    return ref
        elif 'Turei' in link and item.generated_by == 'taz cm':
            return item.refs[0]
    print('no secondary link', link)
    return ''

def getlink(siman, par, line, plink, n):
    link = ''
    if n == 5:
        if siman == 0:
            link = 'Netivot HaMishpat, Beurim on Shulchan Arukh, Choshen Mishpat, Beurim on Klalei Tefisa 1'
        elif siman == 1:
            link = 'Siftei Kohen on Shulchan Arukh, Choshen Mishpat, Dinei Migo {}'.format(smigo.pop(0))
        else:
            link = 'Netivot HaMishpat, Beurim on Shulchan Arukh, Choshen Mishpat, Beurim on Kitzur Dinei Migo {}'.format(nmigo.pop(0))
            if link[-1] == '4':
                link = 'Netivot HaMishpat, Beurim on Shulchan Arukh, Choshen Mishpat, Kitzur Dinei Migo 14'

    dh = getdh(line, n)
    while link == '':
        first = dh.split()[0]
        if any(word in first for word in ['מחבר', 'רמ"א', "מחב'"]):
            link = 'Shulchan Arukh, Choshen Mishpat {}:{}'.format(siman, getOt(dh[dh.index(' ') + 1:], n, True))
        elif 'ש"ך' in first:
            link = 'Siftei Kohen on Shulchan Arukh, Choshen Mishpat {}:{}:1'.format(siman, getOt(dh[dh.index(' ') + 1:], n))
        elif any(word in first for word in ['נתיבות', 'נה"מ']):
            link = 'Netivot HaMishpat, Beurim on Shulchan Arukh, Choshen Mishpat {}:{}'.format(siman, getOt(dh[dh.index(' ') + 1:], n))
        elif 'סמ"ע' in first:
            link = "Me'irat Einayim on Shulchan Arukh, Choshen Mishpat {}:{}".format(siman, getOt(dh[dh.index(' ') + 1:], n))
        elif 'ט"ז' in first:
            link = "Turei Zahav on Shulchan Arukh, Choshen Mishpat {}:{}".format(siman, taz.pop(0))
        elif 'שם)' in first or '[שם' in first:
            link = plink
            break
        elif dh == """@22(ס"ק ג') """:
            link = 'Siftei Kohen on Shulchan Arukh, Choshen Mishpat 28:3:1'
        else:
            dh = dh.split(' ', 1)[1]
            print('trying again', n, dh)

    if '$' in link:
        link = plink

    if link != '':
        if Ref(link).text('he').text == '' or Ref(link).text('he').text == []:
            print('***link to null', n, siman, dh, link)
    else:
        print('no link', n, siman, dh)

    links = [{
    "refs": ["Hagahot Imrei Barukh on Shulchan Arukh, Choshen Mishpat {}:{}".format(siman, par), link],
    "type": "Commentary",
    "auto": True,
    "generated_by": 'imrei barukh'
    }]

    if link[:4] != 'Shul' and link != '' and n != 5:
        link2 = copy.deepcopy(links[0])
        link2['refs'][1] = secondarylink(link)
        links.append(link2)

    if n == 5:
        links = [links[0]]
        if siman == 0:
            links[0]['refs'][0] = "Hagahot Imrei Barukh on Shulchan Arukh, Choshen Mishpat, Klalei Tefisa 1"
        else:
            links[0]['refs'][0] = "Hagahot Imrei Barukh on Shulchan Arukh, Choshen Mishpat, Dinei Migo {}".format(par)

    return link, links

if __name__ == '__main__':

    server = 'http://yishai.sandbox.sefaria.org'
    #server = 'http://localhost:8000'
    functions.add_term('Hagahot Imrei Barukh', "הגהות אמרי ברוך", server=server)
    path = ["Halakhah", "Shulchan Arukh", "Commentary", "Hagahot Imrei Barukh"]
    functions.add_category('Hagahot Imrei Barukh', path, server=server)

    record = SchemaNode()
    record.add_primary_titles("Hagahot Imrei Barukh on Shulchan Arukh, Choshen Mishpat", "הגהות אמרי ברוך על שלחן ערוך חושן משפט")
    node = JaggedArrayNode()
    node.key = 'default'
    node.default = True
    node.add_structure(['Siman', 'Pararaph'])
    record.append(node)
    for titles in [['Klalei Tefisa', 'כללי תפיסה'], ['Dinei Migo', 'דיני מיגו']]:
        node = JaggedArrayNode()
        node.add_primary_titles(*titles)
        node.add_structure(['Pararaph'])
        record.append(node)
    record.validate()

    text = []

    index_dict = {
        'collective_title': 'Hagahot Imrei Barukh',
        'title': "Hagahot Imrei Barukh on Shulchan Arukh, Choshen Mishpat",
        'categories': path,
        'schema': record.serialize(),
        'dependence' : 'Commentary',
        'base_text_titles': ["Shulchan Arukh, Choshen Mishpat"]
    }
    text_version = {
        'versionTitle': "Shulhan Arukh, Hoshen ha-Mishpat, Lemberg, 1898",
        'versionSource': "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002097680",
        'language': 'he',
        'text': text
    }

    functions.post_index(index_dict, server)

    first = False
    siman = 1
    par = 1
    simanim = []
    simantext = []
    links = []
    link = ''
    parts = ['Klalei Tefisa', 'Dinei Migo']

    for n in range(1,6):
        with open('IB{}.txt'.format(n), encoding = 'utf-8') as file:
            data = file.readlines()
        if n == 5: siman = 0

        for line in data:
            line = line.strip()

            if line == '':
                continue

            if n == 5:
                if '$?' in line:
                    part = parts.pop(0)
                    text_version['text'] = text
                    functions.post_text("Hagahot Imrei Barukh on Shulchan Arukh, Choshen Mishpat, " + part, text_version, server = server)
                    text = []
                    par = 1
                if '$' in line:
                    siman += 1
                else:
                    text.append('<b>' + deleteMany(line, ['@' + str(d)*2 for d in range(6)] + [' (")', '(") ']).replace('. נ"ב', '.</b> נ"ב'))
                    link, temps = getlink(siman, par, line, link, n)
                    links += temps
                    par += 1

            elif '$' in line or (n>1 and '@22' in line):
                simanim.append(simantext)
                simantext = []
                simanim += [[]] * (getsiman(line) - siman - 1)
                siman = getsiman(line)
                par = 1
                link = ''

            elif '@22' in line or (n>1 and '@11' in line):

                if n ==1:
                    content = deleteMany(line.replace('@22', '<b>').strip() + ' ', ['(")', '(*)'])
                elif n == 2:
                    simantext.append(deleteMany(line.replace('@11', '<b>').replace('@55', '</b>').replace('  ', ' '), ['@44', '(")', ('*')]))
                else:
                    if '. נ"ב' in line:
                        simantext.append(deleteMany(line.replace('@11', '<b>').replace('. נ"ב', '. </b>נ"ב'), ['@33', '(")', ('*')]))
                    elif ' נ"ב' in line:
                        simantext.append(deleteMany(line.replace('@11', '<b>').replace('נ"ב', '. </b>נ"ב'), ['@33', '(")', '(*)']))
                    elif '@33' in line or '(")' in line:
                        simantext.append(deleteMany(line.replace('@11', '<b>').replace('@33', '</b>').replace('(")', '</b>'), ['(*)']))
                    else:
                        simantext.append(deleteMany(line, ['@11', '@33', '(")', '(*)']))

                link, temps = getlink(siman, par, line, link, n)
                links += temps
                par += 1

            elif n == 1 and '@11' in line:
                simantext.append(content + line.replace('@11', '').replace('@33', '</b>'))

            else:
                print('error tags', n, line)

    simanim.append(simantext)

    text_version['text'] = simanim
    functions.post_text("Hagahot Imrei Barukh on Shulchan Arukh, Choshen Mishpat", text_version, server = server)
    functions.post_link(links, server = server)
