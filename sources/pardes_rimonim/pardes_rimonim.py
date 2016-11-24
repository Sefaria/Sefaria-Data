# encoding=utf-8

import re
import bleach
import codecs
import base64
import urllib2
from bs4 import BeautifulSoup
from data_utilities.util import getGematria
from sefaria.model.schema import JaggedArrayNode, SchemaNode
from sources.functions import post_text, post_index
from sefaria.datatype.jagged_array import JaggedArray


def get_url(snippet=None):

    if snippet is None:
        snippet = 'pardes_rimonim.htm'
    return 'http://www.hebrew.grimoar.cz/kordovero/{}'.format(snippet)


def get_file():
    response = urllib2.urlopen(get_url())
    raw_data = response.read()
    return codecs.decode(raw_data, 'windows-1255')


def get_regex():
    terms = [
        ur'\u05e2\u05db\u0022\u05dc\. ', ur'\. (\u05d5)?\u05d4\u05e0\u05d4', ur'\. \u05d5\u05e2\u05d5\u05d3',
        ur'\. \u05d5\u05e2\u05e0\u05d9\u05df'
    ]
    return re.compile(ur'|'.join(terms))


def split_paragraph(paragraph):
    pattern = get_regex()
    split = []
    start = 0
    for match in pattern.finditer(paragraph):
        end = match.start() + match.group().index(u' ')
        split.append(paragraph[start:end])
        start = end + 1
    else:
        split.append(paragraph[start:])
    return split


def add_image(image_html, string_to_append):
    soup = BeautifulSoup(image_html, 'html.parser')
    image_file = soup.img['src']
    with open(image_file) as infile:
        encoded_image = base64.b64encode(infile.read())
    image = u'<br><img src="data:image/png;base64,{}" >'.format(encoded_image)
    return u'{} {}'.format(string_to_append, image)


def parse():
    with codecs.open('pardes_rimonim.html', 'r', 'windows-1255') as infile:
        lines = infile.readlines()
    gate, chapter, whole_text = -1, -1, []
    root = JaggedArray([[]])
    found_beginning = False
    beginning = re.compile(ur'^<b>\u05e9\u05e2\u05e8 ([\u05d0-\u05ea]{1,2}) \u05e4\u05e8\u05e7 ([\u05d0-\u05ea]{1,2})')

    for line in lines:
        match = beginning.search(line)
        if match:
            if found_beginning:
                if re.search(ur'^\u05e4\u05e8\u05e7', whole_text[0]):  # strip out some unnecessary text
                    root.set_element([gate, chapter], whole_text[1:], pad=[])
                else:
                    root.set_element([gate, chapter], whole_text, pad=[])
                whole_text = []
            else:
                found_beginning = True
            new_gate, new_chapter = getGematria(match.group(1))-1, getGematria(match.group(2))-1
            if new_gate - gate > 1 or new_chapter - chapter > 1:
                print 'skip found at Gate {} Chapter {}'.format(new_gate+1, new_chapter+1)
            gate, chapter = new_gate, new_chapter

        elif found_beginning:
            if re.search(ur'<img', line):
                whole_text[-1] = add_image(line, whole_text[-1])
                continue
            my_line = bleach.clean(line, tags=[], strip=True)
            if my_line.isspace():
                continue
            my_line = re.sub(u'(\n|\r)', u'', my_line)
            split = filter(lambda x: x if len(x) > 1 else None, split_paragraph(my_line))
            whole_text.extend(split)
        else:
            continue
    else:
        root.set_element([gate, chapter], whole_text)
    return root.array()


def post():

    root = SchemaNode()
    root.add_title('Pardes Rimonim', 'en', primary=True)
    root.add_title(u'פרדס רימונים', 'he', primary=True)
    root.key = 'Pardes Rimonim'

    anode = JaggedArrayNode()
    anode.add_title("Author's Introduction", 'en', primary=True)
    anode.add_title(u'הקדמת המחבר', 'he', primary=True)
    anode.key = "Author's Introduction"
    anode.depth = 1
    anode.addressTypes = ['Integer']
    anode.sectionNames = ['Paragraph']
    root.append(anode)

    inode = JaggedArrayNode()
    inode.add_title("Index", 'en', primary=True)
    inode.add_title(u'סימני הספר', 'he', primary=True)
    inode.key = "Index"
    inode.depth = 2
    inode.addressTypes = ['Integer', 'Integer']
    inode.sectionNames = ['Gate', 'Chapter']
    root.append(inode)

    pnode = JaggedArrayNode()
    pnode.add_title("A Prayer", 'en', primary=True)
    pnode.add_title(u'בקשה', 'he', primary=True)
    pnode.key = "A Prayer"
    pnode.depth = 1
    pnode.addressTypes = ['Integer']
    pnode.sectionNames = ['Paragraph']
    root.append(pnode)

    dnode = JaggedArrayNode()
    dnode.default = True
    dnode.key = 'default'
    dnode.depth = 3
    dnode.addressTypes = ['Integer', 'Integer', 'Integer']
    dnode.sectionNames = ['Gate', 'Chapter', 'Paragraph']
    root.append(dnode)
    root.validate()

    index = {
        "pubDate": "1651",
        "title": "Pardes Rimonim",
        "pubPlace": "Amsterdam",
        "enDesc": "Pardes Rimonim (Orchard of Pomegranates) is a primary text of Kabbalah composed by the Jewish mystic Moses ben Jacob Cordovero in Safed. It is composed of thirteen gates or sections each subdivided into chapters. He indicates in his introduction that the work is based upon notes he took during his study of the Zohar, the foundational work of the Kabbalahand was designed \"in order not to become lost and confused in its [the Zohar] depths\". The work is an encyclopaedic summary of the Kabbalah, including an effort to \"elucidate all the tenets of the Cabala, such as the doctrines of the sefirot, emanation, the divine names, the import and significance of the alphabet, etc.\" Pardes Rimonim was the first comprehensive exposition of Medieval Kabbalah, though its rationally influenced scheme was superseded by the subsequent 16th century Safed mythological scheme of Isaac Luria.",
        "era": "RI",
        "authors": ["Moshe Cordovero"],
        "categories": ["Kabbalah"],
        'schema': root.serialize()
    }
    version = {
        'versionTitle': 'Pardes Rimonim',
        'versionSource': 'http://www.hebrew.grimoar.cz/kordovero/pardes_rimonim.htm',
        'language': 'he',
        'text': parse()
    }
    post_index(index)
    post_text('Pardes Rimonim', version, index_count='on', skip_links=1)
