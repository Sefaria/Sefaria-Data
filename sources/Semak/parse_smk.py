# encoding=utf-8

import codecs
import re
from collections import OrderedDict
import unicodecsv as csv
from data_utilities.util import getGematria, numToHeb
from data_utilities.util import ja_to_xml, multiple_replace, traverse_ja, file_to_ja_g, file_to_ja
from sefaria.datatype.jagged_array import JaggedArray
from sefaria.model import *
from sources.functions import post_text, post_index, post_link

# Take 2

def parse_smk(filename):
    '''
    :param filename: smk source txt file
    :return: JA obj smk parsed to depth 2 [siman, segment] (including a citation segment at the top of each siman)
    '''

    def cleaner(my_text):
        replace_dict = {u'@11(.*?)@12': ur'<b>\1</b>', u'@33(.*?)@34': ur'<b>\1</b>',
                        u'@66(.*?)@67': ur'\1'}  # , u'@55[\u05d0-\u05ea]{1,3}' : u'<i-tags = >'}
        new = []
        for line in my_text:
            line = multiple_replace(line, replace_dict, using_regex=True)
            new.append(line)
        return new

    regs = [ur'@22(?P<gim>[\u05d0-\u05ea]{1,3})']  # , u'@(11|23|33)(?P<gim>)']
    with codecs.open(filename, 'r', 'utf-8') as fp:
        lines = fp.readlines()
    starting = None
    # check if we got to the end of the legend and change to started
    # clean all lines of days start with @00
    cleaned = []
    letter_section = []
    alt_day = []
    for line_num, line in enumerate(lines):
        if line == u'\n':
            starting = line_num + 1
            break
    for line_num, line in enumerate(lines[starting:]):
        if re.search(u'@00', line):
            alt_day.append(line_num)
        if not re.search(u'@00', line) and not line.isspace():
            if re.search(u'@22', line):
                line = re.split(u'(@22[\u05d0-\u05ea]{1,3})', line)
                if isinstance(line, basestring):
                    cleaned.append(line)
                else:
                    [cleaned.append(st) for st in line if st]
            else:
                cleaned.append(line)
    alt_day.append(len(lines))
    print alt_day
    try:
        smk_ja = file_to_ja_g(2, cleaned, regs, cleaner, gimatria=True, grab_all=[False, True, True],
                              group_name='gim').array()
    except AttributeError:
        print 'there are more regs then levels...'

    ja_to_xml(smk_ja, ['letter', 'segments'], 'smk.xml')

    return JaggedArray(smk_ja)


def parse_raph(filename, smk_ja):
    '''

    :param filename: raph source txt file
    :param smk_ja: JA obj smk parsed [siman,segment]
    :return: JA obj parsed [siman, letter] some simanim will be empty
    '''

    def cleaner(my_text):
        replace_dict = {u'@(?:11|77)[\u05d0-\u05ea]{0,3}': u'',
                        u'@(33|22)': u''}
        new = []
        for line in my_text:
            line = multiple_replace(line, replace_dict, using_regex=True)
            new.append(line)
        return new

    regs = [ur'@11(?P<gim>[\u05d0-\u05ea]{1,3})']
    with codecs.open(filename, 'r', 'utf-8') as fp:
        lines = fp.readlines()
    starting = None
    # check if we got to the end of the legend and change to started
    # clean all lines of days start with @00
    cleaned = []
    for line_num, line in enumerate(lines):
        if line == u'\n':
            starting = line_num + 1
            break
    for line_num, line in enumerate(lines[starting:]):
        if not re.search(u'@00', line) and not line.isspace():
            line = re.split(u'(@11[\u05d0-\u05ea]{0,3})', line)
            if isinstance(line, basestring):
                cleaned.append(line)
            else:
                [cleaned.append(st.strip()) for st in line if st]
    try:
        ja = file_to_ja(2, cleaned, regs, cleaner, grab_all=False).array()
    except AttributeError:
        print 'there are more regs then levels...'

    ja_to_xml(ja, ['letter', 'segments'], 'raph_letters.xml')

    d1 = 0
    aligned = []
    siman = []
    segment = []
    for letter in smk_ja.array():
        for seg in letter:
            for ff in re.finditer(u'@55[\u05d0-\u05ea]{0,3}', seg):
                # segment.append(ja[d1])
                siman.append(ja[d1])
                d1 += 1
            if segment != []:
                siman.extend(segment) #rather then append
                # segment = []
        aligned.append(siman)
        siman = []
    ja_to_xml(aligned, ['siman', 'letter', 'segment'], 'raph_simanim_24.xml')
    return JaggedArray(aligned)


