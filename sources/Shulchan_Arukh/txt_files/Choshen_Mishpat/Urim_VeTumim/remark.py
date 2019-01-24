# encoding=utf-8

import re
from data_utilities.util import StructuredDocument, numToHeb


def remark_chapter(chapter_text, bad_seifim, pattern):
    current_seif = [1]

    def repl(x):
        while current_seif[0] in bad_seifim:
            current_seif[0] += 1
        new_text = u' {}({}) '.format(x.group(), numToHeb(current_seif[0]))
        current_seif[0] += 1
        return new_text
    chapter_text = re.sub(pattern, repl, chapter_text)
    chapter_text = re.sub(u' {2,}', u' ', chapter_text)
    return re.sub(u'^ +| +$', u'', chapter_text, flags=re.MULTILINE)


urim1 = {
    36: {5, 6, 7, 8, 9, 10},
    37: {14},
    45: {27},
}

urim2 = {
    89: {1, 2, 3},
    149: set(range(1, 18))
}

tumim1 = {
    36: {1, 2, 3, 4},
}

tumim2 = {
    89:  {2},
    123: set(range(1, 11)),
    149: set(range(1, 8)),
    150: {4}
}

my_doc = StructuredDocument('Choshen_Mishpat_1.txt', u'@00([\u05d0-\u05ea]{1,3})')
for chap in my_doc.get_chapter_values():
    my_doc.edit_section(chap, remark_chapter, urim1.get(chap, set()), u'@55')
    my_doc.edit_section(chap, remark_chapter, tumim1.get(chap, set()), u'@66')
my_doc.write_to_file('Choshen_Mishpat_1_test.txt')

my_doc = StructuredDocument('Choshen_Mishpat_2.txt', u'@00([\u05d0-\u05ea]{1,3})')
for chap in my_doc.get_chapter_values():
    my_doc.edit_section(chap, remark_chapter, urim2.get(chap, set()), u'@55')
    my_doc.edit_section(chap, remark_chapter, tumim2.get(chap, set()), u'@66')
my_doc.write_to_file('Choshen_Mishpat_2_test.txt')
