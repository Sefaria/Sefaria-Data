import django
django.setup()
from sources import functions
from sefaria.model.schema import *
from sefaria.model import *
import re

#server = 'http://yishai.sandbox.sefaria.org'
#server = 'http://localhost:8000'
server = 'https://glazner.cauldron.sefaria.org'

book = ["Tzafnat Pa'neach", 'צפנת פענח']
functions.add_term(*book, server=server)
path = ["Halakhah", "Mishneh Torah", "Commentary", book[0]]
functions.add_category(book[0], path, server=server)
mishne = library.get_indexes_in_category('Mishneh Torah')
for n, item in enumerate(mishne):
    mishne[n] = [item, library.get_index(item).get_title('he')]
secnames = ['Paragraph', 'Mitzvah']
texts = {}
introlen = [7, 27]
introindexes = [1, 2, 2, 4, 6, 7, 7, 20, 20, 27, 27, 27]
links = []

def createindex(line, intro=False):
    for item in mishne:
        if line in item[1]:
            path = ["Halakhah", "Mishneh Torah", "Commentary", book[0], library.get_index(item[0]).categories[-1]]
            functions.add_category(library.get_index(item[0]).categories[-1], path, server=server)
            node = JaggedArrayNode()
            node.add_primary_titles(*[book[n] + [' on ', ' על '][n] + item[n] for n in range(2)])
            if intro:
                node.add_structure([secnames.pop(0), 'Comment'])
            else:
                node.add_structure(['Chapter', 'Halakhah', 'Comment'])
            node.validate()
            index_dict = {
                'collective_title': book[0],
                'title': book[0] + ' on ' + item[0],
                'categories': path,
                'schema': node.serialize(),
                'dependence' : 'Commentary',
                'base_text_titles': [item[0]],
                "base_text_mapping": "many_to_one"
            }
            functions.post_index(index_dict, server = server)
            if item[0] not in texts: texts[item[0]] = []
            return item[0]
    print('not find book', line)

def getChapter(line):
    if 'פרק' in line:
        chapter = functions.getGematria(line[4:])
    elif 'פ' in line:
        chapter = functions.getGematria(line.split('פ')[1])
    else:
        chapter = functions.getGematria(line)
    if chapter > 30: print('chapter too big', line, chapter)
    return chapter

def getHalakha(line, hilchot, chapter, halakha):
    if line.count(' ')>1: print(line)
    if 'הלכה' in line:
        halakha = functions.getGematria(line[5:])
    elif any('ה' in word and '"' in word for word in line.split()):
        halakha = functions.getGematria(line.split('"')[1])
    elif 'שם' in line:
        pass
    elif len(line) < 3:
        halakha = functions.getGematria(line)
    else:
        print('error no ref', hilchot, chapter, line)
    if chapter == 0 or halakha == 0:
        print('error {} {}:{}'.format(hilchot, chapter, halakha), line)
    else:
        ref = Ref('{} {}:{}'.format(hilchot, chapter, halakha))
        if ref =='' or ref == []:
            print('error no halakha {} {}:{}'.format(hilchot, chapter, halakha), line)
    return halakha

def boldtags(line):
    if line.count('@') == 1:
        if line[0] == '@': return line[3:]
    return ('<b>' + re.sub('[0-9][0-9]@', '', re.sub('[0-9][0-9]@', '>b/<', line[::-1], 1))[::-1]).replace('<b> </b>', ' ')

def bolding(line):
    if '<b>' in line[:6] or '<sm' in line[:6]: return line
    if line[:6] == '[השמטה':
        if daf:
            return "[<small>" + re.sub('@[0-9][0-9]', '', line.split('.', 1)[0][1:]) + '.</small>' + boldtags(line.split('.', 1)[1]) + ' <small>ע"כ השמטה</small>]'
        else:
            return "[<small>השמטה</small>" + boldtags(line[6:]) + ' <small>ע"כ השמטה</small>]'
    return boldtags(line)

with open('tsafnat.txt', encoding='utf-8') as file:
    data = file.readlines()

addenda = False
daf = False
for line in data:
    line = line.replace('\n', '').strip()
    if line == '' or line == '*' or '%' in line:
        continue
    if '$' in line:
        addenda = not addenda
        if '*' in line:
            daf = True

    elif '@33' in line:
        intro = False
        hilchot = createindex(line[3:])
        chapter = 0
        halakha = 0
    elif '@11' in line:
        intro = True
        hilchot = createindex(line[3:], intro=intro)
        chapter = 0
        halakha = 0
        for i in range(introlen.pop(0)):
            texts[hilchot].append([])

    elif '@55' in line:
        chapter = getChapter(line[3:])
        halakha = 0
        while len(texts[hilchot]) < chapter: texts[hilchot].append([])

    elif '@77' in line and not intro:
        halakha = getHalakha(line[3:], hilchot, chapter, halakha)
        while len(texts[hilchot][chapter-1]) < halakha: texts[hilchot][chapter-1].append([])

    else:
        if len(line) > 50000: print(line[:50])
        line = bolding('[השמטה ' + line) if addenda else bolding(line)
        if intro:
            i =  introindexes.pop(0)-1
            texts[hilchot][i].append(line)
            ref1 = '{} {}'.format(hilchot, i)
            ref2 = '{}:{}'.format(ref1, len(texts[hilchot][i]))
            links.append({
            "refs": [ref1, ref2],
            "type": "Commentary",
            "auto": True,
            "generated_by": book
            })
        else: texts[hilchot][chapter-1][halakha-1].append(line)

for index in texts:
    text_version = {
        'versionTitle': book[0]+' on Mishneh Torah, Warsaw-Piotrków, 1903-1908',
        'versionSource': "https://fjms.genizah.org",
        'language': 'he',
        'text': texts[index]
    }
    functions.post_text(book[0]+' on '+index, text_version, server=server)

functions.post_link(links, server = server)