def parse_hagahot(filename, smk_ja, raph_ja):
    '''

    :param filename: hagahot source txt file
    :param smk_ja: smk JA obj [siman, segment]
    :param raph_ja: raph JA obj [siman, letter]
    :return: JA obj
    '''

    ja_hagahot = []
    def cleaner(my_text):
        #todo: deal with @44 and @00 (@00 maybe should be only in smk base text? - ask Shmuel)
        replace_dict = {u'@11\([\u05d0-\u05ea]{0,3}\)': u'', u'@(33|77|88|99)': u'', u'@55(.*?)@66': u'<b>\1</b>'}
        new = []
        for line in my_text:
            line = multiple_replace(line, replace_dict, using_regex=True)
            new.append(line)
        return new

    regs = [ur'@11\((?P<gim>[\u05d0-\u05ea]{1,3})\)']
    with codecs.open(filename, 'r', 'utf-8') as fp:
        lines = fp.readlines()
    starting = None
    # check if we got to the end of the legend and change to started
    # clean all lines of days start with @00
    cleaned = []
    for line_num, line in enumerate(lines):
        if line == u'\n':
            starting = line_num + 1
            break
    for line_num, line in enumerate(lines[starting:]):
        if not re.search(u'@00', line):
            line = re.split(u'(@11\([\u05d0-\u05ea]{0,3}\))', line)
            if isinstance(line, basestring) and line != u'':
                cleaned.append(line)
            else:
                [cleaned.append(st.strip()) for st in line if st]
    try:
        ja = file_to_ja_g(2, cleaned, regs, cleaner, gimatria=True, grab_all=[False], group_name='gim').array()
    except AttributeError:
        print 'there are more regs then levels...'
    ja_to_xml(ja, ['siman', 'letter'], 'hagahot_letters_25.xml') #, 'segments'

    # for hghds in
    return JaggedArray(ja_hagahot)


def link_raph():
    pass


def link_hagahot():
    pass


def clean(JA, replace_dict):
    '''

    :param JA: JA obj of the text to be cleand
    :param replace_dict: a dictionary of what to replace
    :return: cleaned JA
    '''
    # replace_dict = {u'@23': ur'<b>\1</b>', u'@33(.*?)@34': ur'<b>\1</b>',
    #                 u'@66(.*?)@67': ur'\1'}  # , u'@55[\u05d0-\u05ea]{1,3}' : u'<i-tags = >'}
    lstlst = JA.array()
    new = []
    nd1 = []
    for d1 in lstlst:
        for d2 in d1:
            nd2 = multiple_replace(d2, replace_dict, using_regex=True)
            nd1.append(nd2)
        new.append(nd1)
        nd1 = []
    ja_to_xml(new, ['letter', 'segments'], 'clean_smk.xml')
    return JaggedArray(new)


def post_smk(ja_smk):

    # before posting earase all '@'s
    ja_smk = clean(ja_smk)

    text_version = {
        'versionTitle': 'Sefer Mitzvot Katan, Kopys, 1820',
        'versionSource': 'http://primo.nli.org.il/primo_library/libweb/action/dlDisplay.do?vid=NLI&docId=NNL_ALEPH001771677',
        'language': 'he',
        'text': ja_smk
    }

    schema = JaggedArrayNode()
    schema.add_title('Sefer Mitzvot Katan', 'en', True)
    schema.add_title(u'ספר מצות קטן', 'he', True)
    schema.key = 'Sefer Mitzvot Katan'
    schema.depth = 2
    schema.addressTypes = ['Integer', 'Integer']
    schema.sectionNames = ['Siman', 'Segment']
    schema.validate()

    index_dict = {
        'title': 'Sefer Mitzvot Katan',
        'categories': ['Halakhah'],
        'schema': schema.serialize()  # This line converts the schema into json
    }
    post_index(index_dict)

    post_text('Sefer Mitzvot Katan', text_version)


def post_raph():
    pass


def post_hagahot():
    pass

if __name__ == "__main__":
    # smk_ja = parse_smk('Semak.txt')
    # parse_raph(u'Raph_on_Semak.txt', smk_ja)
    # replace_clean_smk = {u'@[^58\D]\d': ur'', u'@55[א-ת]{0,3}': ur'', u'@88\([א-ת]{1,3}\)': ur''}
    # smk_ja = clean(smk_ja, replace_clean_smk)
    pass
    parse_hagahot(u'Semak_hagahot_chadashot.txt', [], [])
    # post_smk(smk_ja)