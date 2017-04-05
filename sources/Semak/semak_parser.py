# encoding=utf-8

import codecs
import re
from data_utilities.util import ja_to_xml, multiple_replace, traverse_ja, file_to_ja_g, file_to_ja
from sources.functions import post_text, post_index, post_link
from sefaria.model import *
from sefaria.datatype.jagged_array import JaggedArray

def parse_semak_day(filename): # alt struct according to days. (not sure how alt struct works
    pass
# @66[^\(]

def parse_semak(filename):

    def cleaner(my_text):
        replace_dict = {u'@11(.*?)@12': ur'<b>\1</b>', u'@33(.*?)@34': ur'<b>\1</b>', u'@33(.*?)@34': ur'<b>\1</b>', u'@66(.*?)@67': ur'\1'}
        new = []
        for line in my_text:
            line = multiple_replace(line,replace_dict,using_regex=True)
            new.append(line)
        return new


    regs = [ur'@22(?P<gim>[\u05d0-\u05ea]{1,3})'] #, u'@(11|23|33)(?P<gim>)']
    with codecs.open(filename, 'r', 'utf-8') as fp:
        lines = fp.readlines()
    starting = None
    # check if we got to the end of the legend and change to started
    # clean all lines of days start with @00
    cleaned = []
    letter_section = []
    for line_num, line in enumerate(lines):
        if line == u'\n':
            starting = line_num + 1
            break
    for line_num, line in enumerate(lines[starting:]):
        if not re.search(u'@00', line) and not line.isspace():
            if re.search(u'@22', line):
                line = re.split(u'(@22[\u05d0-\u05ea]{1,3})', line)
                if isinstance(line, basestring):
                    cleaned.append(line)
                else:
                    [cleaned.append(st) for st in line if st]
            else:
                cleaned.append(line)
    try:
        smk_ja = file_to_ja_g(2, cleaned, regs, cleaner, gimatria=True,  grab_all=[False, True, True], group_name = 'gim').array() #group_name = 'gim',
    except AttributeError:
        print 'there are more regs then levels...'

    ja_to_xml(smk_ja, ['letter', 'segments'], 'smk.xml')

    return smk_ja


def parse_Raph(filename):

    def cleaner(my_text):
        return my_text
        # replace_dict = {u'@11(.*?)@12': ur'<b>\1</b>'}
        # new = []
        # for line in my_text:
        #     line = multiple_replace(line,replace_dict,using_regex=True)
        #     new.append(line)
        # return new

    regs = [ur'@11(?P<gim>[\u05d0-\u05ea]{1,3})'] #find the letter
    with codecs.open(filename, 'r', 'utf-8') as fp:
        lines = fp.readlines()
    starting = None
    # check if we got to the end of the legend and change to started
    # clean all lines of days start with @00
    cleaned = []
    letter_section = []
    for line_num, line in enumerate(lines):
        if line == u'\n':
            starting = line_num + 1
            break
    for line_num, line in enumerate(lines[starting:]):
        if not re.search(u'@00', line) and not line.isspace():
            if re.search(u'@11', line):
                line = re.split(u'(@11[\u05d0-\u05ea]{1,3})', line)
                if isinstance(line, basestring):
                    cleaned.append(line)
                else:
                    [cleaned.append(st) for st in line if st]
            else:
                cleaned.append(line)
    try:
        ja = file_to_ja_g(2, cleaned, regs, cleaner, gimatria=True,  grab_all=[False, True, True], group_name = 'gim').array() #group_name = 'gim',
    except AttributeError:
        print 'there are more regs then levels...'

    ja_to_xml(ja, ['letter', 'segments'], 'Raph.xml')

    return ja

def count_regex_in_all_db(pattern, lang, text = all):
    found = 0
    vtitle = None
    if text==all:
        indecies = library.all_index_records()
    else:
        indecies = [library.get_index(text)]
    for index in indecies:
        # if index == Index().load({'title': 'Divrei Negidim'}):
        #     continue
        try:
            unit_list_temp = index.nodes.traverse_to_list(lambda n, _: TextChunk(n.ref(), lang, vtitle=vtitle).ja().flatten_to_array() if not n.children else [])
            st = ' '.join(unit_list_temp)
            found += len(re.findall(pattern,st))
        except: # sefaria.system.exceptions.NoVersionFoundError:
            continue
    return found

if __name__ == "__main__":
    # ja_smk = parse_semak('Semak.txt')
    # ja_raph = parse_Raph('Raph_on_Semak.txt')
    print count_regex_in_all_db(u'(\(|\([^)]* )שם(\)| [^(]*\))', 'he') #, text = 'Ramban on Genesis')
