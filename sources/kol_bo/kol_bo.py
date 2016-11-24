# coding=utf-8
from sefaria.utils.util import replace_using_regex as repreg
import codecs
import urllib
import urllib2
from urllib2 import URLError, HTTPError
import json
from sources.local_settings import *


def count_instances(queries, input_file):
    """
    Counts the number of times indicated strings appear in a given text file.
    :param queries: A list of strings to be counted (a single string will be converted to a list)
    :param input_file: The file to be examined
    :return: A list of tuples containing (query, count)
    """

    # if query is not a list, place in a list
    if type(queries) != list:
        queries = [queries]

    # initialize counts to 0
    counts = [0] * len(queries)

    # loop through file
    for line in input_file:

        # loop through queries
        for index, query in enumerate(queries):
            counts[index] += line.count(query)

    # reset file
    input_file.seek(0)

    return zip(queries, counts)


def tag_chapters():
    """
    This function will create a new copy of the kol bo, this time with the chapters
    clearly marked.
    """

    # open kol_bo
    kol_bo = codecs.open('kol_bo.txt', 'r', encoding='utf-8')
    kol_bo_chapters = codecs.open('kol_bo_chapters.txt', 'w', encoding='utf-8')
    for line in kol_bo:
        # parse out tags. As the repreg function only replaces when a regex is found,
        # only one of the following two lines will actually edit the text.
        line = repreg('@01@02.*[.]', line, u'@01@02', u'<chapter>')
        line = repreg('@02.*[.]', line, u'@02', u'<chapter>')
        kol_bo_chapters.write(line)

    kol_bo.close()
    kol_bo_chapters.close()


def add_bold_tags():
    """
    replaces @03 with <b>, @04 with </b>. Lines marked by @02 get @02 replaced by <b> and </b>
    is appended to the end. Removes @01.
    """

    # open files
    original = codecs.open('kol_bo_chapters.txt', 'r', 'utf-8')
    new = codecs.open('kol_bo_bold.txt', 'w', 'utf-8')

    # loop through file
    for line in original:

        # check if line starts with @02
        if line.find(u'@02') == 0:
            line = line.replace(u'@02', u'<b>')
            line = line.replace(u'\n', u'</b>\n')

        # replace @03 with <b> and @04 with </b>
        line = line.replace(u'@03', u'<b>')
        line = line.replace(u'@04', u'</b>')

        # remove @01 tags
        line = line.replace(u'@01', u'')

        # write line to file
        new.write(line)

    original.close()
    new.close()


def post_index(index):
    """
    Posts an index to the api. Copied straight from the github wiki with minor changes,
    :param index: index to be posted
    :return:
    """
    url = 'http://www.sefaria.org/api/index/' + index["title"].replace(" ", "_")
    indexJSON = json.dumps(index)
    values = {
        'json': indexJSON,
        'apikey': API_KEY
    }
    data = urllib.urlencode(values)
    req = urllib2.Request(url, data)
    print 'posting'
    try:
        response = urllib2.urlopen(req)
        print response.read()
    except HTTPError, e:
        print 'Error code: ', e.code


def post_kolbo_index():
    """
    Posts the index for the kol bo.
    """
    index = {
        "title": "Kol Bo",
        "titleVariants": ["KolBo", u'כל בו'],
        "sectionNames": ["Siman", "Paragraph"],
        "categories": ["Halakhah"],
        "pubDate": "1490",
        "compDate": "1490",
        "pubPlace": "Middle-Age Italy",
        "compPlace": "Narbonne",
        "enDesc": "Kol Bo (all is in it) is a collection of Jewish ritual and civil laws, probably by Aaron ben Jacob ha-Kohen. It is mostly likely an abridgement of a longer work called Orḥot Ḥayyim, though this claim is disputed with some opinions saying the Kol Bo was a shorter earlier attempt to write a Halakhic work. Others claim the two works were authored by independent writers from Provence with both Gedaliah ibn Yaḥya Shemariah b. Simḥah or Joseph ben Tobiah of Provence suggested as authors. The Kol Bo does not pretend to any order; the laws that were later arranged in Oraḥ Ḥayyim are found together with those that were later arranged in Yoreh De'ah and Eben ha-'Ezer. Likewise, many laws are entirely missing in the Kol Bo. It is peculiar also in that some of the laws are briefly stated, while others are stated at great length, without division into paragraphs. After the regular code, terminating with the laws of mourning (No. 115), there comes a miscellaneous collection, containing the \"taḳḳanot\" of R. Gershom and of Jacob Tam, the Ma'aseh Torah of Judah ha-Nasi I, the legend of Solomon's throne, the legend of Joshua b. Levi, a cabalistic dissertation on circumcision, a dissertation on gemaṭria and noṭariḳon, sixty-one decisions of Eliezer b. Nathan; forty-four decisions of Samson Zadok, decisions of Isaac of Corbeil, and responsa of Perez ha-Kohen, decisions of Isaac Orbil, of the geonim Naṭronai, Hai Gaon, Amram Gaon, Nahshon Gaon, laws of the \"miḳweh\" taken from Perez's Sefer ha-Miẓwot, responsa, and finally the law of excommunication of Naḥmanides. For this reason it is quoted under the title of \"Sefer ha-Liḳḳuṭim\" in Avḳat Rokel, No. 13.",
        "era": "RI",
        "authors": [
            "Aharon ben Jacob Ha-Kohen of Lunil"
        ],
    }
    post_index(index)


def post_text(ref, text):
    """
    Posts a text that has been indexed. Copied from wiki, amended as post_index
    :param ref: Name of ref.
    :param text: Text to be posted.
    """
    textJSON = json.dumps(text)
    ref = ref.replace(" ", "_")
    url = 'http://www.sefaria.org/api/texts/%s' % ref
    values = {'json': textJSON, 'apikey': API_KEY}
    data = urllib.urlencode(values)
    req = urllib2.Request(url, data)
    try:
        response = urllib2.urlopen(req)
        print response.read()
    except HTTPError, e:
        print 'Error code: ', e.code
        print e.read()


def parse_kol_bo(upload=True):
    """
    Parses the kol bo and uploads it. MUST  be run after index has been uploaded.
    :param upload: if True will upload to site. Otherwise it will just save the parsed text
    to a file.
    """
    kolbo = codecs.open('kol_bo_bold.txt', 'r', 'utf-8')

    # set storage arrays for strings. Add first line in file to current.
    text = []
    line = kolbo.readline()
    current = [line.replace(u'<chapter>', u'')]
    # loop through file
    for line in kolbo:

        # if beginning of new chapter, add previous chapter to text and clear current
        if line.find(u'<chapter>') == 0:
            text.append(current)
            line = line.replace(u'<chapter>', u'<b>')
            line = line.replace(u'\n', u'</b>\n')
            current = [line]

        else:
            # add line to current
            current.append(line)

    # add final chapter to text    )
    text.append(current)
    kolbo.close()

    # upload text
    if upload:
        kolbo = {
            "versionTitle": "Kol Bo 1547 Venice Unknown Publisher",
            "versionSource": "http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001227196",
            "language": "he",
            "text": text,

        }
        post_text('Kol Bo', kolbo)

    else:
        # save parsed text to file
        output = codecs.open('output.txt', 'w', 'utf-8')
        for chapter in text:
            for line in chapter:
                output.write(line)
        output.close()


post_kolbo_index()
parse_kol_bo()
