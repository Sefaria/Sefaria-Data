# encoding=utf-8

import codecs
import re
from data_utilities.util import ja_to_xml, multiple_replace, traverse_ja
from sources.functions import post_text, post_index, post_link
from sefaria.model import *
from sefaria.datatype.jagged_array import JaggedArray


def raavad_parse():
    with codecs.open('yitzira_raavad.txt', 'r', 'utf-8') as fp:
        lines = fp.readlines()
    # init JA and there depths
    ja_sp = [] # JA starting points in the txt

    # dictionary for line ocr tag fixing
    replace_dict = {u'@(44|13|31|41)': u'<b>', u'@(45|14|32|42)': u'</b>',# bold in text
                    u'@(03|04|10|11|98|99|56)' : u'', #
                    u'@55' : ur'<img src = " " height = "100" width = "100">',  # image tag
                    ur'(\*\[.*?\])': ur'<small>\1</small>'  # notes in the text
                    }
    # check if we got to the end of the legend and change to started
    startJA = None
    for line_num, line in enumerate(lines):
        if line == u'\n':
            startJA = line_num + 1  # ignoring the book name from text
            ja_sp.append(startJA)

    ja_fifty = fifty_parse(lines[ja_sp[0]+1:ja_sp[1]],replace_dict)
    ja_32_hakdama_n = threty_two_parse(lines[ja_sp[1]:ja_sp[2]], replace_dict, 'hakdama_n')
    ja_32_netivot = threty_two_parse(lines[ja_sp[2]:ja_sp[3]], replace_dict, 'netivot')
    ja_32_hakdama_p = threty_two_parse(lines[ja_sp[3]:ja_sp[4]], replace_dict, 'hakdama_p')
    ja_32_perush = threty_two_parse(lines[ja_sp[4]:ja_sp[5]], replace_dict, 'perush')
    ja_raavad_perush = raavad_perush_parse(lines[ja_sp[5]:], replace_dict)

    #  not nice fixing of segments into break tags
    ja_32_netivot[31] = ja_32_netivot[31] + '<br><small>' + ja_32_netivot[32] + '</small>'
    ja_32_netivot = ja_32_netivot[:32]
    ja_32_perush[0] = ja_32_hakdama_p[0] + '<br>' + ja_32_hakdama_p[1] + '<br><br>' + ja_32_perush[0]

    ja_to_xml(ja_32_perush, ['netiv'], 'test.xml')
    return {'Raavad on Sefer Yetzirah': ja_raavad_perush,
                'Raavad on Sefer Yetzirah, Introduction, The Fifty Gates of Understanding': ja_fifty,
                'Raavad on Sefer Yetzirah, Introduction, The Thirty Two Paths of Wisdom, Introduction': ja_32_hakdama_n,
                'Raavad on Sefer Yetzirah, Introduction, The Thirty Two Paths of Wisdom': ja_32_netivot,
                'Raavad on Sefer Yetzirah, Introduction, The Thirty Two Paths of Wisdom, The Thirty Two Paths Explained': ja_32_perush}


def fifty_parse(lines, replace_dict):
    # start the parsing of part fifty
    arr = []
    perek = []
    peska = []
    lines = split_lines(lines)
    for line in lines:
        if line.find(ur'@05') is not -1:
            if perek:

                perek.append(peska)
                peska = []
                arr.append(perek)
                perek = []
        else:
            if (line.find(u'@13') is not -1) and (peska):
                perek.append(peska)
                peska = []
            line = multiple_replace(line, replace_dict, using_regex=True)
            peska.append(line)
    perek.append(peska)
    arr.append(perek)
    ja_to_xml(arr,['perek', 'piska', 'break'], 'raavad_50.xml')

    return arr

# split long lines into smaller ones useing key words like "VeHene".
#   note: if you use this spliting methos you want to be sure not to use the "".join()

