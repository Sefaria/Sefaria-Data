# encoding=utf-8

import re
import bleach
import codecs
import base64
import urllib2
from bs4 import BeautifulSoup
from data_utilities.util import getGematria
from sefaria.model.schema import JaggedArrayNode
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
            split = filter(lambda x: x if len(x) > 1 else None, my_line.split(u'.'))
            whole_text.extend([i if re.search(ur':$', i) else u'{}.'.format(i) for i in split])
        else:
            continue
    else:
        root.set_element([gate, chapter], whole_text)
    return root.array()


def post():

    node = JaggedArrayNode()
    node.add_title('Pardes Rimonim', 'en', primary=True)
    node.add_title(u'פרדס רימונים', 'he', primary=True)
    node.key = 'Pardes Rimonim'
    node.depth = 3
    node.addressTypes = ['Integer', 'Integer', 'Integer']
    node.sectionNames = ['Gate', 'Chapter', 'Paragraph']
    node.validate()

    index = {
        'title': 'Pardes Rimonim',
        'categories': ['Kabbalah'],
        'schema': node.serialize(),
    }
    version = {
        'versionTitle': 'Pardes Rimonim',
        'versionSource': 'http://www.hebrew.grimoar.cz/kordovero/pardes_rimonim.htm',
        'language': 'he',
        'text': parse()
    }
    post_index(index)
    post_text('Pardes Rimonim', version, index_count='on', skip_links=1)

post()
