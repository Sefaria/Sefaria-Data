# encoding=utf-8

import codecs
import re
from data_utilities.util import ja_to_xml,  traverse_ja, multiple_replace
from sources.functions import post_text, post_index, post_link
from sefaria.model import *
from sefaria.system.exceptions import DuplicateRecordError

# init section lists - do we want this in the method or not?

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
    # init section lists and flags
    parsed = []
    perek = []
    mishna = []
    dibur = []
    first_p = True  # first perek flag
    first_m = True  # first mishna flag
    first_d = True  # first dibur flag
    ofen = False # 'ofen' flag

    # dictionary for line ocr tag fixing
    replace_dict = {u'@03': u'<b>', u'@04': u'</b><br>',  # title 'Ofen' in the gra's commentary
                    u'@11': u'',  # not necessary ocr tag
                    u'@31': u'<b>', u'@32': u'</b>',  # bold dibur hamatchil
                    u'@44': u'<b>', u'@45': u'</b>',  # was bold in text
                    u'@98': u'<small>', u'@99': u'</small>',  # the slik at the end
                    ur'\*\[(.*?)\]': ur'<small>[\1]</small>'  # footnotes
                    }
    # loop on lines and creat the jagged array
    for line in lines[starting:]:
        if line.find(u'@00') is not -1:
            # perek
            if first_p:
                first_p = False
            else:
                dibur = ' '.join(dibur)
                mishna.append(dibur)
                dibur = []
                perek.append(mishna)
                mishna = []
                parsed.append(perek)
                perek = []
                first_m = True  # since this is opening a new perek

        elif line.find(u'@22') == 0:  # notice that this parsing is given that there is no text on same line with @22 and @00
            # mishna
            if first_m:
                first_m = False
            else:
                dibur = ' '.join(dibur)
                mishna.append(dibur)
                dibur = []
                perek.append(mishna)
                mishna = []
                first_d = True  # since this is opening a new mishna
        else: # this line is going to be part of the dibur
            # Dibur Hamatchil
            if re.search(u'@(03|31|98)', line):  # probably start a new dibur
                 if (not ofen) and (not first_d): # prob close prev dibur
                    dibur = ' '.join(dibur)
                    mishna.append(dibur)
                    dibur = []
                 else:
                    if ofen:
                        ofen = False
                    if first_d:
                        first_d = False
            if re.search(u'@03', line):
                ofen = True
            # segment ocr tag fixing
            line = multiple_replace(line, replace_dict, using_regex = True)
            dibur.append(line)

    # once reached the end close all what was opened
    dibur = ' '.join(dibur)
    mishna.append(dibur)
    perek.append(mishna)
    parsed.append(perek)
    # ja_to_xml(parsed,['perek','mishna','dibur'],filename = 'gra.xml')
    return parsed

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
    schema.add_title('HaGra on Sefer Yetzirah Gra Version', 'en', True)
    schema.add_title(u'פירוש הגר"א על ספר יצירה', 'he', True)
    schema.key = 'HaGra on Sefer Yetzirah Gra Version'
    schema.depth = 3
    schema.addressTypes = ['Integer', 'Integer', 'Integer']
    schema.sectionNames = ['Chapter', 'Mishnah', 'Comment']
    schema.validate()

    index_dict = {
        'title': 'HaGra on Sefer Yetzirah Gra Version',
        'categories': ['Commentary2', 'Kabbalah', 'Gra'],
        'schema': schema.serialize()# This line converts the schema into json
    }
    post_index(index_dict)

    post_text('HaGra on Sefer Yetzirah Gra Version', text_version, index_count='on')

# post with the post function
post_this()

# create the link objects btween the dibur HaMatchil of the GRA and the main text
gra_links = []
# use a generator to go over the text and find the 3 level indices
for dh in traverse_ja(gra):
        link = (
            {
            "refs": [
                "HaGra on Sefer Yetzirah Gra Version " + '%d:%d:%d' %tuple(x+1 for x in dh['indices']),
                "Sefer Yetzirah Gra Version " + '%d:%d' %tuple(x+1 for x in dh['indices'][:2]),
            ],
            "type": "commentary",
            "auto": True,
            "generated_by": "gra_parse"
        })
        dh_text = dh['data']
        # append to links list
        gra_links.append(link)

# shave off the last link of "slik" shpuldn't be linked in
gra_links.pop()

# save to mongo the list of dictionaries.
post_link(gra_links)

# link_ofen = (
#             {
#             "refs": [
#                 "Pri Yitzhak on Sefer Yetzirah " + '%d:%d:%d' %tuple(x+1 for x in dh['indices']),
#                 "Sefer Yetzirah Ari Version " + '%d:%d' %tuple(x+1 for x in dh['indices'][:2]),
#             ],
#             "type": "reference"
#         })