def split_lines(lines):
    ret = []
    for line in lines:
        line = re.sub(u'\. (\u05d5?(\u05d4\u05e0\u05d4|\u05e2\u05d5\u05d3))',ur'. #\1', line)
        line_list = re.split(ur'#', line)
        ret = ret + line_list
    return ret

def threty_two_parse(lines, replace_dict, str):
    # start the parsing of 32 netivot
    arr = []
    netiv = []
    first = True
    for line in lines:
        if re.search(u'@(13|03)', line):# and (netiv):
            if first:
                first = False
            else:
                netiv = ' '.join(netiv)
                arr.append(netiv)
                netiv = []
        line = multiple_replace(line, replace_dict, using_regex=True)
        netiv.append(line.strip())
    netiv = ' '.join(netiv)
    arr.append(netiv)
    ja_to_xml(arr, ['netiv'], '{}{}'.format(str,'_32.xml'))

    return arr


def raavad_perush_parse(lines, replace_dict):
    # start the parsing of part raavad text itself
    arr = []
    first_p = True
    first_m = True
    first_d = True
    perek = []
    mishna = []
    dibur = []
    for line in lines:
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
                arr.append(perek)
                perek = []
                first_m = True  # since this is opening a new perek

        elif line.find(u'@22') is not -1:  # notice that this parsing is given that there is no text on same line with @22 and @00
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
        else:
            # this line is going to be part of the dibur
            # Dibur Hamatchil
            if re.search(u'@(31|98)', line) and (not first_d):# and not first_d:  # probably start a new dibur
                    dibur = ' '.join(dibur)
                    mishna.append(dibur)
                    dibur = []
            else:
                if first_d:
                    first_d = False
            # segment ocr tag fixing
            line = multiple_replace(line, replace_dict, using_regex=True)
            dibur.append(line)
    dibur = ' '.join(dibur)
    mishna.append(dibur)
    perek.append(mishna)
    arr.append(perek)
    ja_to_xml(arr,['perek', 'mishna', 'dibur'], 'raavad_text.xml')

    return arr


def ravaad_schema():
    # create index record for the root
    record_root = SchemaNode()
    record_root.add_title('Raavad on Sefer Yetzirah', 'en', primary=True, )
    record_root.add_title(u'פירוש הראב"ד על ספר יצירה', 'he', primary=True, )
    record_root.key = 'Raavad on Sefer Yetzirah'


    # create index record for the introduction
    record_intro = SchemaNode()
    record_intro.add_title('Introduction', 'en', primary=True, )
    record_intro.add_title(u'הקדמה', 'he', primary=True, )
    record_intro.key = 'Introduction'

    # 50 shearim node under intro SchemaNode
    node_50 = JaggedArrayNode()
    node_50.add_title('The Fifty Gates of Understanding', 'en', primary=True)
    node_50.add_title('חמשים שערי בינה', 'he', primary=True)
    node_50.key = 'The Fifty Gates of Understanding'
    node_50.depth = 3
    node_50.addressTypes = ['Integer', 'Integer', 'Integer']
    node_50.sectionNames = ['Chapter', 'Paragraph', 'Segment']
    record_intro.append(node_50)

    # index for 32 Paths of Wisdom SchemaNode
    record_32 = SchemaNode()
    record_32.add_title('The Thirty Two Paths of Wisdom', 'en', primary=True, )
    record_32.add_title(u'ל"ב נתיבות חכמה', 'he', primary=True, )
    record_32.key = 'The Thirty Two Paths of Wisdom'
    record_intro.append(record_32)

    # add node for the Introduction to The Thirty Two Paths of Wisdom
    node_hakdama = JaggedArrayNode()
    node_hakdama.add_title('Introduction', 'en', primary=True, )
    node_hakdama.add_title(u'הקדמה', 'he', primary=True, )
    node_hakdama.key = 'Introduction'
    node_hakdama.depth = 1
    node_hakdama.addressTypes = ['Integer']
    node_hakdama.sectionNames = ['Paragraph']
    record_32.append(node_hakdama)

    # add default node - the The Thirty Two Paths of Wisdom
    node_ravaad = JaggedArrayNode()
    node_ravaad.key = "default"
    node_ravaad.default = True
    node_ravaad.depth = 1
    node_ravaad.addressTypes = ['Integer']
    node_ravaad.sectionNames = ['Path']
    record_32.append(node_ravaad)

    # add node Perush to The Thirty Two Paths of Wisdom
    node_32_perush = JaggedArrayNode()
    node_32_perush.add_title('The Thirty Two Paths Explained', 'en', primary=True)
    node_32_perush.add_title('פירוש ל"ב נתיבות חכמה', 'he', primary=True)
    node_32_perush.key = 'The Thirty Two Paths Explained'
    node_32_perush.depth = 1
    node_32_perush.addressTypes = ['Integer']
    node_32_perush.sectionNames = ['Path']
    record_32.append(node_32_perush)

    record_root.append(record_intro)

    # add default node - the Ravaad perush
    node_ravaad = JaggedArrayNode()
    node_ravaad.key = "default"
    node_ravaad.default = True
    node_ravaad.depth = 3
    node_ravaad.addressTypes = ['Integer', 'Integer', 'Integer']
    node_ravaad.sectionNames = ['Chapter', 'Verse', 'Comment']
    record_root.append(node_ravaad)
    record_root.validate()

    return record_root


