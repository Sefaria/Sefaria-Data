# -*- coding: utf-8 -*-
"""
מקרא:
@00 פרשה
@11 קטע אות גדול
@22 פרק ופסוק
@33 קטע אות קטן
@44 השאלה הפותחת
@88 מקור (שו"ת)
$+מספר קישור להערה
#+מספר קישור להערה חוזרת
C במקום מילים בלועזית

TODO:
1) MISSING GREEK, MISSING IMAGE

; at 7:4
"""
import os
import sys
import re
import json
import codecs
import collections
p = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, p)
os.environ['DJANGO_SETTINGS_MODULE'] = "sefaria.settings"
from data_utilities import util
from sources.local_settings import *
from sources import functions
sys.path.insert(0, SEFARIA_PROJECT_PATH)
from sefaria.model import *
from sefaria.datatype.jagged_array import JaggedArray


def footnotify(line):
    """
    :param line: Line of text from main_text
    :return: Annotated string of text
    """

    m = re.findall(u"\$(\d{1,3}\*{0,2})", line)
    for number in m:
        footnotes_parasha[number] = footnotes.next()
        line = re.sub(u''.join([u"\$(", number.replace(u"*", u"\*"), u")"]), u''.join([u"<sup>", number, u"</sup><i class='footnote'>", footnotes_parasha[number] ,u"</i>"]), line, 1)
    return line


def repeat_footnotify(philo):
    """
    :param philo: List of strings with untouched footnotes
    :return: Same list with labeled # footnotes
    """
    for line in philo:
        m = re.findall(u"#\d{1,3}\*{0,2}", line)
        i = philo.index(line)
        for number in m:
            philo[i] = re.sub(number, u''.join([u"<sup>", number[1:], u"</sup><i class='footnote'>", footnotes_parasha[number[1:]], u"</i>"]), line)
    return philo


def cleanup(line):
    """
    :param line: String with @##'s,  T's, and \n's
    :return: String w/o @##'s,  T's, and \n's
    """
    #;? [\u05d0-\u05ea]{0,2}\.
    while line.startswith('@22'):
        line = re.sub(u"^(@22).*(@44)", u"", line)
    line = re.sub(u'T', u'', line)
    line = line.rstrip()
    line = re.sub(u'@\d\d', u'', line)
    return line


def jaggedarray_from_files(input_file, footnote_file):
    """
    :param input_file: Main text file to parse
    :param footnote_file: Footnote text file to parase
    :return: A 3D jaggedArray of text from files.
    """

    ja = JaggedArray([[]])
    global footnotes
    global footnotes_parasha
    global link_refs
    link_refs = []
    current = []
    list_of_currents = []
    footnotes = []
    footnotes_parasha = {}
    links = []

    text = codecs.open(footnote_file, 'r', 'utf-8')
    for line in text:
        footnotes.append(cleanup(line))
    text.close()
    footnotes = iter(footnotes)
    main_text = codecs.open(input_file, 'r', 'utf-8')

    for line in main_text:
        if line.startswith('@22'):
            while current:
                list_of_currents.append(current)
                current = []
            m = re.search(u'([\u05d0-\u05ea]{1,2}-?[\u05d0-\u05ea]{0,2}), ([\u05d0-\u05ea]{1,2}-?[\u05d0-\u05ea]{0,2})', line)
            # if with semicolon, choose first pasuk ignore second
            location = Ref(u"".join([u"בראשית ", m.group(1), u": ", m.group(2)]))
            link_refs.append(location)
            current.append(footnotify(u''.join([u"<strong>", cleanup(line), u"</strong>"])))
        elif line.startswith('@88'):
            current[-1] += u''.join([u"<sup>*</sup><i class='footnote'>", cleanup(line), u"</i>", "<br>___________<br>"])
        elif line.startswith('@11') or line.startswith('@33'):
            current.append(cleanup(footnotify(line)))
        elif line.startswith('@00'): #move line is None to own condition
            while current:
                list_of_currents.append(current)
                current = []
            while list_of_currents:
                for x in list_of_currents:
                    i = list_of_currents.index(x)
                    location = [link_refs[i].sections[0] - 1, link_refs[i].sections[1] - 1]
                    # if they start on same verse, append array to previous array
                    if link_refs[i].sections[0] == link_refs[i - 1].sections[0] and link_refs[i].sections[1] == link_refs[i - 1].sections[1]:
                        bereshit_ref = link_refs[i].normal()
                        philo_ref = "".join(["The Midrash of Philo ", str(location[0] + 1), ":", str(location[1] + 1), ":", str(len(ja.get_element([location[0], location[1]]))+1), "-", str(len(ja.get_element([location[0], location[1]]))+len(x))])
                        #above line: base first on last number of element len(ja.get_element([location[0], locationo[1]]))
                        links.append((bereshit_ref, philo_ref))
                        ja.get_element([location[0], location[1]]).extend(repeat_footnotify(x))
                    else:
                        bereshit_ref = link_refs[i].normal()
                        philo_ref = "".join(["The Midrash of Philo ", str(location[0] + 1), ":", str(location[1] + 1), ":1-", str(len(x))])
                        links.append((bereshit_ref, philo_ref))
                        ja.set_element([location[0], location[1]], repeat_footnotify(x), pad = [])
                footnotes_parasha.clear()
                current = []
                link_refs = []
                list_of_currents = []


    main_text.close()

    #util.ja_to_xml(ja.array(), ['Chapter', 'Verse','Comment'])
    return ja.array(), links


def create_index():
    # create index
    schema = JaggedArrayNode()
    schema.add_primary_titles("The Midrash of Philo", u"מדרש פילון")
    schema.add_structure(["Chapter", "Verse", "Comment"])
    schema.validate()

    index_dict = {
        'title': "The Midrash of Philo",
        'categories': ['Other'],
        'schema': schema.serialize() # This line converts the schema into json
    }
    functions.post_index(index_dict)

def post_text(text):
    text = {
        "title": "The Midrash of Philo",
        "versionTitle": "The Midrash of Philo, by Samuel Belkin, 1989",
        "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001117662",
        "language": "he",
        "text": text,
    }
    functions.post_text("The Midrash of Philo", text, index_count="on")


def post_links(links):
    functions.post_link(links)

final_product, ref_links = jaggedarray_from_files('/Users/joelbemis/Documents/programming/Sefaria-Data/sources/Midrash_Philo/philo_midrash.txt',
                            '/Users/joelbemis/Documents/programming/Sefaria-Data/sources/Midrash_Philo/philo_footers.txt')
ref_links = [{
    'refs': refs,
    'auto': True,
    'generated_by': "Yoel's Philo parser",
    'type': 'commentary'
} for refs in ref_links]
#create_index()
post_text(final_product)
#post_links(ref_links)
