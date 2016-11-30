# encoding=utf-8

import codecs
import re
from data_utilities.util import ja_to_xml,  traverse_ja
from sources.functions import post_text, post_index
from sefaria.model import *
from sefaria.system.exceptions import DuplicateRecordError

# init section lists - do we want this in the method or not?
parsed = []
perek = []
mishna = []
dibur = []

def text_parse():
    # open, read, close the original txt file
    with codecs.open('yitzira_gra.txt', 'r', 'utf-8') as fp:
        lines = fp.readlines()
    starting = None
    # check if we got to the end of the legend and change to started
    for line_num, line in enumerate(lines):
        if line == u'\n':
            starting = line_num + 1
            break
    # init section lists
    # parsed = []
    # perek = []
    # mishna = []
    # dibur = []
    # loop on lines and creat the jagged array
    for line in lines[starting:]:
        if line.find(u'@00') == 0: #is not -1:
            # perek
            if perek:
                dibur = ' '.join(dibur)
                mishna.append(dibur)
                dibur = []
                perek.append(mishna)
                mishna = []
                parsed.append(perek)
                perek = []

        elif line.find(u'@22') == 0:# is not -1:
            # mishna
            if mishna:
                dibur = ' '.join(dibur)
                mishna.append(dibur)
                dibur = []
                perek.append(mishna)
                mishna = []
        else: # this line is going to be part of the dibur
            # Dibur Hamatchil
            if line.find(u'@31') is not -1 and dibur:
                dibur = ' '.join(dibur)
                mishna.append(dibur)
                dibur = []
            # note: can make this peace of code slimmer, kept it like this in case we want to change the html <> tags of orginal legend @ tag to somthing else
            # segment ocr tag fixing
            line = re.sub(u'@(31)', u'<b>', line)
            line = re.sub(u'@(32)', u'</b>', line)
            # title 'Ofen' in the gra's commentary
            line = re.sub(u'@(03)', u'<br>', line)
            line = re.sub(u'@(04)', u'</br>', line)
            # in text was modgash
            line = re.sub(u'@(44)', u'<b>', line)
            line = re.sub(u'@(45)', u'</b>', line)
            # end of pirush gr"a
            line = re.sub(u'@(98)', u'<small>', line)
            line = re.sub(u'@(99)', u'</small>', line)
            # not necessary ocr tag
            line = re.sub(u'@(11)', u'', line)
            # append this line to the given dibur
            dibur.append(line.strip())

    # once reached the end close all what was opened
    dibur = ' '.join(dibur)
    mishna.append(dibur)
    perek.append(mishna)
    parsed.append(perek)
    ja_to_xml(parsed,['perek','mishna','dibur'],filename = 'gra.xml')
    return parsed


#
# def end(section, line):
#     dibur.append(line)
#     dibur = ' '.join(dibur)
#     mishna.append(dibur)
#     dibur = []
#     if section == 'mishna':
#         perek.append(mishna)
#         mishna = []


# get the parssed text (it is a jagged array depth 3, ['perek','mishna','dibur']
gra = text_parse()
# specefid post function
def post_this():
    text_version = {
        'versionTitle': 'Sefer Yetzirah, Warsaw 1884',
        'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001310968',
        'language': 'he',
        'text': gra
    }

    schema = JaggedArrayNode()
    schema.add_title('GRA on Sefer Yetzirah Ari Version', 'en', True)
    schema.add_title(u'פירוש הגרא על ספר יצירה', 'he', True)
    schema.key = 'GRA on Sefer Yetzirah Ari Version'
    schema.depth = 3
    schema.addressTypes = ['Integer', 'Integer','Integer']
    schema.sectionNames = ['Chapter', 'Mishnah','Comment']
    schema.validate()

    index_dict = {
        'title': 'GRA on Sefer Yetzirah Ari Version',
        'categories': ['Commentray2','Kabbalah','Gra'],
        'schema': schema.serialize() # This line converts the schema into json
    }
    post_index(index_dict)

    post_text('GRA on Sefer Yetzirah Ari Version', text_version, index_count='on')

# post with the post function
post_this()

# create the link objects btween the dibur HaMatchil of the GRA and the main text
gra_links = []
# use a generator to go over the text and find the 3 level indices
for dh in traverse_ja(gra):
        link = (
            {
            "refs": [
                "GRA on Sefer Yetzirah Ari Version " + '%d:%d:%d' %tuple(x+1 for x in dh['indices']),
                "Sefer Yetzirah Ari Version " + '%d:%d' %tuple(x+1 for x in dh['indices'][:2]),
            ],
            "type": "commentary",
            "auto": True,
            "generated_by": "gra_parse"
        })
        gra_links.append(link)

# save to mongo the list of dictionaries.
for link in gra_links:
    try:
        Link(link).save()
    except DuplicateRecordError:
        print 'error: DuplicateRecordError flew'