def post_raavad_index():
    # add index for the perush
    index_ravaad = {
        "title": "Raavad on Sefer Yetzirah",
        "categories": ["Commentary2", "Kabbalah", "Raavad"],
        "schema": ravaad_schema().serialize(),
        "author " : [u'Yosef ben Shalom Ashkenazi']
    }
    post_index(index_ravaad)


def post_raavad_text(text_dict):
    # version for all the ja
    for ja in text_dict.keys():
        version = {
            'versionTitle': 'Sefer Yetzirah, Warsaw 1884',
            'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001310968',
            'language': 'he',
            'text': text_dict[ja]
        }
        post_text(ja, version)
    # index_count = "off"


# link perush 32 to main 32
def link_32():
    # create the link objects btween the dibur HaMatchil and the main text
    links = []
    # use a generator to go over the text and find the 3 level indices
    for i in range(1,33):
        link = (
            {
                "refs": [
                    "Raavad on Sefer Yetzirah, Introduction, The Thirty Two Paths of Wisdom " + '{}'.format(i),
                    "Raavad on Sefer Yetzirah, Introduction, The Thirty Two Paths of Wisdom, The Thirty Two Paths Explained " + '{}'.format(i),
                ],
                "type": "commentary",
                "auto": True,
                "generated_by": "raavad_parse"
            })
        # append to links list
        links.append(link)
    return links


# link raavad comantary to Sefer Yetzira (stam aka short version)
def link_raavad(text_ja):
    # create the link objects btween the dibur HaMatchil and the main text
    links = []
    # use a generator to go over the text and find the 3 level indices
    for dh in traverse_ja(text_ja):
        link = (
            {
                "refs": [
                    "Raavad on Sefer Yetzirah , " + '%d:%d:%d' % tuple(x + 1 for x in dh['indices']),
                    "Sefer Yetzirah " + '%d:%d' % tuple(x + 1 for x in dh['indices'][:2]),
                ],
                "type": "commentary",
                "auto": True,
                "generated_by": "raavad_parse"
            })
        dh_text = dh['data']
        # append to links list
        links.append(link)
    # shave off the last link of "slik" shpuldn't be linked in
    links.pop()
    return links

# main
#get the dictionary with all the ja.
text_dict = raavad_parse()

post_raavad_index()

post_raavad_text(text_dict)

# save to mongo the links text <-> raavad.
post_link(link_raavad(text_dict['Raavad on Sefer Yetzirah']))

# save to mongo links 32 <-> perush 32
post_link(link_32())