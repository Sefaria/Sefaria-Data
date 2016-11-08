# encoding=utf-8

import re
import codecs
from data_utilities.util import file_to_ja, multiple_replace


def parse_yitzira():

    def cleaner(my_text):
        return filter(None,
                      [re.sub(u'@[0-9]{2}', u'', line) if re.search(u'@11', line) else None for line in my_text])

    with codecs.open('yitzira_mishna.txt', 'r', 'utf-8') as infile:
        return file_to_ja([[]], infile, [u'@00\u05e4\u05e8\u05e7 [\u05d0-\u05ea]{1,2}'], cleaner)


def parse_general(filename):

    def cleaner(my_text):
        result = []
        for line in my_text:
            new_line = multiple_replace(line, {u'@31': u'<b>', u'@32': u'</b>'})
            new_line = re.sub(u'@[0-9]{2}', u'', new_line)
            result.append(new_line)
        return result

    regs = [u'@00\u05e4\u05e8\u05e7 [\u05d0-\u05ea]{1,2}', u'@22[\u05d0-\u05ea]{1,2}']
    with codecs.open(filename, 'r', 'utf-8') as infile:
        return file_to_ja([[[]]], infile, regs, cleaner)
