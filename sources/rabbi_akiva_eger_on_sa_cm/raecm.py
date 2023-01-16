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

with open('tazrefs.txt', encoding = 'utf-8') as file:
    taz = file.readlines()

def findot(dh):
    dh += ' '
    start = 4 + dh.index('אות')
    end = dh.index(' ', start)
    ot = (dh[start:end]).replace(']', '').replace('[', '')
    if ot == '':
        print('no ot', dh)
    return ot

def findinbh(siman, seif, dh):
    salinks = Ref("Shulchan Arukh, Choshen Mishpat {}:{}".format(siman, seif)).linkset()
    for item in salinks:
        ref = item.refs[1]
        if "Be'er HaGolah" in ref and item.generated_by == 'Shulchan Arukh Parser' and (findot(dh) + ')') in Ref(ref).text('he').text:
            return ref
    print('error finding beer hagola', siman, dh)
    return ''


def dhtolink(siman, dh, plink):
    if 'ש"ך' in dh:
        link = 'Siftei Kohen on Shulchan Arukh, Choshen Mishpat {}:$:1'.format(siman)
    elif 'סמ"ע' in dh:
        link = "Me'irat Einayim on Shulchan Arukh, Choshen Mishpat {}:$".format(siman)

    if 'בא"ד' in dh or 'שם' in dh:
        if link[:10] == plink[:10]:
            link = plink
        else:
            print('error, ibid to other commentary', siman, link)
            return ''
    elif 'אות' in dh:
        if 'ש"ך' in dh or 'סמ"ע' in dh:
            link = link.replace('$', str(gematria(findot(dh))))
        else:
            link = findinbh(siman, seif, dh)

    elif 'ט"ז' in dh:
        link = "Turei Zahav on Shulchan Arukh, Choshen Mishpat {}:{}".format(siman, taz.pop(0))

    else:
        print('error, no ref in commentary', siman, link)
        return ''

    return link

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

def linetolinks(siman, seif, par, line, plink):
    link = "Shulchan Arukh, Choshen Mishpat {}:{}".format(siman, seif)
    links = [{
    "refs": ["Rabbi Akiva Eiger on Shulchan Arukh, Choshen Mishpat {}:{}".format(siman, par), link],
    "type": "Commentary",
    "auto": True,
    "generated_by": 'yad avraham'
    }]

    dh = re.findall(r'\[.*?\]', line)[0]

    if any(word in dh for word in ['שו"ע', 'הגה']):
        pass

    elif any(word in dh for word in ['ש"ך', 'סמ"ע', 'באר הגולה', 'באה"ג', 'ט"ז']):
        link = dhtolink(siman, dh, plink)

    elif 'שם' in dh:
        link = plink

    else:
        print('error, no commentary', siman, line)
        return '', []

    if link[:4] != 'Shul' and link != '':
        link2 = copy.deepcopy(links[0])
        link2['refs'][1] = link
        links.append(link2)

    if 'ט"ז' in dh:
        links.pop(0)
        tazlinks = Ref(link).linkset()
        for item in tazlinks:
            if item.generated_by == 'taz cm':
                link2 = copy.deepcopy(links[0])
                link2['refs'][1] = item.refs[0]
                links.append(link2)

    return link, links

if __name__ == '__main__':

    server = 'http://draft.sandbox.sefaria.org'
    #server = 'http://localhost:8000'


    schema = JaggedArrayNode()
    schema.add_primary_titles("Rabbi Akiva Eiger on Shulchan Arukh, Choshen Mishpat", "הגהות רבי עקיבא איגר על שלחן ערוך חושן משפט")
    schema.add_structure(["Siman", "Paragraph"])
    schema.validate()

    index_dict = {
        'collective_title': 'Rabbi Akiva Eiger',
        'title': "Rabbi Akiva Eiger on Shulchan Arukh, Choshen Mishpat",
        'categories': ["Halakhah", "Shulchan Arukh", "Commentary", "Rabbi Akiva Eiger"],
        'schema': schema.serialize(),
        'dependence' : 'Commentary',
        'base_text_titles': ["Shulchan Arukh, Choshen Mishpat"]
    }
    functions.post_index(index_dict, server)

    with open('rae cmp.txt', encoding = 'utf-8') as file:
        data = file.readlines()

    first = False
    siman = 1
    par = 1
    simanim = []
    simantext = []
    links = []

    for line in data:
        line = line.strip().replace('\n', '')

        if line == '':
            continue

        elif "רבי עקיבא איגר חושן משפט סימן " in line:
            first = not first
            if first:
                continue
            simanim.append(simantext)
            simantext = []
            simanim += [[]] * (gematria(line.split()[-1]) - siman -1)
            siman = gematria(line.split()[-1])
            par = 1
            link = ''

        elif line[:5] == 'סעיף ':
            seif = gematria(line.split()[1])

        elif line[0] == '[':
            simantext.append(re.sub(r'\\.*?\\', '', line))
            link, temps = linetolinks(siman, seif, par, line, link)
            links += temps
            par += 1

        else:
            simantext[-1] += '<br>' + re.sub(r'\\.*?\\', '', line)

    simanim.append(simantext)

    text_version = {
        'versionTitle': "Shulhan Arukh, Hoshen ha-Mishpat, Lemberg, 1898",
        'versionSource': "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH002097680",
        'language': 'he',
        'text': simanim
    }

    functions.post_text("Rabbi Akiva Eiger on Shulchan Arukh, Choshen Mishpat", text_version, server = server)
    functions.post_link(links, server = server)
